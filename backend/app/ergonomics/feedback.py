from ..config import (
    FORWARD_HEAD_BAD,
    FORWARD_HEAD_WARNING,
    HEAD_TILT_BAD_DEGREES,
    HEAD_TILT_WARNING_DEGREES,
    NECK_OFFSET_BAD,
    NECK_OFFSET_WARNING,
    SHOULDER_ALIGNMENT_BAD_DEGREES,
    SHOULDER_ALIGNMENT_WARNING_DEGREES,
    SLOUCH_BAD,
    SLOUCH_WARNING,
    TORSO_LEAN_BAD_DEGREES,
    TORSO_LEAN_WARNING_DEGREES,
)
from .measurements import ErgonomicMeasurements


class FeedbackEngine:
    def generate(self, measurement: ErgonomicMeasurements, status: str) -> list[str]:
        if not measurement.person_detected:
            return ["No person detected. Position yourself in front of the camera."]

        messages: list[tuple[str, str]] = []

        if measurement.slouch_indicator >= SLOUCH_BAD:
            messages.append(("BAD", "You appear to be slouching. Lift your chest, bring your shoulders back, and sit tall."))
        elif measurement.slouch_indicator >= SLOUCH_WARNING:
            messages.append(("WARNING", "Your upper body is beginning to collapse forward. Sit taller and reset your shoulders."))

        if measurement.torso_lean_degrees >= TORSO_LEAN_BAD_DEGREES:
            messages.append(("BAD", "Your torso is leaning to the side. Re-center your trunk over your hips."))
        elif measurement.torso_lean_degrees >= TORSO_LEAN_WARNING_DEGREES:
            messages.append(("WARNING", "Your torso is drifting off-center. Re-center over your hips."))

        if measurement.head_tilt_degrees >= HEAD_TILT_BAD_DEGREES:
            messages.append(("BAD", "Your head is tilted significantly. Straighten your head to face the screen directly."))
        elif measurement.head_tilt_degrees >= HEAD_TILT_WARNING_DEGREES:
            messages.append(("WARNING", "Your head is tilted slightly. Try to keep your head level."))

        if measurement.shoulder_alignment_degrees >= SHOULDER_ALIGNMENT_BAD_DEGREES:
            messages.append(("BAD", "Your shoulders are uneven. Try to level them by sitting up straighter."))
        elif measurement.shoulder_alignment_degrees >= SHOULDER_ALIGNMENT_WARNING_DEGREES:
            messages.append(("WARNING", "Your shoulders are slightly uneven. Adjust your posture to align them."))

        if abs(measurement.neck_offset) >= NECK_OFFSET_BAD:
            direction = "left" if measurement.neck_offset < 0 else "right"
            messages.append(("BAD", f"Your head is leaning to the {direction}. Center your head over your shoulders."))
        elif abs(measurement.neck_offset) >= NECK_OFFSET_WARNING:
            direction = "left" if measurement.neck_offset < 0 else "right"
            messages.append(("WARNING", f"Your head is slightly to the {direction}. Try to center it over your spine."))

        if measurement.forward_head_indicator >= FORWARD_HEAD_BAD:
            messages.append(("BAD", "You have moved too far toward the screen. Sit back and bring your head over your shoulders."))
        elif measurement.forward_head_indicator >= FORWARD_HEAD_WARNING:
            messages.append(("WARNING", "You are moving closer to the screen than your calibrated position. Sit back slightly and re-center your head."))

        if not messages:
            if status == "GOOD":
                return ["Your posture looks good. Keep it up!"]
            return ["Maintain an upright posture with your head centered."]

        messages.sort(key=_severity_order)
        return [message for _, message in messages[:3]]


def _severity_order(item: tuple[str, str]) -> int:
    return {"BAD": 0, "WARNING": 1}.get(item[0], 2)
