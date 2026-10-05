from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

from .geometry import clamp
from .measurements import ErgonomicMeasurements

DATA_DIR = Path(os.environ.get("ERGOVISION_DATA_DIR", str(Path.home() / ".ergovision")))
CALIBRATION_PATH = DATA_DIR / "calibration.json"
CALIBRATION_VERSION = 5


@dataclass
class CalibrationProfile:
    version: int = CALIBRATION_VERSION
    calibrated: bool = False
    captured_at: str | None = None
    torso_length_ratio: float = 0.0
    torso_vertical_ratio: float = 0.0
    head_shoulder_gap_ratio: float = 0.0
    torso_depth_ratio: float = 0.0
    forward_head_indicator: float = 0.0
    shoulder_alignment_degrees: float = 0.0
    samples: int = 0

    @classmethod
    def load(cls) -> "CalibrationProfile":
        try:
            data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
            if data.get("version") != CALIBRATION_VERSION:
                # Older profiles were created with absolute body-proportion assumptions
                # that could incorrectly label an upright person as slouching.
                return cls()
            return cls(**data)
        except (OSError, ValueError, TypeError):
            return cls()

    def capture(self, samples: list[ErgonomicMeasurements]) -> None:
        valid = [
            s
            for s in samples
            if s.person_detected
            and s.torso_length_ratio > 0
            and s.torso_vertical_ratio > 0
        ]
        if len(valid) < 15:
            raise ValueError(
                "Not enough reliable calibration frames were captured. "
                "Keep your head, shoulders and hips visible and hold your upright posture for the full 5 seconds."
            )

        torso = [s.torso_length_ratio for s in valid]
        vertical = [s.torso_vertical_ratio for s in valid]
        gaps = [s.head_shoulder_gap_ratio for s in valid if s.head_shoulder_gap_ratio > 0]
        depths = [s.torso_depth_ratio for s in valid]
        forward = [s.forward_head_indicator for s in valid]
        shoulders = [s.shoulder_alignment_degrees for s in valid]

        # Learn this user's own upright proportions. Do not reject calibration
        # against a generic body-shape template.
        if (
            _relative_variation(torso) > 0.08
            or _relative_variation(vertical) > 0.08
            or (gaps and _relative_variation(gaps) > 0.10)
            or pstdev(forward) > 0.10
            or pstdev(shoulders) > 2.5
        ):
            raise ValueError(
                "Too much movement was detected. Hold still and try calibration again."
            )

        self.version = CALIBRATION_VERSION
        self.calibrated = True
        self.captured_at = datetime.now(timezone.utc).isoformat()
        self.torso_length_ratio = mean(torso)
        self.torso_vertical_ratio = mean(vertical)
        self.head_shoulder_gap_ratio = mean(gaps) if gaps else 0.0
        self.torso_depth_ratio = mean(depths)
        self.forward_head_indicator = mean(forward)
        # Natural shoulder asymmetry is part of the user's neutral baseline.
        # We care about change from this posture, not perfect anatomical symmetry.
        self.shoulder_alignment_degrees = mean(shoulders)
        self.samples = len(valid)
        self.save()

    def clear(self) -> None:
        self.version = CALIBRATION_VERSION
        self.calibrated = False
        self.captured_at = None
        self.torso_length_ratio = 0.0
        self.torso_vertical_ratio = 0.0
        self.head_shoulder_gap_ratio = 0.0
        self.torso_depth_ratio = 0.0
        self.forward_head_indicator = 0.0
        self.shoulder_alignment_degrees = 0.0
        self.samples = 0
        try:
            CALIBRATION_PATH.unlink(missing_ok=True)
        except OSError:
            pass

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp = CALIBRATION_PATH.with_suffix(".json.tmp")
        temp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        temp.replace(CALIBRATION_PATH)

    def apply_personal_baseline(self, measurement: ErgonomicMeasurements) -> ErgonomicMeasurements:
        """Return posture measurements normalized to the user's calibrated neutral pose."""
        if not self.calibrated:
            return replace(measurement)

        shoulder_delta = max(
            0.0,
            measurement.shoulder_alignment_degrees - self.shoulder_alignment_degrees,
        )
        shoulder_score = max(0.0, 1.0 - shoulder_delta / 20.0)

        # Convert forward-head movement into a personal 0..1 severity score.
        # A roughly 0.11 increase over the calibrated value reaches WARNING
        # and ~0.14 reaches BAD with the existing 0.6 / 0.8 thresholds.
        forward_delta = max(
            0.0,
            measurement.forward_head_indicator - self.forward_head_indicator,
        )
        forward_severity = clamp(forward_delta / 0.18, 0.0, 1.0)

        return replace(
            measurement,
            shoulder_alignment_degrees=shoulder_delta,
            shoulder_alignment_score=shoulder_score,
            forward_head_indicator=forward_severity,
        )

    def slouch_indicator(self, measurement: ErgonomicMeasurements) -> float:
        # Slouch is relative to a person's normal upright posture. Before
        # calibration, do not infer it from absolute body proportions.
        if not self.calibrated:
            return 0.0

        signals: list[float] = []

        if self.torso_vertical_ratio > 0 and measurement.torso_vertical_ratio > 0:
            vertical_drop = self.torso_vertical_ratio - measurement.torso_vertical_ratio
            # Vertical shoulder-to-hip compression is the most reliable
            # front-camera cue for chest collapse / hunching.
            signals.append(
                clamp(
                    vertical_drop / max(self.torso_vertical_ratio * 0.16, 0.10),
                    0.0,
                    1.0,
                )
            )

        if self.torso_length_ratio > 0 and measurement.torso_length_ratio > 0:
            drop = self.torso_length_ratio - measurement.torso_length_ratio
            signals.append(
                clamp(
                    drop / max(self.torso_length_ratio * 0.24, 0.22),
                    0.0,
                    1.0,
                )
            )

            depth_change = measurement.torso_depth_ratio - self.torso_depth_ratio
            signals.append(clamp(depth_change / 0.55, 0.0, 1.0))

        if (
            self.head_shoulder_gap_ratio > 0
            and measurement.head_shoulder_gap_ratio > 0
        ):
            gap_drop = (
                self.head_shoulder_gap_ratio - measurement.head_shoulder_gap_ratio
            )
            signals.append(
                clamp(
                    gap_drop / max(self.head_shoulder_gap_ratio * 0.28, 0.18),
                    0.0,
                    1.0,
                )
            )

        forward_change = (
            measurement.forward_head_indicator - self.forward_head_indicator
        )
        signals.append(clamp(forward_change / 0.35, 0.0, 1.0))

        # Webcam landmarks can jitter, but a front-facing slouch may mainly
        # appear as depth change. Let one strong signal produce a warning while
        # keeping BAD posture dependent on corroboration from another signal.
        if not signals:
            return 0.0

        ordered = sorted(signals, reverse=True)
        strongest = ordered[0]
        second = ordered[1] if len(ordered) > 1 else 0.0
        return clamp(0.55 * strongest + 0.45 * second, 0.0, 1.0)

    def as_dict(self) -> dict:
        return asdict(self)


def _relative_variation(values: list[float]) -> float:
    average = mean(values)
    return 0.0 if abs(average) < 1e-6 else pstdev(values) / abs(average)
