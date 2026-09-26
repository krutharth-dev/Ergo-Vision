import type { PostureEvent } from '../types'

interface Props { posture: PostureEvent | null }

export default function OcularPanel({ posture }: Props) {
  const ocular = posture?.ocular
  if (!ocular) {
    return (
      <div className="card insight-card">
        <div className="card-title">Visual Ergonomics</div>
        <p className="muted">Waiting for eye tracking…</p>
      </div>
    )
  }

  const baselineReady = ocular.calibrated
  const blinkReady = ocular.blink_ready

  return (
    <div className="card insight-card">
      <div className="card-title-row">
        <div className="card-title">Visual Ergonomics</div>
        <span className={'tracking-badge ' + (ocular.available ? 'excellent' : 'poor')}>
          {ocular.available ? Math.round(ocular.confidence * 100) + '%' : 'UNAVAILABLE'}
        </span>
      </div>

      <div className="insight-grid-small ocular-grid">
        <div>
          <span>Eye Aspect Ratio</span>
          <strong>{ocular.available ? ocular.ear.toFixed(3) : '—'}</strong>
        </div>
        <div>
          <span>Blink rate</span>
          <strong>{blinkReady ? ocular.blink_rate_per_min.toFixed(1) + '/min' : 'Warming up'}</strong>
        </div>
        <div>
          <span>Blinks observed</span>
          <strong>{ocular.blink_count}</strong>
        </div>
        <div>
          <span>Visual load</span>
          <strong>{blinkReady ? Math.round(ocular.visual_load * 100) + '%' : 'Warming up'}</strong>
        </div>
        <div>
          <span>Proximity drift</span>
          <strong>
            {baselineReady
              ? (ocular.proximity_drift >= 0 ? '+' : '') +
                Math.round(ocular.proximity_drift * 100) +
                '%'
              : 'Await baseline'}
          </strong>
        </div>
        <div>
          <span>Personal eye baseline</span>
          <strong>{baselineReady ? 'READY' : 'CALIBRATING'}</strong>
        </div>
      </div>

      <div className={'signal-state ' + (blinkReady ? 'ready' : 'warming')}>
        <span>
          {blinkReady
            ? 'Blink observation ready'
            : baselineReady
              ? 'Building blink observation window'
              : 'Collecting valid eye baseline'}
        </span>
        <strong>
          {baselineReady
            ? ocular.observation_seconds.toFixed(1) + ' s observed'
            : ocular.baseline_observation_seconds.toFixed(1) +
              ' / ' +
              ocular.baseline_required_seconds.toFixed(0) +
              ' s valid eye tracking'}
        </strong>
      </div>

      <p className="panel-note">
        EAR, blink and relative proximity are visual ergonomic indicators only.
        Visual load is withheld until the personalized eye baseline and warm-up
        window are ready; it is not a diagnosis of eye disease or CVS.
      </p>
    </div>
  )
}
