import type { PostureEvent } from '../types'

interface Props { posture: PostureEvent | null }

function pct(value: number) {
  const sign = value > 0 ? '+' : ''
  return sign + Math.round(value * 100) + '%'
}

export default function ExposurePanel({ posture }: Props) {
  const exposure = posture?.exposure
  if (!exposure) {
    return (
      <div className="card insight-card">
        <div className="card-title">Ergonomic Exposure</div>
        <p className="muted">Waiting for exposure data…</p>
      </div>
    )
  }

  return (
    <div className="card insight-card">
      <div className="card-title-row">
        <div className="card-title">Ergonomic Exposure</div>
        <span className={'dose-pill dose-' + exposure.dose_level.toLowerCase()}>
          {exposure.dose_level}
        </span>
      </div>

      <div className="hero-metric">
        <strong>{exposure.cumulative_dose.toFixed(1)}</strong>
        <span>risk-seconds</span>
      </div>

      <div className="insight-grid-small">
        <div>
          <span>Current risk</span>
          <strong>{Math.round(exposure.instantaneous_risk * 100)}%</strong>
        </div>
        <div>
          <span>Continuous poor</span>
          <strong>{exposure.continuous_poor_seconds.toFixed(0)} s</strong>
        </div>
        <div>
          <span>Postural drift</span>
          <strong className={exposure.baseline_ready && exposure.postural_drift > 0.08 ? 'risk-text' : ''}>
            {exposure.baseline_ready ? pct(exposure.postural_drift) : 'Baselining'}
          </strong>
        </div>
        <div>
          <span>Confidence weighted</span>
          <strong>{Math.round(exposure.confidence_weighted_risk * 100)}%</strong>
        </div>
      </div>

      <div className={'signal-state ' + (exposure.baseline_ready ? 'ready' : 'warming')}>
        <span>{exposure.baseline_ready ? 'Baseline ready' : 'Building session baseline'}</span>
        <strong>
          {exposure.baseline_ready
            ? exposure.baseline_risk.toFixed(2) + ' baseline risk'
            : exposure.baseline_observation_seconds.toFixed(1) +
              ' / ' +
              exposure.baseline_required_seconds.toFixed(0) +
              ' s reliable data'}
        </strong>
      </div>

      <p className="panel-note">
        Prototype exposure indicator: risk accumulates with time and tracking
        confidence, then recovers during lower-risk posture. Drift is withheld
        until the session baseline is ready.
      </p>
    </div>
  )
}
