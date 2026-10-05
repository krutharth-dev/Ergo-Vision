from dataclasses import dataclass

from ..vision.landmarks import LandmarkSet
from .geometry import (
    angle_from_horizontal,
    angle_from_vertical,
    calculate_distance,
    calculate_midpoint,
    clamp,
)


@dataclass
class ErgonomicMeasurements:
    head_tilt_degrees: float = 0.0
    shoulder_alignment_score: float = 1.0
    shoulder_alignment_degrees: float = 0.0
    neck_offset: float = 0.0
    forward_head_indicator: float = 0.0
    face_scale: float = 0.0
    gaze_vertical_degrees: float = 0.0
    torso_lean_degrees: float = 0.0
    torso_length_ratio: float = 0.0
    torso_vertical_ratio: float = 0.0
    head_shoulder_gap_ratio: float = 0.0
    torso_depth_ratio: float = 0.0
    slouch_indicator: float = 0.0
    person_detected: bool = False


def compute_measurements(landmarks: LandmarkSet | None) -> ErgonomicMeasurements:
    if landmarks is None:
        return ErgonomicMeasurements(person_detected=False)

    required_face = ["nose_tip", "left_eye_outer", "right_eye_outer", "chin", "forehead"]
    required_shoulders = ["left_shoulder", "right_shoulder"]
    required_hips = ["left_hip", "right_hip"]

    has_face = all(landmarks.has(name) for name in required_face)
    has_shoulders = all(landmarks.has(name) for name in required_shoulders)
    has_hips = all(landmarks.has(name) for name in required_hips)

    if not has_face and not has_shoulders:
        return ErgonomicMeasurements(person_detected=False)

    measurements = ErgonomicMeasurements(person_detected=True)

    if has_face:
        measurements.head_tilt_degrees = _compute_head_tilt(landmarks)
        measurements.face_scale = _compute_face_scale(landmarks)
        measurements.gaze_vertical_degrees = _compute_gaze_vertical(landmarks)

    if has_face and has_shoulders:
        measurements.neck_offset = _compute_neck_offset(landmarks)
        measurements.forward_head_indicator = _compute_forward_head(landmarks)
        measurements.head_shoulder_gap_ratio = _compute_head_shoulder_gap(landmarks)

    if has_shoulders:
        (
            measurements.shoulder_alignment_score,
            measurements.shoulder_alignment_degrees,
        ) = _compute_shoulder_alignment(landmarks)

    if has_shoulders and has_hips:
        (
            measurements.torso_lean_degrees,
            measurements.torso_length_ratio,
            measurements.torso_vertical_ratio,
            measurements.torso_depth_ratio,
        ) = _compute_torso_metrics(landmarks)

    measurements.slouch_indicator = estimate_slouch(measurements)
    return measurements


def estimate_slouch(m: ErgonomicMeasurements) -> float:
    signals: list[float] = []

    if m.torso_length_ratio > 0:
        signals.append(clamp((1.35 - m.torso_length_ratio) / 0.45, 0.0, 1.0))
        signals.append(clamp((m.torso_depth_ratio - 0.25) / 0.55, 0.0, 1.0))

    if m.head_shoulder_gap_ratio > 0:
        signals.append(clamp((1.00 - m.head_shoulder_gap_ratio) / 0.45, 0.0, 1.0))

    return max(signals, default=0.0)


def _compute_head_tilt(landmarks: LandmarkSet) -> float:
    left = landmarks.get_pos("left_eye_outer")
    right = landmarks.get_pos("right_eye_outer")
    if left is None or right is None:
        return 0.0
    return abs(angle_from_horizontal(left, right))


def _compute_shoulder_alignment(landmarks: LandmarkSet) -> tuple[float, float]:
    left = landmarks.get_pos("left_shoulder")
    right = landmarks.get_pos("right_shoulder")
    if left is None or right is None:
        return 1.0, 0.0
    angle = abs(angle_from_horizontal(left, right))
    degrees = abs(angle) if angle <= 90 else 180 - abs(angle)
    alignment = max(0.0, 1.0 - degrees / 20.0)
    return alignment, degrees


