from __future__ import annotations

from dataclasses import asdict, dataclass

from .landmarks import Landmark2D, LandmarkSet


@dataclass
class TrackingAssessment:
    confidence: float = 0.0
    quality: str = "POOR"
    reliable: bool = False
    head_visible: bool = False
    shoulders_visible: bool = False
    hips_visible: bool = False
    guidance: list[str] | None = None

    def as_dict(self) -> dict:
        data = asdict(self)
        data["guidance"] = self.guidance or []
        return data


def _confidence(landmark: Landmark2D | None) -> float:
    if landmark is None:
        return 0.0
    values = [v for v in (landmark.visibility, landmark.presence) if v is not None and v > 0]
    return 1.0 if not values else max(0.0, min(1.0, sum(values) / len(values)))


def _group(landmarks: LandmarkSet, names: tuple[str, ...]) -> float:
    return sum(_confidence(landmarks.get(name)) for name in names) / len(names)


def assess_tracking(landmarks: LandmarkSet | None) -> TrackingAssessment:
    if landmarks is None:
        return TrackingAssessment(guidance=["Move into frame so your head and shoulders are visible."])

    heads = ("nose_tip", "left_eye_outer", "right_eye_outer", "chin", "forehead")
    shoulders = ("left_shoulder", "right_shoulder")
    hips = ("left_hip", "right_hip")
    hs, ss = _group(landmarks, heads), _group(landmarks, shoulders)
    ps = _group(landmarks, hips)
    head_visible = all(landmarks.has(n) for n in heads) and hs >= 0.45
    shoulders_visible = all(landmarks.has(n) for n in shoulders) and ss >= 0.45
    hips_visible = all(landmarks.has(n) for n in hips) and ps >= 0.45
    confidence = 0.55 * hs + 0.45 * ss
    reliable = head_visible and shoulders_visible and confidence >= 0.55
    quality = "EXCELLENT" if reliable and confidence >= 0.82 else "FAIR" if reliable else "POOR"
    guidance = []
    if not head_visible:
        guidance.append("Keep your full head and face visible.")
    if not shoulders_visible:
        guidance.append("Move back until both shoulders are visible.")
    if confidence < 0.55:
        guidance.append("Improve lighting and face the camera more directly.")
    return TrackingAssessment(round(confidence, 3), quality, reliable, head_visible, shoulders_visible, hips_visible, guidance)
