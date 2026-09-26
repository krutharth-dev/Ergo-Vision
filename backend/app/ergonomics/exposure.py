from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from statistics import mean
import time

from .geometry import clamp


@dataclass
class ExposureSnapshot:
    """Time-aware ergonomic exposure state.

    cumulative_dose is expressed in confidence-weighted risk-seconds. This is a
    prototype ergonomic exposure indicator, not a clinically validated dose.
    """

    instantaneous_risk: float = 0.0
    confidence_weighted_risk: float = 0.0
    cumulative_dose: float = 0.0
    dose_level: str = "LOW"
    continuous_poor_seconds: float = 0.0
    postural_drift: float = 0.0
    baseline_risk: float = 0.0
    recent_risk: float = 0.0
    baseline_ready: bool = False
    baseline_observation_seconds: float = 0.0
    baseline_required_seconds: float = 10.0
    available: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class ExposureEngine:
    """Accumulates ergonomic exposure using risk, confidence and elapsed time."""

    def __init__(
        self,
        recovery_rate: float = 0.15,
        poor_risk_threshold: float = 0.40,
        max_step_seconds: float = 1.0,
        baseline_window_seconds: float = 10.0,
        recent_window_seconds: float = 12.0,
    ):
        self.recovery_rate = max(0.0, recovery_rate)
        self.poor_risk_threshold = clamp(poor_risk_threshold, 0.0, 1.0)
        self.max_step_seconds = max(0.01, max_step_seconds)
        self.baseline_window_seconds = max(2.0, baseline_window_seconds)
        self.recent_window_seconds = max(3.0, recent_window_seconds)
        self._dose = 0.0
        self._continuous_poor = 0.0
        self._last_timestamp: float | None = None
        self._baseline_samples: list[float] = []
        self._baseline_risk: float | None = None
        self._baseline_observation_seconds = 0.0
        self._history: deque[tuple[float, float]] = deque()
        self._snapshot = ExposureSnapshot(
            baseline_required_seconds=self.baseline_window_seconds,
        )

    def update(
        self,
        risk: float,
        confidence: float,
        reliable: bool,
        timestamp: float | None = None,
    ) -> ExposureSnapshot:
        now = time.monotonic() if timestamp is None else float(timestamp)
        risk = clamp(float(risk), 0.0, 1.0)
        confidence = clamp(float(confidence), 0.0, 1.0)

        if self._last_timestamp is None:
            self._last_timestamp = now
            if reliable:
                self._record_risk(now, risk, reliable_seconds=0.0)
            return self._make_snapshot(risk, confidence, reliable)

        dt = clamp(now - self._last_timestamp, 0.0, self.max_step_seconds)
        self._last_timestamp = now

        if not reliable:
            return self._make_snapshot(0.0, 0.0, False)

        weighted_risk = risk * confidence
        accumulation = weighted_risk * dt
        recovery = self.recovery_rate * (1.0 - risk) * confidence * dt
        self._dose = max(0.0, self._dose + accumulation - recovery)

        if risk >= self.poor_risk_threshold:
            self._continuous_poor += dt
        else:
            self._continuous_poor = 0.0

        self._record_risk(now, risk, reliable_seconds=dt)
        return self._make_snapshot(risk, confidence, True)

    def current(self) -> ExposureSnapshot:
        return self._snapshot

    def reset(self) -> None:
        self._dose = 0.0
        self._continuous_poor = 0.0
        self._last_timestamp = None
        self._baseline_samples = []
        self._baseline_risk = None
        self._baseline_observation_seconds = 0.0
        self._history.clear()
        self._snapshot = ExposureSnapshot(
            baseline_required_seconds=self.baseline_window_seconds,
        )

    def _record_risk(self, now: float, risk: float, reliable_seconds: float) -> None:
        if self._baseline_risk is None:
            self._baseline_observation_seconds += max(0.0, reliable_seconds)
            self._baseline_samples.append(risk)
            if (
                self._baseline_observation_seconds >= self.baseline_window_seconds
                and self._baseline_samples
            ):
                self._baseline_risk = mean(self._baseline_samples)

        self._history.append((now, risk))
        keep_after = now - max(60.0, self.recent_window_seconds * 2)
        while self._history and self._history[0][0] < keep_after:
            self._history.popleft()

    def _make_snapshot(
        self,
        risk: float,
        confidence: float,
        available: bool,
    ) -> ExposureSnapshot:
        weighted_risk = risk * confidence if available else 0.0
        recent_values: list[float] = []
        if self._history and self._last_timestamp is not None:
            cutoff = self._last_timestamp - self.recent_window_seconds
            recent_values = [value for ts, value in self._history if ts >= cutoff]

        recent_risk = mean(recent_values) if recent_values else risk
        baseline = self._baseline_risk
        if baseline is None and self._baseline_samples:
            baseline = mean(self._baseline_samples)
        baseline = baseline or 0.0

        # Drift is only interpretable once the baseline window is complete.
        drift = (
            clamp(recent_risk - baseline, -1.0, 1.0)
            if self._baseline_risk is not None
            else 0.0
        )

        if self._dose < 15:
            level = "LOW"
        elif self._dose < 45:
            level = "MODERATE"
        else:
            level = "HIGH"

        self._snapshot = ExposureSnapshot(
            instantaneous_risk=round(risk, 4) if available else 0.0,
            confidence_weighted_risk=round(weighted_risk, 4),
            cumulative_dose=round(self._dose, 3),
            dose_level=level,
            continuous_poor_seconds=round(self._continuous_poor, 3),
            postural_drift=round(drift, 4),
            baseline_risk=round(baseline, 4),
            recent_risk=round(recent_risk, 4),
            baseline_ready=self._baseline_risk is not None,
            baseline_observation_seconds=round(self._baseline_observation_seconds, 2),
            baseline_required_seconds=round(self.baseline_window_seconds, 2),
            available=available,
        )
        return self._snapshot
