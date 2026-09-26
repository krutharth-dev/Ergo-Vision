from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from statistics import mean
import time

from ..vision.landmarks import LandmarkSet
from .geometry import calculate_distance, clamp


@dataclass
class OcularSnapshot:
    available: bool = False
    calibrated: bool = False
    confidence: float = 0.0
    ear: float = 0.0
    baseline_ear: float = 0.0
    blink_threshold: float = 0.0
    blink_count: int = 0
    blink_rate_per_min: float = 0.0
    inter_blink_interval_seconds: float = 0.0
    observation_seconds: float = 0.0
    baseline_observation_seconds: float = 0.0
    baseline_required_seconds: float = 2.0
    blink_ready: bool = False
    visual_load: float = 0.0
    proximity_drift: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def _eye_ear(landmarks: LandmarkSet, names: tuple[str, str, str, str, str, str]) -> float | None:
    points = [landmarks.get_pos(name) for name in names]
    if any(point is None for point in points):
        return None
    p1, p2, p3, p4, p5, p6 = points
    horizontal = calculate_distance(p1, p4)
    if horizontal < 1e-6:
        return None
    vertical_1 = calculate_distance(p2, p6)
    vertical_2 = calculate_distance(p3, p5)
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def calculate_ear(landmarks: LandmarkSet | None) -> float | None:
    if landmarks is None:
        return None

    left = _eye_ear(
        landmarks,
        (
            "left_eye_outer",
            "left_eye_upper_outer",
            "left_eye_upper_inner",
            "left_eye_inner",
            "left_eye_lower_inner",
            "left_eye_lower_outer",
        ),
    )
    right = _eye_ear(
        landmarks,
        (
            "right_eye_inner",
            "right_eye_upper_inner",
            "right_eye_upper_outer",
            "right_eye_outer",
            "right_eye_lower_outer",
            "right_eye_lower_inner",
        ),
    )
    values = [value for value in (left, right) if value is not None]
    return mean(values) if values else None


class OcularEngine:
    """Personalized blink and visual-load estimator using Face Landmarker eyes."""

    def __init__(
        self,
        baseline_seconds: float = 2.0,
        threshold_ratio: float = 0.72,
        minimum_eye_confidence: float = 0.45,
    ):
        self.baseline_seconds = max(1.0, baseline_seconds)
        self.threshold_ratio = clamp(threshold_ratio, 0.55, 0.90)
        self.minimum_eye_confidence = clamp(minimum_eye_confidence, 0.0, 1.0)
        self.reset()

    def reset(self) -> None:
        self._baseline_samples: list[float] = []
        self._baseline_ear: float | None = None
        self._baseline_observation_seconds = 0.0
        self._last_valid_baseline_timestamp: float | None = None
        self._closed_since: float | None = None
        self._blink_times: deque[float] = deque()
        self._last_blink_time: float | None = None
        self._last_ibi = 0.0
        self._observation_started: float | None = None
        self._snapshot = OcularSnapshot(
            baseline_required_seconds=self.baseline_seconds,
        )

    def current(self) -> OcularSnapshot:
        return self._snapshot

    def update(
        self,
        landmarks: LandmarkSet | None,
        eye_confidence: float,
        proximity_drift: float = 0.0,
        timestamp: float | None = None,
    ) -> OcularSnapshot:
        now = time.monotonic() if timestamp is None else float(timestamp)
        confidence = clamp(float(eye_confidence), 0.0, 1.0)
        ear = calculate_ear(landmarks)

        if ear is None or confidence < self.minimum_eye_confidence:
            self._closed_since = None
            self._last_valid_baseline_timestamp = None
            return self._emit(False, confidence, 0.0, proximity_drift, now)

        if self._observation_started is None:
            self._observation_started = now

        if self._baseline_ear is None:
            if self._last_valid_baseline_timestamp is not None:
                valid_step = clamp(
                    now - self._last_valid_baseline_timestamp,
                    0.0,
                    0.25,
                )
                self._baseline_observation_seconds += valid_step
            self._last_valid_baseline_timestamp = now

            if ear > 0.05:
                self._baseline_samples.append(ear)

            if (
                self._baseline_observation_seconds >= self.baseline_seconds
                and len(self._baseline_samples) >= 8
            ):
                ordered = sorted(self._baseline_samples)
                upper_half = ordered[len(ordered) // 2 :]
                self._baseline_ear = mean(upper_half)

        if self._baseline_ear is not None:
            threshold = self._baseline_ear * self.threshold_ratio
            if ear < threshold:
                if self._closed_since is None:
                    self._closed_since = now
            elif self._closed_since is not None:
                closed_for = now - self._closed_since
                self._closed_since = None
                if 0.05 <= closed_for <= 0.80:
                    if self._last_blink_time is not None:
                        self._last_ibi = now - self._last_blink_time
                    self._last_blink_time = now
                    self._blink_times.append(now)

        while self._blink_times and self._blink_times[0] < now - 60.0:
            self._blink_times.popleft()

        return self._emit(True, confidence, ear, proximity_drift, now)

    def _emit(
        self,
        available: bool,
        confidence: float,
        ear: float,
        proximity_drift: float,
        now: float,
    ) -> OcularSnapshot:
        observation_seconds = (
            max(0.0, now - self._observation_started)
            if self._observation_started is not None
            else 0.0
        )

        if observation_seconds > 0:
            effective_window = min(60.0, observation_seconds)
            recent_blinks = len(self._blink_times)
            blink_rate = recent_blinks / effective_window * 60.0
        else:
            blink_rate = 0.0

        proximity_load = clamp((max(0.0, proximity_drift) - 0.08) / 0.25, 0.0, 1.0)
        blink_ready = self._baseline_ear is not None and observation_seconds >= 15.0
        if blink_ready:
            blink_load = clamp((12.0 - blink_rate) / 8.0, 0.0, 1.0)
            visual_load = 0.65 * blink_load + 0.35 * proximity_load
        else:
            visual_load = 0.35 * proximity_load

        threshold = (self._baseline_ear or 0.0) * self.threshold_ratio
        self._snapshot = OcularSnapshot(
            available=available,
            calibrated=self._baseline_ear is not None,
            confidence=round(confidence, 3),
            ear=round(ear, 4) if available else 0.0,
            baseline_ear=round(self._baseline_ear or 0.0, 4),
            blink_threshold=round(threshold, 4),
            blink_count=len(self._blink_times),
            blink_rate_per_min=round(blink_rate, 1),
            inter_blink_interval_seconds=round(self._last_ibi, 2),
            observation_seconds=round(observation_seconds, 1),
            baseline_observation_seconds=round(self._baseline_observation_seconds, 2),
            baseline_required_seconds=round(self.baseline_seconds, 2),
            blink_ready=blink_ready,
            visual_load=round(clamp(visual_load, 0.0, 1.0), 4),
            proximity_drift=round(proximity_drift, 4),
        )
        return self._snapshot
