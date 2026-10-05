import type { AppConfig, PostureEvent } from '../types'

interface Props {
  posture: PostureEvent | null
  config: AppConfig | null
}

const SHOULDER_LABEL = (score: number) => {
  if (score >= 0.95) return 'Good'
  if (score >= 0.75) return 'Slight Imbalance'
  return 'Poor'
}

const SLOUCH_LABEL = (value: number, config: AppConfig | null) => {
  if (!config) return '—'
  if (value >= config.slouch_bad) return 'Poor'
  if (value >= config.slouch_warning) return 'Slouching'
  return 'Upright'
}

export default function Metrics({ posture, config }: Props) {
  const measurement = posture?.measurements
  if (!measurement) {
    return (
      <div className="card">
        <div className="card-title">Ergonomic Metrics</div>
        <p>Waiting for data…</p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-title">Ergonomic Metrics</div>
      <table className="metrics-table">
        <tbody>
          <tr><td>Slouch / Hunch</td><td>{SLOUCH_LABEL(measurement.slouch_indicator, config)} ({measurement.slouch_indicator.toFixed(2)})</td></tr>
          <tr><td>Head Tilt</td><td>{measurement.head_tilt_degrees.toFixed(1)}°</td></tr>
          <tr><td>Shoulder Angle</td><td>{measurement.shoulder_alignment_degrees.toFixed(1)}°</td></tr>
          <tr><td>Shoulder Alignment</td><td>{SHOULDER_LABEL(measurement.shoulder_alignment_score)}</td></tr>
          <tr><td>Neck Offset</td><td>{(measurement.neck_offset > 0 ? '+' : '') + measurement.neck_offset.toFixed(2)}</td></tr>
          <tr><td>Forward Head</td><td>{Math.round(measurement.forward_head_indicator * 100)}%</td></tr>
          <tr><td>Gaze Angle</td><td>{measurement.gaze_vertical_degrees.toFixed(1)}°</td></tr>
        </tbody>
      </table>
      <p className="metric-note">Personal posture tracking uses head + shoulders only.</p>
    </div>
  )
}
