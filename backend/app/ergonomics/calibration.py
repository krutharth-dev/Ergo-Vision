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
CALIBRATION_VERSION = 7


@dataclass
class CalibrationProfile:
    version: int = CALIBRATION_VERSION
    calibrated: bool = False
    captured_at: str | None = None
    head_tilt_degrees: float = 0.0
    shoulder_alignment_degrees: float = 0.0
    neck_offset: float = 0.0
    head_shoulder_gap_ratio: float = 0.0
    forward_head_indicator: float = 0.0
    samples: int = 0

    @classmethod
    def load(cls) -> "CalibrationProfile":
        try:
            data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
            if data.get("version") != CALIBRATION_VERSION:
                return cls()
            return cls(**data)
        except (OSError, ValueError, TypeError):
            return cls()

    def capture(self, samples: list[ErgonomicMeasurements]) -> None:
        valid = [
            sample
            for sample in samples
            if sample.person_detected
            and sample.head_shoulder_gap_ratio > 0
        ]
        if len(valid) < 15:
            raise ValueError(
                "Not enough reliable head-and-shoulder frames were captured. "
                "Keep your full head and both shoulders visible for the full 5 seconds."
            )

        head_tilts = [s.head_tilt_degrees for s in valid]
        shoulders = [s.shoulder_alignment_degrees for s in valid]
        neck_offsets = [s.neck_offset for s in valid]
        gaps = [s.head_shoulder_gap_ratio for s in valid]
        forward = [s.forward_head_indicator for s in valid]

        if (
            pstdev(head_tilts) > 2.5
            or pstdev(shoulders) > 2.5
            or pstdev(neck_offsets) > 0.08
            or _relative_variation(gaps) > 0.12
            or pstdev(forward) > 0.10
        ):
            raise ValueError(
                "Too much movement was detected. Hold your normal comfortable posture still and try again."
            )

        self.version = CALIBRATION_VERSION
        self.calibrated = True
        self.captured_at = datetime.now(timezone.utc).isoformat()
        self.head_tilt_degrees = mean(head_tilts)
        self.shoulder_alignment_degrees = mean(shoulders)
        self.neck_offset = mean(neck_offsets)
        self.head_shoulder_gap_ratio = mean(gaps)
        self.forward_head_indicator = mean(forward)
        self.samples = len(valid)
        self.save()

    def clear(self) -> None:
        self.version = CALIBRATION_VERSION
        self.calibrated = False
        self.captured_at = None
        self.head_tilt_degrees = 0.0
        self.shoulder_alignment_degrees = 0.0
        self.neck_offset = 0.0
        self.head_shoulder_gap_ratio = 0.0
        self.forward_head_indicator = 0.0
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
        if not self.calibrated:
            return replace(
                measurement,
                gaze_vertical_degrees=0.0,
                torso_lean_degrees=0.0,
                torso_length_ratio=0.0,
                torso_vertical_ratio=0.0,
                torso_depth_ratio=0.0,
            )

        head_tilt_delta = max(0.0, measurement.head_tilt_degrees - self.head_tilt_degrees)
        shoulder_delta = max(
            0.0,
            measurement.shoulder_alignment_degrees - self.shoulder_alignment_degrees,
        )
        neck_delta = measurement.neck_offset - self.neck_offset

        forward_delta = max(
            0.0,
            measurement.forward_head_indicator - self.forward_head_indicator,
        )
        forward_severity = clamp(forward_delta / 0.18, 0.0, 1.0)

        # After personal calibration, hip/torso measurements are intentionally
        # excluded from posture classification. Head + shoulders only.
        return replace(
            measurement,
            head_tilt_degrees=head_tilt_delta,
            shoulder_alignment_degrees=shoulder_delta,
            shoulder_alignment_score=max(0.0, 1.0 - shoulder_delta / 20.0),
            neck_offset=neck_delta,
            forward_head_indicator=forward_severity,
            gaze_vertical_degrees=0.0,
            torso_lean_degrees=0.0,
            torso_length_ratio=0.0,
            torso_vertical_ratio=0.0,
            torso_depth_ratio=0.0,
        )

    def slouch_indicator(self, measurement: ErgonomicMeasurements) -> float:
        """Head-and-shoulder-only hunch signal relative to the personal baseline."""
        if not self.calibrated:
            return 0.0

        signals: list[float] = []

        if self.head_shoulder_gap_ratio > 0 and measurement.head_shoulder_gap_ratio > 0:
            gap_drop = self.head_shoulder_gap_ratio - measurement.head_shoulder_gap_ratio
            signals.append(
                clamp(
                    gap_drop / max(self.head_shoulder_gap_ratio * 0.24, 0.14),
                    0.0,
                    1.0,
                )
            )

        forward_change = max(
            0.0,
            measurement.forward_head_indicator - self.forward_head_indicator,
        )
        signals.append(clamp(forward_change / 0.20, 0.0, 1.0))

        return max(signals, default=0.0)

    def as_dict(self) -> dict:
        return asdict(self)


def _relative_variation(values: list[float]) -> float:
    average = mean(values)
    return 0.0 if abs(average) < 1e-6 else pstdev(values) / abs(average)
