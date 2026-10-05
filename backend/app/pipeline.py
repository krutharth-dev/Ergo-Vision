import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import cv2

from .config import WEBSOCKET_UPDATE_INTERVAL
from .ergonomics.calibration import CalibrationProfile
from .ergonomics.classifier import PostureClassifier
from .ergonomics.feedback import FeedbackEngine
from .ergonomics.measurements import ErgonomicMeasurements, compute_measurements
from .ergonomics.scoring import compute_score
from .ergonomics.smoothing import SmoothingBuffer
from .session.tracker import SessionTracker
from .vision.camera import Camera
from .vision.detector import Detector
from .vision.quality import assess_tracking

logger = logging.getLogger(__name__)


class PosturePipeline:
    def __init__(self, camera: Camera, detector: Detector):
        self.camera = camera
        self.detector = detector
        self.classifier = PostureClassifier()
        self.feedback_engine = FeedbackEngine()
        self.smoother = SmoothingBuffer()
        self.tracker = SessionTracker()
        self.calibration = CalibrationProfile.load()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_update_time = 0.0
        self._current_measurements = ErgonomicMeasurements(person_detected=False)
        self._current_tracking = assess_tracking(None)
        self._current_status = "NO_PERSON"
        self._current_score = 0
        self._current_frame_jpeg: bytes | None = None
        self._last_event: dict | None = None
        self._recent_measurements: deque[ErgonomicMeasurements] = deque(maxlen=90)

    def start(self):
        if self._running:
            return
        self._running = True
        self.tracker.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Pipeline started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.tracker.stop()
        logger.info("Pipeline stopped")

    def activate_camera(self) -> bool:
        # Open the webcam and resume posture processing for an active dashboard.
        if self._running and self.camera.is_opened:
            return True

        if not self.camera.is_opened and not self.camera.open():
            logger.warning("Camera could not be opened for the dashboard")
            return False

        self.detector.reset_tracking()
        self.smoother.reset()
        self.classifier.reset()
        self.start()
        logger.info("Camera activated for dashboard client")
        return True

    def deactivate_camera(self) -> None:
        # Stop posture processing and release the webcam when nobody is viewing.
        if self._running:
            self.stop()

        self.camera.release()
        self.detector.reset_tracking()
        self.smoother.reset()
        self.classifier.reset()

        with self._lock:
            self._current_frame_jpeg = None
            self._current_status = "NO_PERSON"
            self._current_score = 0
            self._current_measurements = ErgonomicMeasurements(person_detected=False)
            self._current_tracking = assess_tracking(None)
            self._last_event = None

        logger.info("Camera released because no dashboard clients remain")

    def _run_loop(self):
        while self._running:
            ok, frame = self.camera.read()
            if not ok or frame is None:
                time.sleep(0.005)
                continue

            landmarks, annotated = self.detector.process_frame(frame)
            tracking = assess_tracking(landmarks)
            measurements = compute_measurements(landmarks)
            smoothed = self.smoother.smooth(measurements)
            if tracking.quality == "EXCELLENT" and tracking.hips_visible and smoothed.person_detected:
                self._recent_measurements.append(smoothed)
            smoothed.slouch_indicator = self.calibration.slouch_indicator(smoothed)

            if not tracking.reliable:
                status = "LOW_CONFIDENCE"
                score = 0
            else:
                status = self.classifier.classify(smoothed)
                score, _breakdown = compute_score(smoothed)
            encoded, jpeg = cv2.imencode(".jpg", annotated)

            with self._lock:
                self._current_measurements = smoothed
                self._current_tracking = tracking
                self._current_status = status
                self._current_score = score
                if encoded:
                    self._current_frame_jpeg = jpeg.tobytes()

            tracker_status = "NO_PERSON" if status == "LOW_CONFIDENCE" else status
            self.tracker.update(tracker_status, score)
            self._maybe_emit(status, smoothed, score, tracking)

    def _maybe_emit(self, status, measurements, score, tracking):
        now = time.time()
        if now - self._last_update_time < WEBSOCKET_UPDATE_INTERVAL:
            return
        self._last_update_time = now
        event = self._build_event(status, measurements, score, tracking)
        with self._lock:
            self._last_event = event

    def _build_event(self, status, measurements, score, tracking) -> dict:
        feedback = (tracking.guidance or ["Tracking quality is too low for a reliable posture assessment."]) if status == "LOW_CONFIDENCE" else self.feedback_engine.generate(measurements, status)
        return {
            "score": score,
            "status": status,
            "measurements": {
                "head_tilt_degrees": round(measurements.head_tilt_degrees, 1),
                "shoulder_alignment_score": round(measurements.shoulder_alignment_score, 2),
                "shoulder_alignment_degrees": round(measurements.shoulder_alignment_degrees, 1),
                "neck_offset": round(measurements.neck_offset, 3),
                "forward_head_indicator": round(measurements.forward_head_indicator, 2),
                "gaze_vertical_degrees": round(measurements.gaze_vertical_degrees, 1),
                "torso_lean_degrees": round(measurements.torso_lean_degrees, 1),
                "torso_length_ratio": round(measurements.torso_length_ratio, 3),
                "torso_vertical_ratio": round(measurements.torso_vertical_ratio, 3),
                "head_shoulder_gap_ratio": round(measurements.head_shoulder_gap_ratio, 3),
                "torso_depth_ratio": round(measurements.torso_depth_ratio, 3),
                "slouch_indicator": round(measurements.slouch_indicator, 3),
            },
            "tracking": tracking.as_dict(),
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "person_detected": measurements.person_detected,
        }

    def get_current(self) -> dict:
        with self._lock:
            measurements = self._current_measurements
            tracking = self._current_tracking
            status = self._current_status
            score = self._current_score
        return self._build_event(status, measurements, score, tracking)

    def get_last_event(self) -> Optional[dict]:
        with self._lock:
            return self._last_event

    def get_frame_jpeg(self) -> bytes | None:
        with self._lock:
            return self._current_frame_jpeg

    def get_session_stats(self) -> dict:
        return self.tracker.get_stats().__dict__

    def capture_calibration(self) -> dict:
        samples = list(self._recent_measurements)[-60:]
        self.calibration.capture(samples)
        self.classifier.reset()
        return self.calibration.as_dict()

    def clear_calibration(self) -> dict:
        self.calibration.clear()
        self.classifier.reset()
        return self.calibration.as_dict()

    def get_calibration(self) -> dict:
        return self.calibration.as_dict()

    def camera_devices(self) -> list[dict]:
        current = self.camera.camera_index
        return [{"index": i, "label": f"Camera {i+1}", "current": i == current} for i in self.camera.scan()]

    def select_camera(self, index: int) -> dict:
        if not self.camera.select(index):
            raise ValueError(f"Camera {index+1} could not be opened.")
        self.detector.reset_tracking(); self.smoother.reset(); self.classifier.reset(); self._recent_measurements.clear(); self.calibration.clear()
        return self.camera.get_status()
