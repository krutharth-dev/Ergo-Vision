import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { CalibrationProfile, PostureEvent } from '../types'

interface Props {
  posture: PostureEvent | null
}

export default function CalibrationPanel({ posture }: Props) {
  const [profile, setProfile] = useState<CalibrationProfile | null>(null)
  const [busy, setBusy] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    api.calibration().then(setProfile).catch(() => setError('Calibration service unavailable'))
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current)
    }
  }, [])

  const ready =
    Boolean(posture?.person_detected) &&
    Boolean(posture?.tracking.reliable) &&
    Boolean(posture?.tracking.hips_visible)

  const capture = async () => {
    setBusy(true)
    setError('')
    setMessage('')
    setSecondsLeft(5)

    if (timerRef.current !== null) window.clearInterval(timerRef.current)
    timerRef.current = window.setInterval(() => {
      setSecondsLeft((current) => Math.max(0, current - 1))
    }, 1000)

    try {
      const result = await api.captureCalibration()
      setProfile(result)
      setMessage(`Calibration saved successfully from ${result.samples} reliable frames.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not calibrate')
    } finally {
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current)
        timerRef.current = null
      }
      setSecondsLeft(0)
      setBusy(false)
    }
  }

  const clear = async () => {
    setBusy(true)
    setError('')
    setMessage('')
    try {
      setProfile(await api.clearCalibration())
      setMessage('Calibration reset.')
    } catch {
      setError('Could not reset calibration')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card calibration-card">
      <div className="card-title-row">
        <div className="card-title">Personal Calibration</div>
        <span className={`session-state ${profile?.calibrated ? 'active' : 'paused'}`}>
          {profile?.calibrated ? 'CALIBRATED' : 'DEFAULT'}
        </span>
      </div>

      <p className="muted calibration-copy">
        Press calibrate, then hold your normal comfortable upright posture for the full 5 seconds. FAIR
        or EXCELLENT tracking is accepted. A slight natural shoulder imbalance is completely okay — it
        becomes part of your personal baseline instead of being treated as bad posture.
      </p>

      {!ready && (
        <p className="calibration-meta">
          Move back until your hips are visible and tracking is reliable. Your posture can be GOOD or
          slightly imbalanced; symmetry is not required for calibration.
        </p>
      )}

      {busy && (
        <div className="reminder-status">
          <span>Recording upright posture</span>
          <strong>{secondsLeft}s</strong>
        </div>
      )}

      <div className="calibration-actions">
        <button className="button primary" disabled={busy || !ready} onClick={capture}>
          {busy ? `Recording… ${secondsLeft}s` : 'Calibrate for 5 seconds'}
        </button>
        {profile?.calibrated && (
          <button className="button" disabled={busy} onClick={clear}>
            Reset
          </button>
        )}
      </div>

      {profile?.calibrated && profile.captured_at && (
        <p className="calibration-meta">
          Saved locally · {new Date(profile.captured_at).toLocaleString()} · {profile.samples} samples · natural shoulder baseline {profile.shoulder_alignment_degrees.toFixed(1)}°
        </p>
      )}

      {message && <p className="calibration-meta">{message}</p>}
      {error && <p className="inline-error">{error}</p>}
    </div>
  )
}
