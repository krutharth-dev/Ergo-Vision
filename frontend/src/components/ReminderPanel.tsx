import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { PostureEvent, ReminderSettings } from '../types'

interface Props {
  posture: PostureEvent | null
}

const POOR_POSTURE_OPTIONS = [
  { seconds: 10, label: '10 sec' },
  { seconds: 20, label: '20 sec' },
  { seconds: 30, label: '30 sec' },
  { seconds: 60, label: '1 min' },
  { seconds: 120, label: '2 min' },
  { seconds: 180, label: '3 min' },
  { seconds: 300, label: '5 min' },
  { seconds: 600, label: '10 min' },
  { seconds: 900, label: '15 min' },
  { seconds: 1200, label: '20 min' },
  { seconds: 1500, label: '25 min' },
  { seconds: 1800, label: '30 min' },
]

const BREAK_OPTIONS = [1, 2, 3, 5, 10, 15, 20, 25, 30]

const DEFAULTS: ReminderSettings = {
  enabled: false,
  poor_posture_seconds: 10,
  movement_break_minutes: 5,
  background_monitoring: false,
  last_reminder: '',
}

export default function ReminderPanel({ posture }: Props) {
  const [settings, setSettings] = useState<ReminderSettings>(DEFAULTS)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let disposed = false

    const refresh = async () => {
      try {
        const current = await api.reminders()
        if (!disposed) {
          setSettings(current)
          setError('')
        }
      } catch {
        if (!disposed) setError('Background reminder service is unavailable.')
      }
    }

    refresh()
    const timer = window.setInterval(refresh, 5000)
    return () => {
      disposed = true
      window.clearInterval(timer)
    }
  }, [])

  const save = async (
    patch: Partial<Pick<ReminderSettings, 'enabled' | 'poor_posture_seconds' | 'movement_break_minutes'>>,
  ) => {
    setBusy(true)
    setError('')
    const next = { ...settings, ...patch }

    try {
      const saved = await api.setReminders({
        enabled: next.enabled,
        poor_posture_seconds: next.poor_posture_seconds,
        movement_break_minutes: next.movement_break_minutes,
      })
      setSettings(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update reminders.')
    } finally {
      setBusy(false)
    }
  }

  const currentPosture =
    posture?.status === 'BAD'
      ? 'Poor posture'
      : posture?.status === 'WARNING'
        ? 'Posture warning'
        : posture?.status === 'GOOD'
          ? 'Upright'
          : 'Waiting'

  return (
    <div className="card reminder-card">
      <div className="card-title-row">
        <div className="card-title">Smart Reminders</div>
        <span className={`session-state ${settings.enabled ? 'active' : 'paused'}`}>
          {settings.enabled ? 'BACKGROUND ON' : 'OFF'}
        </span>
      </div>

      <p className="reminder-copy">
        Choose how long poor posture must persist before ErgoVision sends a native macOS notification.
        If you stay in poor posture, it repeats after the same selected interval.
      </p>

      <div className="setting-grid">
        <label>
          <span>Poor-posture notification</span>
          <select
            value={settings.poor_posture_seconds}
            disabled={busy}
            onChange={(event) => save({ poor_posture_seconds: Number(event.target.value) })}
          >
            {POOR_POSTURE_OPTIONS.map((option) => (
              <option key={option.seconds} value={option.seconds}>
                After {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Movement break</span>
          <select
            value={settings.movement_break_minutes}
            disabled={busy}
            onChange={(event) => save({ movement_break_minutes: Number(event.target.value) })}
          >
            {BREAK_OPTIONS.map((minutes) => (
              <option key={minutes} value={minutes}>
                Every {minutes} min
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="reminder-status">
        <span>Current posture</span>
        <strong>{currentPosture}</strong>
      </div>

      <div className="reminder-status">
        <span>Background monitoring</span>
        <strong>{settings.background_monitoring ? 'Active' : 'Paused'}</strong>
      </div>

      <div className="reminder-actions">
        <button
          className="button primary"
          disabled={busy}
          onClick={() => save({ enabled: !settings.enabled })}
        >
          {busy ? 'Updating…' : settings.enabled ? 'Stop background reminders' : 'Enable background reminders'}
        </button>
      </div>

      <p className="calibration-meta">
        When enabled, the Python backend keeps posture monitoring active even if this dashboard tab is
        minimized or closed. It stops when you disable reminders or stop ErgoVision.
      </p>

      {settings.last_reminder && (
        <p className="reminder-last-alert">Last alert: {settings.last_reminder}</p>
      )}
      {error && <p className="inline-error">{error}</p>}
    </div>
  )
}
