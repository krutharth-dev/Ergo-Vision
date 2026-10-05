from pydantic import BaseModel, Field


class Measurements(BaseModel):
    head_tilt_degrees: float
    shoulder_alignment_score: float
    shoulder_alignment_degrees: float
    neck_offset: float
    forward_head_indicator: float
    gaze_vertical_degrees: float
    torso_lean_degrees: float
    torso_length_ratio: float
    torso_vertical_ratio: float
    head_shoulder_gap_ratio: float
    torso_depth_ratio: float
    slouch_indicator: float


class TrackingInfo(BaseModel):
    confidence: float
    quality: str
    reliable: bool
    head_visible: bool
    shoulders_visible: bool
    hips_visible: bool
    guidance: list[str]


class PostureCurrent(BaseModel):
    score: int
    status: str
    measurements: Measurements
    tracking: TrackingInfo
    feedback: list[str]
    timestamp: str
    person_detected: bool


class SessionStatsResponse(BaseModel):
    session_duration_seconds: float
    good_duration_seconds: float
    warning_duration_seconds: float
    bad_duration_seconds: float
    no_person_duration_seconds: float
    good_percentage: float
    warning_percentage: float
    bad_percentage: float
    no_person_percentage: float
    warning_count: int
    bad_count: int
    average_score: float
    current_score: int
    longest_poor_posture_seconds: float
    active: bool


class CalibrationResponse(BaseModel):
    version: int
    calibrated: bool
    captured_at: str | None
    head_tilt_degrees: float
    shoulder_alignment_degrees: float
    neck_offset: float
    head_shoulder_gap_ratio: float
    forward_head_indicator: float
    samples: int


class CameraDeviceResponse(BaseModel):
    index: int
    label: str
    current: bool


class CameraSelectRequest(BaseModel):
    index: int = Field(ge=0, le=12)


class CameraStatusResponse(BaseModel):
    camera_index: int
    is_opened: bool
    current_fps: float
    frame_width: int
    frame_height: int


class ConfigResponse(BaseModel):
    head_tilt_warning_degrees: float
    head_tilt_bad_degrees: float
    shoulder_alignment_warning_degrees: float
    shoulder_alignment_bad_degrees: float
    neck_offset_warning: float
    neck_offset_bad: float
    forward_head_warning: float
    forward_head_bad: float
    gaze_warning_degrees: float
    gaze_bad_degrees: float
    torso_lean_warning_degrees: float
    torso_lean_bad_degrees: float
    slouch_warning: float
    slouch_bad: float
    score_good_threshold: int
    score_warning_threshold: int
    smoothing_alpha: float
    warning_frames_before_escalation: int
    bad_frames_before_escalation: int
    camera_index: int
    frame_width: int
    frame_height: int
    target_fps: int
    demo_mode: bool


class HealthResponse(BaseModel):
    status: str
    camera_available: bool
    model_loaded: bool
    demo_mode: bool
    uptime_seconds: float
    fps: float


class ReminderSettingsRequest(BaseModel):
    enabled: bool
    poor_posture_seconds: int = Field(ge=10, le=1800)
    movement_break_minutes: int = Field(ge=1, le=30)


class ReminderSettingsResponse(BaseModel):
    enabled: bool
    poor_posture_seconds: int
    movement_break_minutes: int
    background_monitoring: bool
    last_reminder: str
