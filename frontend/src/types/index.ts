export type PostureStatus = 'GOOD' | 'WARNING' | 'BAD' | 'NO_PERSON' | 'LOW_CONFIDENCE' | 'UNKNOWN'

export interface Measurements {
  head_tilt_degrees:number
  shoulder_alignment_score:number
  shoulder_alignment_degrees:number
  neck_offset:number
  forward_head_indicator:number
  gaze_vertical_degrees:number
  torso_lean_degrees:number
  torso_length_ratio:number
  head_shoulder_gap_ratio:number
  torso_depth_ratio:number
  slouch_indicator:number
}

export interface TrackingInfo {
  confidence:number
  quality:'EXCELLENT'|'FAIR'|'POOR'
  reliable:boolean
  head_visible:boolean
  shoulders_visible:boolean
  hips_visible:boolean
  eyes_visible:boolean
  head_confidence:number
  shoulder_confidence:number
  torso_confidence:number
  eye_confidence:number
  guidance:string[]
}

export interface OcularInfo {
  available:boolean
  calibrated:boolean
  confidence:number
  ear:number
  baseline_ear:number
  blink_threshold:number
  blink_count:number
  blink_rate_per_min:number
  inter_blink_interval_seconds:number
  observation_seconds:number
  baseline_observation_seconds:number
  baseline_required_seconds:number
  blink_ready:boolean
  visual_load:number
  proximity_drift:number
}

export interface ExposureInfo {
  instantaneous_risk:number
  confidence_weighted_risk:number
  cumulative_dose:number
  dose_level:'LOW'|'MODERATE'|'HIGH'|string
  continuous_poor_seconds:number
  postural_drift:number
  baseline_risk:number
  recent_risk:number
  baseline_ready:boolean
  baseline_observation_seconds:number
  baseline_required_seconds:number
  available:boolean
}

export interface InterventionInfo {
  state:'NORMAL'|'PENDING'|'ALERTING'|'VERIFYING'|'CORRECTED'|string
  active:boolean
  trigger_seconds:number
  recovery_required_seconds:number
  pending_seconds:number
  verification_seconds:number
  correction_seconds:number
  risk_before:number
  risk_after:number
  improvement_percent:number
  total_interventions:number
  successful_corrections:number
  correction_rate_percent:number
}

export interface PostureEvent {
  score:number
  ergovision_index:number
  combined_risk:number
  proximity_drift:number
  status:PostureStatus
  measurements:Measurements
  tracking:TrackingInfo
  ocular:OcularInfo
  exposure:ExposureInfo
  intervention:InterventionInfo
  feedback:string[]
  timestamp:string
  posture_calibrated:boolean
  person_detected:boolean
}

export interface SessionStats {
  session_duration_seconds:number
  good_duration_seconds:number
  warning_duration_seconds:number
  bad_duration_seconds:number
  no_person_duration_seconds:number
  good_percentage:number
  warning_percentage:number
  bad_percentage:number
  no_person_percentage:number
  warning_count:number
  bad_count:number
  average_score:number
  current_score:number
  longest_poor_posture_seconds:number
  active:boolean
  exposure_dose:number
  exposure_level:string
  postural_drift:number
  blink_rate_per_min:number
  intervention_count:number
  successful_corrections:number
  correction_rate_percent:number
  last_correction_seconds:number
  last_improvement_percent:number
}

export interface CalibrationProfile {
  calibrated:boolean
  captured_at:string|null
  torso_length_ratio:number
  head_shoulder_gap_ratio:number
  torso_depth_ratio:number
  forward_head_indicator:number
  samples:number
}

export interface CameraDevice { index:number; label:string; current:boolean }
export interface CameraStatus { camera_index:number; is_opened:boolean; current_fps:number; frame_width:number; frame_height:number }
export interface SessionHistoryEntry { id:string; ended_at:string; duration_seconds:number; average_score:number; good_percentage:number; warning_percentage:number; bad_percentage:number }
export interface AppConfig { head_tilt_warning_degrees:number; head_tilt_bad_degrees:number; shoulder_alignment_warning_degrees:number; shoulder_alignment_bad_degrees:number; neck_offset_warning:number; neck_offset_bad:number; forward_head_warning:number; forward_head_bad:number; gaze_warning_degrees:number; gaze_bad_degrees:number; torso_lean_warning_degrees:number; torso_lean_bad_degrees:number; slouch_warning:number; slouch_bad:number; score_good_threshold:number; score_warning_threshold:number; smoothing_alpha:number; warning_frames_before_escalation:number; bad_frames_before_escalation:number; camera_index:number; frame_width:number; frame_height:number; target_fps:number; demo_mode:boolean }
export interface HealthStatus { status:string; camera_available:boolean; model_loaded:boolean; demo_mode:boolean; uptime_seconds:number; fps:number }
