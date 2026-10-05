from pathlib import Path

import app.ergonomics.calibration as calibration_module
from app.ergonomics.calibration import CalibrationProfile
from app.ergonomics.measurements import ErgonomicMeasurements


def measurement(torso=1.7, vertical=1.6, gap=1.4, depth=0.0, forward=0.2, shoulder=0.0):
    return ErgonomicMeasurements(
        person_detected=True,
        torso_length_ratio=torso,
        torso_vertical_ratio=vertical,
        head_shoulder_gap_ratio=gap,
        torso_depth_ratio=depth,
        forward_head_indicator=forward,
        shoulder_alignment_degrees=shoulder,
    )


def test_uncalibrated_profile_does_not_guess_slouch_from_body_proportions():
    profile = CalibrationProfile()
    unusual_but_upright = measurement(torso=0.95, gap=0.72, depth=0.35, forward=0.55)
    assert profile.slouch_indicator(unusual_but_upright) == 0.0


def test_calibration_accepts_stable_personal_proportions(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture(
        [measurement(torso=0.95, gap=0.72, depth=0.35, forward=0.55) for _ in range(20)]
    )
    assert profile.calibrated
    assert profile.slouch_indicator(
        measurement(torso=0.95, gap=0.72, depth=0.35, forward=0.55)
    ) < 0.1


def test_calibration_detects_correlated_posture_change(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement() for _ in range(20)])
    assert profile.calibrated
    assert profile.slouch_indicator(measurement()) < 0.1

    hunched = measurement(torso=1.15, vertical=1.05, gap=0.85, depth=0.5, forward=0.55)
    assert profile.slouch_indicator(hunched) >= 0.7


def test_mild_single_signal_jitter_does_not_trigger_slouch(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement() for _ in range(20)])

    mild_depth_jitter = measurement(depth=0.2)
    assert profile.slouch_indicator(mild_depth_jitter) < 0.35


def test_strong_depth_only_change_can_trigger_warning(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement() for _ in range(20)])

    front_facing_slouch = measurement(depth=0.55)
    indicator = profile.slouch_indicator(front_facing_slouch)
    assert 0.35 <= indicator < 0.70


def test_old_calibration_profile_is_invalidated(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")
    (tmp_path / "calibration.json").write_text(
        '{"calibrated": true, "torso_length_ratio": 1.7, '
        '"head_shoulder_gap_ratio": 1.4, "torso_depth_ratio": 0.0, '
        '"forward_head_indicator": 0.2, "samples": 20}',
        encoding="utf-8",
    )

    profile = CalibrationProfile.load()
    assert not profile.calibrated


def test_calibration_requires_enough_samples():
    profile = CalibrationProfile()
    try:
        profile.capture([measurement() for _ in range(3)])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected calibration to require more samples")


def test_vertical_compression_alone_can_trigger_slouch_warning(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement() for _ in range(20)])

    compressed = measurement(vertical=1.30)
    assert profile.slouch_indicator(compressed) >= 0.35



def test_calibration_accepts_stable_natural_shoulder_asymmetry(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement(shoulder=7.0) for _ in range(20)])

    assert profile.calibrated
    assert abs(profile.shoulder_alignment_degrees - 7.0) < 0.01

    neutral = profile.apply_personal_baseline(measurement(shoulder=7.0))
    assert neutral.shoulder_alignment_degrees == 0.0
    assert neutral.shoulder_alignment_score == 1.0


def test_only_extra_shoulder_imbalance_is_penalized(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement(shoulder=6.0) for _ in range(20)])

    slightly_more_uneven = profile.apply_personal_baseline(measurement(shoulder=9.0))
    assert abs(slightly_more_uneven.shoulder_alignment_degrees - 3.0) < 0.01



def test_forward_head_is_relative_to_personal_baseline(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(calibration_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(calibration_module, "CALIBRATION_PATH", tmp_path / "calibration.json")

    profile = CalibrationProfile()
    profile.capture([measurement(forward=0.20) for _ in range(20)])

    neutral = profile.apply_personal_baseline(measurement(forward=0.20))
    warning = profile.apply_personal_baseline(measurement(forward=0.32))
    bad = profile.apply_personal_baseline(measurement(forward=0.36))

    assert neutral.forward_head_indicator == 0.0
    assert warning.forward_head_indicator >= 0.60
    assert bad.forward_head_indicator >= 0.80
