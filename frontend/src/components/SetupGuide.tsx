import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { CameraDevice, PostureEvent } from '../types'

interface Props { posture: PostureEvent | null }

export default function SetupGuide({ posture }: Props) {
  const [devices, setDevices] = useState<CameraDevice[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async () => { try { setDevices(await api.cameraDevices()); setError('') } catch { setError('Could not scan cameras') } }
  useEffect(() => { load() }, [])
  const tracking = posture?.tracking
  const current = devices.find((device) => device.current)?.index ?? 0
  const select = async (index: number) => { setBusy(true); try { await api.selectCamera(index); await load() } catch (e) { setError(e instanceof Error ? e.message : 'Could not switch camera') } finally { setBusy(false) } }
  return <div className="card setup-card">
    <div className="card-title-row"><div className="card-title">Camera Setup</div><span className={`tracking-badge ${tracking?.quality?.toLowerCase() ?? 'poor'}`}>{tracking?.quality ?? 'WAITING'}</span></div>
    <div className="tracking-meter"><div className="tracking-meter-fill" style={{ width: `${Math.round((tracking?.confidence ?? 0) * 100)}%` }} /></div>
    <p className="setup-confidence">Tracking confidence {Math.round((tracking?.confidence ?? 0) * 100)}%</p>
    <div className="setup-checks"><span className={tracking?.head_visible ? 'ready' : ''}>{tracking?.head_visible ? '✓' : '○'} Head</span><span className={tracking?.shoulders_visible ? 'ready' : ''}>{tracking?.shoulders_visible ? '✓' : '○'} Shoulders</span></div>
    {tracking?.guidance?.length ? <ul className="setup-guidance">{tracking.guidance.slice(0, 3).map((message) => <li key={message}>{message}</li>)}</ul> : <p className="setup-good">✓ Framing looks good.</p>}
    <label className="camera-select-label">Camera<select value={current} disabled={busy || devices.length === 0} onChange={(e) => select(Number(e.target.value))}>{devices.map((device) => <option key={device.index} value={device.index}>{device.label}</option>)}</select></label>
    <button className="text-button camera-rescan" disabled={busy} onClick={load}>Rescan cameras</button>
    {error && <p className="inline-error">{error}</p>}
    <p className="setup-note">Head + shoulders only. Changing camera clears calibration because camera geometry changes.</p>
  </div>
}
