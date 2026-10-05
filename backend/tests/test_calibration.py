from pathlib import Path

import app.ergonomics.calibration as calibration_module
from app.ergonomics.calibration import CalibrationProfile
from app.ergonomics.measurements import ErgonomicMeasurements


def measurement(torso=1.7, gap=1.4, depth=0.0, forward=0.2):
    return ErgonomicMeasurements(
        person_detected=True,
        torso_length_ratio=torso,
        head_shoulder_gap_ratio=gap,
        torso_depth_ratio=depth,
        forward_head_indicator=forward,
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

    hunched = measurement(torso=1.15, gap=0.85, depth=0.5, forward=0.55)
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
