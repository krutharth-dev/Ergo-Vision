from dataclasses import dataclass, field

from ..config import SMOOTHING_ALPHA
from .measurements import ErgonomicMeasurements


@dataclass
class SmoothingBuffer:
    alpha: float = SMOOTHING_ALPHA
    _prev: ErgonomicMeasurements | None = field(default=None, repr=False)

    def smooth(self, new: ErgonomicMeasurements) -> ErgonomicMeasurements:
        if not new.person_detected:
            self._prev = None
            return new

        if self._prev is None or not self._prev.person_detected:
            self._prev = new
            return new

        a = self.alpha
        prev = self._prev

        smoothed = ErgonomicMeasurements(
            head_tilt_degrees=a * new.head_tilt_degrees + (1 - a) * prev.head_tilt_degrees,
            shoulder_alignment_score=a * new.shoulder_alignment_score + (1 - a) * prev.shoulder_alignment_score,
            shoulder_alignment_degrees=a * new.shoulder_alignment_degrees + (1 - a) * prev.shoulder_alignment_degrees,
            neck_offset=a * new.neck_offset + (1 - a) * prev.neck_offset,
            forward_head_indicator=a * new.forward_head_indicator + (1 - a) * prev.forward_head_indicator,
            face_scale=a * new.face_scale + (1 - a) * prev.face_scale,
            gaze_vertical_degrees=a * new.gaze_vertical_degrees + (1 - a) * prev.gaze_vertical_degrees,
            torso_lean_degrees=a * new.torso_lean_degrees + (1 - a) * prev.torso_lean_degrees,
            torso_length_ratio=a * new.torso_length_ratio + (1 - a) * prev.torso_length_ratio,
            torso_vertical_ratio=a * new.torso_vertical_ratio + (1 - a) * prev.torso_vertical_ratio,
            head_shoulder_gap_ratio=a * new.head_shoulder_gap_ratio + (1 - a) * prev.head_shoulder_gap_ratio,
            torso_depth_ratio=a * new.torso_depth_ratio + (1 - a) * prev.torso_depth_ratio,
            slouch_indicator=a * new.slouch_indicator + (1 - a) * prev.slouch_indicator,
            person_detected=True,
        )

        self._prev = smoothed
        return smoothed

    def reset(self):
        self._prev = None