def _compute_neck_offset(landmarks: LandmarkSet) -> float:
    nose = landmarks.get_pos("nose_tip")
    left = landmarks.get_pos("left_shoulder")
    right = landmarks.get_pos("right_shoulder")
    if nose is None or left is None or right is None:
        return 0.0
    midpoint = calculate_midpoint(left, right)
    shoulder_width = calculate_distance(left, right)
    if shoulder_width < 1e-6:
        return 0.0
    offset = (nose[0] - midpoint[0]) / shoulder_width
    return clamp(offset, -1.0, 1.0)


def _compute_forward_head(landmarks: LandmarkSet) -> float:
    nose = landmarks.get_pos("nose_tip")
    left = landmarks.get_pos("left_shoulder")
    right = landmarks.get_pos("right_shoulder")
    chin = landmarks.get_pos("chin")
    forehead = landmarks.get_pos("forehead")
    if nose is None or left is None or right is None or chin is None:
        return 0.0
    shoulder_width = calculate_distance(left, right)
    if shoulder_width < 1e-6:
        return 0.0
    face_height = abs(chin[1] - forehead[1]) if forehead else 0.0
    if face_height < 1e-6:
        face_height = abs(chin[1] - nose[1]) * 2.0
    ratio = face_height / shoulder_width
    return clamp((ratio - 0.4) / 0.8, 0.0, 1.0)


def _compute_face_scale(landmarks: LandmarkSet) -> float:
    chin = landmarks.get_pos("chin")
    forehead = landmarks.get_pos("forehead")
    if chin is None or forehead is None:
        return 0.0
    # Landmarks are normalized to image height, so this rises as the user's
    # face moves closer to the camera even if the whole upper body moves too.
    return clamp(abs(chin[1] - forehead[1]), 0.0, 1.0)


def _compute_gaze_vertical(landmarks: LandmarkSet) -> float:
    nose = landmarks.get_pos("nose_tip")
    forehead = landmarks.get_pos("forehead")
    if nose is None or forehead is None:
        return 0.0
    return angle_from_vertical(forehead, nose)


def _compute_head_shoulder_gap(landmarks: LandmarkSet) -> float:
    left_shoulder = landmarks.get_pos("left_shoulder")
    right_shoulder = landmarks.get_pos("right_shoulder")
    left_ear = landmarks.get_pos("left_ear")
    right_ear = landmarks.get_pos("right_ear")
    if not all((left_shoulder, right_shoulder, left_ear, right_ear)):
        return 0.0

    shoulder_width = calculate_distance(left_shoulder, right_shoulder)
    if shoulder_width < 1e-6:
        return 0.0

    shoulder_mid = calculate_midpoint(left_shoulder, right_shoulder)
    ear_mid = calculate_midpoint(left_ear, right_ear)
    vertical_gap = max(0.0, shoulder_mid[1] - ear_mid[1])
    return vertical_gap / shoulder_width


def _compute_torso_metrics(landmarks: LandmarkSet) -> tuple[float, float, float, float]:
    left_shoulder = landmarks.get("left_shoulder")
    right_shoulder = landmarks.get("right_shoulder")
    left_hip = landmarks.get("left_hip")
    right_hip = landmarks.get("right_hip")
    if not all((left_shoulder, right_shoulder, left_hip, right_hip)):
        return 0.0, 0.0, 0.0, 0.0

    left_shoulder_pos = (left_shoulder.x, left_shoulder.y)
    right_shoulder_pos = (right_shoulder.x, right_shoulder.y)
    left_hip_pos = (left_hip.x, left_hip.y)
    right_hip_pos = (right_hip.x, right_hip.y)

    shoulder_mid = calculate_midpoint(left_shoulder_pos, right_shoulder_pos)
    hip_mid = calculate_midpoint(left_hip_pos, right_hip_pos)
    shoulder_width = calculate_distance(left_shoulder_pos, right_shoulder_pos)
    if shoulder_width < 1e-6:
        return 0.0, 0.0, 0.0, 0.0

    torso_lean = abs(angle_from_vertical(hip_mid, shoulder_mid))
    torso_length_ratio = calculate_distance(shoulder_mid, hip_mid) / shoulder_width
    torso_vertical_ratio = max(0.0, hip_mid[1] - shoulder_mid[1]) / shoulder_width

    shoulder_z = (left_shoulder.z + right_shoulder.z) / 2.0
    hip_z = (left_hip.z + right_hip.z) / 2.0
    torso_depth_ratio = clamp((hip_z - shoulder_z) / shoulder_width, -2.0, 2.0)

    return torso_lean, torso_length_ratio, torso_vertical_ratio, torso_depth_ratio
