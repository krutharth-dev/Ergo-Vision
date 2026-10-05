from pathlib import Path

import app.ergonomics.calibration as calibration_module
from app.ergonomics.calibration import CalibrationProfile
from app.ergonomics.measurements import ErgonomicMeasurements


def measurement(
    *,
    head_tilt=2.0,
    shoulder=6.0,
    neck=0.03,
    gap=1.20,
    forward=0.25,
    torso_lean=20.0,
    torso=0.0,
    vertical=0.0,
    depth=0.0,
):
    return ErgonomicMeasurements(
        person_detected=True,
        head_tilt_degrees=head_tilt,
        shoulder_alignment_degrees=shoulder,
        neck_offset=neck,
        head_shoulder_gap_ratio=gap,
        forward_head_indicator=forward,
        torso_lean_degrees=torso_lean,
        torso_length_ratio=torso,
        torso_vertical_ratio=vertical,
        torso_depth_ratio=depth,
    )


def configure_paths(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")


def test_calibration_needs_only_head_and_shoulders(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()

    profile.capture([measurement() for _ in range(20)])

    assert profile.calibrated
    assert profile.samples == 20


def test_natural_shoulder_asymmetry_becomes_neutral(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()
    profile.capture([measurement(shoulder=7.0) for _ in range(20)])

    neutral = profile.apply_personal_baseline(measurement(shoulder=7.0))
    slightly_more = profile.apply_personal_baseline(measurement(shoulder=10.0))

    assert neutral.shoulder_alignment_degrees == 0.0
    assert neutral.shoulder_alignment_score == 1.0
    assert abs(slightly_more.shoulder_alignment_degrees - 3.0) < 0.01


def test_natural_head_tilt_becomes_neutral(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()
    profile.capture([measurement(head_tilt=4.0) for _ in range(20)])

    neutral = profile.apply_personal_baseline(measurement(head_tilt=4.0))
    changed = profile.apply_personal_baseline(measurement(head_tilt=10.0))

    assert neutral.head_tilt_degrees == 0.0
    assert abs(changed.head_tilt_degrees - 6.0) < 0.01


def test_forward_head_is_relative_to_baseline(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()
    profile.capture([measurement(forward=0.20) for _ in range(20)])

    neutral = profile.apply_personal_baseline(measurement(forward=0.20))
    warning = profile.apply_personal_baseline(measurement(forward=0.32))

    assert neutral.forward_head_indicator == 0.0
    assert warning.forward_head_indicator >= 0.60


def test_head_shoulder_gap_can_detect_hunch(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()
    profile.capture([measurement(gap=1.20, forward=0.20) for _ in range(20)])

    neutral = measurement(gap=1.20, forward=0.20)
    hunched = measurement(gap=0.85, forward=0.20)

    assert profile.slouch_indicator(neutral) < 0.1
    assert profile.slouch_indicator(hunched) >= 0.35


def test_torso_and_hip_metrics_are_ignored_after_baseline(tmp_path: Path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    profile = CalibrationProfile()
    profile.capture([measurement() for _ in range(20)])

    evaluated = profile.apply_personal_baseline(
        measurement(torso_lean=35.0, torso=0.6, vertical=0.4, depth=1.2)
    )

    assert evaluated.torso_lean_degrees == 0.0
    assert evaluated.torso_length_ratio == 0.0
    assert evaluated.torso_vertical_ratio == 0.0
    assert evaluated.torso_depth_ratio == 0.0
    assert evaluated.gaze_vertical_degrees == 0.0


def test_calibration_requires_enough_head_shoulder_samples():
    profile = CalibrationProfile()
    try:
        profile.capture([measurement() for _ in range(3)])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected calibration to require more samples")
