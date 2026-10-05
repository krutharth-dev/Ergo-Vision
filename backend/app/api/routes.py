import time
from typing import Optional

from fastapi import APIRouter, HTTPException

import app.config as config
from ..pipeline import PosturePipeline
from .schemas import (
    CalibrationResponse,
    CameraDeviceResponse,
    CameraSelectRequest,
    CameraStatusResponse,
    ConfigResponse,
    HealthResponse,
    PostureCurrent,
    ReminderSettingsRequest,
    ReminderSettingsResponse,
    SessionStatsResponse,
)

router = APIRouter()


def _get_pipeline() -> Optional[PosturePipeline]:
    from ..main import get_pipeline
    return get_pipeline()


def _require_pipeline() -> PosturePipeline:
    pipe = _get_pipeline()
    if pipe is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return pipe


@router.get("/health", response_model=HealthResponse)
def health():
    from ..main import _start_time
    pipe = _get_pipeline()
    camera_ok = pipe.camera.is_opened if pipe else False
    model_ok = pipe.detector.model_loaded if pipe else False
    return HealthResponse(
        status="healthy",
        camera_available=camera_ok,
        model_loaded=model_ok,
        demo_mode=config.DEMO_MODE,
        uptime_seconds=round(time.time() - _start_time, 1),
        fps=round(pipe.camera.current_fps, 1) if pipe else 0.0,
    )


@router.get("/api/posture/current", response_model=PostureCurrent)
def current_posture():
    return PostureCurrent(**_require_pipeline().get_current())


@router.get("/api/session/stats", response_model=SessionStatsResponse)
def session_stats():
    return SessionStatsResponse(**_require_pipeline().get_session_stats())


@router.post("/api/session/start", response_model=SessionStatsResponse)
def session_start():
    pipe = _require_pipeline()
    pipe.tracker.start()
    return SessionStatsResponse(**pipe.get_session_stats())


@router.post("/api/session/stop", response_model=SessionStatsResponse)
def session_stop():
    pipe = _require_pipeline()
    pipe.tracker.stop()
    return SessionStatsResponse(**pipe.get_session_stats())


@router.post("/api/session/reset", response_model=SessionStatsResponse)
def session_reset():
    pipe = _require_pipeline()
    pipe.tracker.reset()
    pipe.tracker.start()
    return SessionStatsResponse(**pipe.get_session_stats())


@router.get("/api/calibration", response_model=CalibrationResponse)
def calibration_status():
    return CalibrationResponse(**_require_pipeline().get_calibration())


@router.post("/api/calibration/capture", response_model=CalibrationResponse)
def calibration_capture():
    pipe = _require_pipeline()
    try:
        return CalibrationResponse(**pipe.capture_calibration(duration_seconds=5.0))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/api/calibration", response_model=CalibrationResponse)
def calibration_clear():
    return CalibrationResponse(**_require_pipeline().clear_calibration())


@router.get("/api/camera/devices", response_model=list[CameraDeviceResponse])
def camera_devices():
    return [CameraDeviceResponse(**item) for item in _require_pipeline().camera_devices()]

@router.post("/api/camera/select", response_model=CameraStatusResponse)
def camera_select(request: CameraSelectRequest):
    try:
        return CameraStatusResponse(**_require_pipeline().select_camera(request.index))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/config", response_model=ConfigResponse)
def get_config():
    return ConfigResponse(
        head_tilt_warning_degrees=config.HEAD_TILT_WARNING_DEGREES,
        head_tilt_bad_degrees=config.HEAD_TILT_BAD_DEGREES,
        shoulder_alignment_warning_degrees=config.SHOULDER_ALIGNMENT_WARNING_DEGREES,
        shoulder_alignment_bad_degrees=config.SHOULDER_ALIGNMENT_BAD_DEGREES,
        neck_offset_warning=config.NECK_OFFSET_WARNING,
        neck_offset_bad=config.NECK_OFFSET_BAD,
        forward_head_warning=config.FORWARD_HEAD_WARNING,
        forward_head_bad=config.FORWARD_HEAD_BAD,
        gaze_warning_degrees=config.GAZE_WARNING_DEGREES,
        gaze_bad_degrees=config.GAZE_BAD_DEGREES,
        torso_lean_warning_degrees=config.TORSO_LEAN_WARNING_DEGREES,
        torso_lean_bad_degrees=config.TORSO_LEAN_BAD_DEGREES,
        slouch_warning=config.SLOUCH_WARNING,
        slouch_bad=config.SLOUCH_BAD,
        score_good_threshold=config.SCORE_GOOD_THRESHOLD,
        score_warning_threshold=config.SCORE_WARNING_THRESHOLD,
        smoothing_alpha=config.SMOOTHING_ALPHA,
        warning_frames_before_escalation=config.WARNING_FRAMES_BEFORE_ESCALATION,
        bad_frames_before_escalation=config.BAD_FRAMES_BEFORE_ESCALATION,
        camera_index=config.CAMERA_INDEX,
        frame_width=config.FRAME_WIDTH,
        frame_height=config.FRAME_HEIGHT,
        target_fps=config.TARGET_FPS,
        demo_mode=config.DEMO_MODE,
    )


@router.get("/api/reminders", response_model=ReminderSettingsResponse)
def reminder_settings():
    return ReminderSettingsResponse(**_require_pipeline().get_reminder_settings())


@router.post("/api/reminders", response_model=ReminderSettingsResponse)
def reminder_settings_update(request: ReminderSettingsRequest):
    pipe = _require_pipeline()
    return ReminderSettingsResponse(
        **pipe.configure_reminders(
            enabled=request.enabled,
            poor_posture_seconds=request.poor_posture_seconds,
            movement_break_minutes=request.movement_break_minutes,
        )
    )
