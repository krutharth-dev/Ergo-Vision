import type { PostureEvent } from '../types'

interface Props {
  posture: PostureEvent | null
}

function percent(value: number, total: number): number {
  if (total <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((value / total) * 100)))
}

export default function SignalReadiness({ posture }: Props) {
  const tracking = posture?.tracking
  const exposure = posture?.exposure
  const ocular = posture?.ocular

  const trackingReady = Boolean(tracking?.reliable)
  const postureReady = Boolean(posture?.posture_calibrated)
  const exposureReady = Boolean(exposure?.baseline_ready)
  const ocularReady = Boolean(ocular?.calibrated)
  const blinkReady = Boolean(ocular?.blink_ready)

  const exposureProgress = exposure
    ? percent(
        exposure.baseline_observation_seconds,
        exposure.baseline_required_seconds,
      )
    : 0

  const ocularProgress = ocular
    ? percent(
        ocular.baseline_observation_seconds,
        ocular.baseline_required_seconds,
      )
    : 0

  return (
    <div className="card readiness-card">
      <div className="card-title-row">
        <div>
          <div className="card-title">Signal Readiness</div>
          <p className="readiness-intro">
            ErgoVision separates signal quality, personal baselines and
            ergonomic interpretation.
          </p>
        </div>
        <span className="evidence-pill">PROTOTYPE EVIDENCE</span>
      </div>

      <div className="readiness-grid">
        <div className={'readiness-item ' + (trackingReady ? 'ready' : 'waiting')}>
          <div className="readiness-heading">
            <span>Tracking</span>
            <strong>{trackingReady ? 'READY' : 'REPOSITION'}</strong>
          </div>
          <div
            className="readiness-progress"
            role="progressbar"
            aria-label="Tracking confidence"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round((tracking?.confidence ?? 0) * 100)}
          >
            <span style={{ width: String(Math.round((tracking?.confidence ?? 0) * 100)) + '%' }} />
          </div>
          <p>
            {Math.round((tracking?.confidence ?? 0) * 100)}% confidence ·{' '}
            {tracking?.quality ?? 'WAITING'}
          </p>
        </div>

        <div className={'readiness-item ' + (postureReady ? 'ready' : 'waiting')}>
          <div className="readiness-heading">
            <span>Personal posture</span>
            <strong>{postureReady ? 'CALIBRATED' : 'DEFAULT'}</strong>
          </div>
          <div
            className="readiness-progress"
            role="progressbar"
            aria-label="Personal posture calibration"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={postureReady ? 100 : 0}
          >
            <span style={{ width: postureReady ? '100%' : '0%' }} />
          </div>
          <p>
            {postureReady
              ? 'Slouch and proximity signals use your neutral posture.'
              : 'Calibrate upright posture before interpreting personal drift.'}
          </p>
        </div>

        <div className={'readiness-item ' + (exposureReady ? 'ready' : 'waiting')}>
          <div className="readiness-heading">
            <span>Exposure baseline</span>
            <strong>{exposureReady ? 'READY' : 'BASELINING'}</strong>
          </div>
          <div
            className="readiness-progress"
            role="progressbar"
            aria-label="Exposure baseline progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={exposureProgress}
          >
            <span style={{ width: String(exposureProgress) + '%' }} />
          </div>
          <p>
            {exposureReady
              ? 'Drift can now be interpreted relative to this session.'
              : (exposure?.baseline_observation_seconds ?? 0).toFixed(1) +
                ' / ' +
                (exposure?.baseline_required_seconds ?? 10).toFixed(0) +
                ' s reliable posture'}
          </p>
        </div>

        <div className={'readiness-item ' + (ocularReady ? 'ready' : 'waiting')}>
          <div className="readiness-heading">
            <span>Visual signal</span>
            <strong>
              {blinkReady ? 'READY' : ocularReady ? 'WARMING' : 'CALIBRATING'}
            </strong>
          </div>
          <div
            className="readiness-progress"
            role="progressbar"
            aria-label="Eye baseline progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={ocularReady ? 100 : ocularProgress}
          >
            <span style={{ width: String(ocularReady ? 100 : ocularProgress) + '%' }} />
          </div>
          <p>
            {blinkReady
              ? 'Personal eye baseline and blink observation window are ready.'
              : ocularReady
                ? 'Eye baseline ready; collecting a longer blink window.'
                : (ocular?.baseline_observation_seconds ?? 0).toFixed(1) +
                  ' / ' +
                  (ocular?.baseline_required_seconds ?? 2).toFixed(0) +
                  ' s valid eye tracking'}
          </p>
        </div>
      </div>

      <p className="readiness-note">
        LOW_CONFIDENCE pauses exposure accumulation and cannot verify a posture
        correction. These outputs are ergonomic indicators, not clinical
        measurements.
      </p>
    </div>
  )
}
