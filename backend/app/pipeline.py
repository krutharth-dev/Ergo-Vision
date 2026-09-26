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
from .ergonomics.exposure import ExposureEngine
from .ergonomics.feedback import FeedbackEngine
from .ergonomics.intervention import InterventionEngine
from .ergonomics.measurements import ErgonomicMeasurements, compute_measurements
from .ergonomics.ocular import OcularEngine
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
        self.ocular_engine = OcularEngine()
        self.exposure_engine = ExposureEngine()
        self.intervention_engine = InterventionEngine()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_update_time = 0.0

        self._current_measurements = ErgonomicMeasurements(person_detected=False)
        self._current_tracking = assess_tracking(None)
        self._current_ocular = self.ocular_engine.current()
        self._current_exposure = self.exposure_engine.current()
        self._current_intervention = self.intervention_engine.current()
        self._current_status = "NO_PERSON"
        self._current_score = 0
        self._current_ergovision_index = 0
        self._current_combined_risk = 0.0
        self._current_proximity_drift = 0.0
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
        self.intervention_engine.pause()
        logger.info("Pipeline stopped")

    def activate_camera(self) -> bool:
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
            self._current_ergovision_index = 0
            self._current_combined_risk = 0.0
            self._current_proximity_drift = 0.0
            self._current_measurements = ErgonomicMeasurements(person_detected=False)
            self._current_tracking = assess_tracking(None)
            self._current_ocular = self.ocular_engine.current()
            self._current_exposure = self.exposure_engine.current()
            self._current_intervention = self.intervention_engine.current()
            self._last_event = None

        logger.info("Camera released because no dashboard clients remain")

    def _run_loop(self):
        while self._running:
            ok, frame = self.camera.read()
            if not ok or frame is None:
                time.sleep(0.005)
                continue

            now = time.monotonic()
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

            proximity_drift = self._proximity_drift(smoothed)
            ocular = self.ocular_engine.update(
                landmarks=landmarks,
                eye_confidence=tracking.eye_confidence,
                proximity_drift=proximity_drift,
                timestamp=now,
            )

            posture_risk = (1.0 - score / 100.0) if tracking.reliable else 0.0
            if ocular.available:
                combined_risk = 0.75 * posture_risk + 0.25 * ocular.visual_load
                combined_confidence = 0.75 * tracking.confidence + 0.25 * ocular.confidence
            else:
                combined_risk = posture_risk
                combined_confidence = tracking.confidence

            combined_risk = max(0.0, min(1.0, combined_risk))
            combined_confidence = max(0.0, min(1.0, combined_confidence))
            ergovision_index = int(round((1.0 - combined_risk) * 100.0)) if tracking.reliable else 0

            if self.tracker.active:
                exposure = self.exposure_engine.update(
                    risk=combined_risk,
                    confidence=combined_confidence,
                    reliable=tracking.reliable,
                    timestamp=now,
                )
                intervention = self.intervention_engine.update(
                    risk=combined_risk,
                    posture_status=status,
                    reliable=tracking.reliable,
                    timestamp=now,
                )
            else:
                exposure = self.exposure_engine.update(
                    risk=combined_risk,
                    confidence=combined_confidence,
                    reliable=False,
                    timestamp=now,
                )
                self.intervention_engine.pause()
                intervention = self.intervention_engine.current()

            encoded, jpeg = cv2.imencode(".jpg", annotated)

            with self._lock:
                self._current_measurements = smoothed
                self._current_tracking = tracking
                self._current_ocular = ocular
                self._current_exposure = exposure
                self._current_intervention = intervention
                self._current_status = status
                self._current_score = score
                self._current_ergovision_index = ergovision_index
                self._current_combined_risk = combined_risk
                self._current_proximity_drift = proximity_drift
                if encoded:
                    self._current_frame_jpeg = jpeg.tobytes()

            tracker_status = "NO_PERSON" if status == "LOW_CONFIDENCE" else status
            self.tracker.update(tracker_status, score)
            self._maybe_emit()

    def _proximity_drift(self, measurements: ErgonomicMeasurements) -> float:
        if not self.calibration.calibrated:
            return 0.0
        baseline = self.calibration.forward_head_indicator
        return max(-1.0, min(1.0, measurements.forward_head_indicator - baseline))

    def _maybe_emit(self):
        now = time.time()
        if now - self._last_update_time < WEBSOCKET_UPDATE_INTERVAL:
            return
        self._last_update_time = now
        event = self.get_current()
        with self._lock:
            self._last_event = event

    def _build_event(
        self,
        status,
        measurements,
        score,
        ergovision_index,
        combined_risk,
        proximity_drift,
        tracking,
        ocular,
        exposure,
        intervention,
    ) -> dict:
        feedback = (
            tracking.guidance or ["Tracking quality is too low for a reliable posture assessment."]
            if status == "LOW_CONFIDENCE"
            else self.feedback_engine.generate(measurements, status)
        )
        return {
            "score": score,
            "ergovision_index": ergovision_index,
            "combined_risk": round(combined_risk, 4),
            "proximity_drift": round(proximity_drift, 4),
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
                "head_shoulder_gap_ratio": round(measurements.head_shoulder_gap_ratio, 3),
                "torso_depth_ratio": round(measurements.torso_depth_ratio, 3),
                "slouch_indicator": round(measurements.slouch_indicator, 3),
            },
            "tracking": tracking.as_dict(),
            "ocular": ocular.as_dict(),
            "exposure": exposure.as_dict(),
            "intervention": intervention.as_dict(),
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "posture_calibrated": self.calibration.calibrated,\n            "person_detected": measurements.person_detected,
        }

    def get_current(self) -> dict:
        with self._lock:
            measurements = self._current_measurements
            tracking = self._current_tracking
            ocular = self._current_ocular
            exposure = self._current_exposure
            intervention = self._current_intervention
            status = self._current_status
            score = self._current_score
            ergovision_index = self._current_ergovision_index
            combined_risk = self._current_combined_risk
            proximity_drift = self._current_proximity_drift
        return self._build_event(
            status,
            measurements,
            score,
            ergovision_index,
            combined_risk,
            proximity_drift,
            tracking,
            ocular,
            exposure,
            intervention,
        )

    def get_last_event(self) -> Optional[dict]:
        with self._lock:
            return self._last_event

    def get_frame_jpeg(self) -> bytes | None:
        with self._lock:
            return self._current_frame_jpeg

    def get_session_stats(self) -> dict:
        stats = self.tracker.get_stats().__dict__.copy()
        exposure = self.exposure_engine.current()
        ocular = self.ocular_engine.current()
        intervention = self.intervention_engine.current()
        stats.update(
            {
                "exposure_dose": exposure.cumulative_dose,
                "exposure_level": exposure.dose_level,
                "postural_drift": exposure.postural_drift,
                "blink_rate_per_min": ocular.blink_rate_per_min,
                "intervention_count": intervention.total_interventions,
                "successful_corrections": intervention.successful_corrections,
                "correction_rate_percent": intervention.correction_rate_percent,
                "last_correction_seconds": intervention.correction_seconds,
                "last_improvement_percent": intervention.improvement_percent,
            }
        )
        return stats

    def start_session(self) -> dict:
        self.tracker.start()
        return self.get_session_stats()

    def stop_session(self) -> dict:
        self.tracker.stop()
        self.intervention_engine.pause()
        return self.get_session_stats()

    def reset_session(self) -> dict:
        self.tracker.reset()
        self.exposure_engine.reset()
        self.intervention_engine.reset()
        self.ocular_engine.reset()
        self.tracker.start()
        return self.get_session_stats()

    def capture_calibration(self) -> dict:
        samples = list(self._recent_measurements)[-60:]
        self.calibration.capture(samples)
        self.classifier.reset()
        self.exposure_engine.reset()
        self.intervention_engine.reset()
        return self.calibration.as_dict()

    def clear_calibration(self) -> dict:
        self.calibration.clear()
        self.classifier.reset()
        self.exposure_engine.reset()
        self.intervention_engine.reset()
        return self.calibration.as_dict()

    def get_calibration(self) -> dict:
        return self.calibration.as_dict()

    def camera_devices(self) -> list[dict]:
        current = self.camera.camera_index
        return [{"index": i, "label": f"Camera {i + 1}", "current": i == current} for i in self.camera.scan()]

    def select_camera(self, index: int) -> dict:
        if not self.camera.select(index):
            raise ValueError(f"Camera {index + 1} could not be opened.")
        self.detector.reset_tracking()
        self.smoother.reset()
        self.classifier.reset()
        self._recent_measurements.clear()
        self.calibration.clear()
        self.ocular_engine.reset()
        self.exposure_engine.reset()
        self.intervention_engine.reset()
        return self.camera.get_status()
