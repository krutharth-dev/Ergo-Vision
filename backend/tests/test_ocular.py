from app.ergonomics.ocular import OcularEngine, calculate_ear
from app.vision.landmarks import Landmark2D, LandmarkSet


def eye_landmarks(closed: bool = False) -> LandmarkSet:
    v = 0.003 if closed else 0.02
    data = {
        "left_eye_outer": Landmark2D(0.40, 0.40),
        "left_eye_upper_outer": Landmark2D(0.43, 0.40 - v),
        "left_eye_upper_inner": Landmark2D(0.47, 0.40 - v),
        "left_eye_inner": Landmark2D(0.50, 0.40),
        "left_eye_lower_inner": Landmark2D(0.47, 0.40 + v),
        "left_eye_lower_outer": Landmark2D(0.43, 0.40 + v),
        "right_eye_inner": Landmark2D(0.55, 0.40),
        "right_eye_upper_inner": Landmark2D(0.58, 0.40 - v),
        "right_eye_upper_outer": Landmark2D(0.62, 0.40 - v),
        "right_eye_outer": Landmark2D(0.65, 0.40),
        "right_eye_lower_outer": Landmark2D(0.62, 0.40 + v),
        "right_eye_lower_inner": Landmark2D(0.58, 0.40 + v),
    }
    return LandmarkSet(data)


def test_ear_drops_when_eye_closes():
    assert calculate_ear(eye_landmarks(False)) > calculate_ear(eye_landmarks(True))


def test_personal_baseline_and_blink_detection():
    engine = OcularEngine(baseline_seconds=1.0)
    for i in range(12):
        engine.update(eye_landmarks(False), eye_confidence=1.0, timestamp=i * 0.1)
    assert engine.current().calibrated
    assert engine.current().baseline_observation_seconds >= 1.0
    assert engine.current().baseline_required_seconds == 1.0

    engine.update(eye_landmarks(True), eye_confidence=1.0, timestamp=1.2)
    engine.update(eye_landmarks(True), eye_confidence=1.0, timestamp=1.3)
    snapshot = engine.update(eye_landmarks(False), eye_confidence=1.0, timestamp=1.4)
    assert snapshot.blink_count == 1


def test_low_confidence_disables_measurement():
    engine = OcularEngine()
    snapshot = engine.update(eye_landmarks(False), eye_confidence=0.1, timestamp=0.0)
    assert not snapshot.available


def test_eye_baseline_requires_contiguous_valid_observation():
    engine = OcularEngine(baseline_seconds=1.0)

    for i in range(5):
        engine.update(eye_landmarks(False), eye_confidence=1.0, timestamp=i * 0.1)

    interrupted = engine.update(
        eye_landmarks(False),
        eye_confidence=0.1,
        timestamp=5.0,
    )
    assert not interrupted.calibrated
    before_resume = interrupted.baseline_observation_seconds

    resumed = engine.update(
        eye_landmarks(False),
        eye_confidence=1.0,
        timestamp=5.1,
    )
    assert resumed.baseline_observation_seconds == before_resume
    assert not resumed.calibrated


def test_blink_readiness_is_explicit_after_warmup():
    engine = OcularEngine(baseline_seconds=1.0)
    for i in range(12):
        engine.update(eye_landmarks(False), eye_confidence=1.0, timestamp=i * 0.1)

    assert engine.current().calibrated
    assert not engine.current().blink_ready

    ready = engine.update(
        eye_landmarks(False),
        eye_confidence=1.0,
        timestamp=15.1,
    )
    assert ready.blink_ready
