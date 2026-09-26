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
    eyes_visible: bool
    head_confidence: float
    shoulder_confidence: float
    torso_confidence: float
    eye_confidence: float
    guidance: list[str]


class OcularInfo(BaseModel):
    available: bool
    calibrated: bool
    confidence: float
    ear: float
    baseline_ear: float
    blink_threshold: float
    blink_count: int
    blink_rate_per_min: float
    inter_blink_interval_seconds: float
    observation_seconds: float
    baseline_observation_seconds: float
    baseline_required_seconds: float
    blink_ready: bool
    visual_load: float
    proximity_drift: float


class ExposureInfo(BaseModel):
    instantaneous_risk: float
    confidence_weighted_risk: float
    cumulative_dose: float
    dose_level: str
    continuous_poor_seconds: float
    postural_drift: float
    baseline_risk: float
    recent_risk: float
    baseline_ready: bool
    baseline_observation_seconds: float
    baseline_required_seconds: float
    available: bool


class InterventionInfo(BaseModel):
    state: str
    active: bool
    trigger_seconds: float
    recovery_required_seconds: float
    pending_seconds: float
    verification_seconds: float
    correction_seconds: float
    risk_before: float
    risk_after: float
    improvement_percent: float
    total_interventions: int
    successful_corrections: int
    correction_rate_percent: float


class PostureCurrent(BaseModel):
    score: int
    ergovision_index: int
    combined_risk: float
    proximity_drift: float
    status: str
    measurements: Measurements
    tracking: TrackingInfo
    ocular: OcularInfo
    exposure: ExposureInfo
    intervention: InterventionInfo
    feedback: list[str]
    timestamp: str
    posture_calibrated: bool
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
    exposure_dose: float
    exposure_level: str
    postural_drift: float
    blink_rate_per_min: float
    intervention_count: int
    successful_corrections: int
    correction_rate_percent: float
    last_correction_seconds: float
    last_improvement_percent: float


class CalibrationResponse(BaseModel):
    calibrated: bool
    captured_at: str | None
    torso_length_ratio: float
    head_shoulder_gap_ratio: float
    torso_depth_ratio: float
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
