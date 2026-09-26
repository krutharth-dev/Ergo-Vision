import { useEffect, useState } from 'react'
import CalibrationPanel from './components/CalibrationPanel'
import CameraFeed from './components/CameraFeed'
import CorrectionOverlay from './components/CorrectionOverlay'
import ExposurePanel from './components/ExposurePanel'
import Feedback from './components/Feedback'
import Metrics from './components/Metrics'
import OcularPanel from './components/OcularPanel'
import PostureScore from './components/PostureScore'
import ReminderPanel from './components/ReminderPanel'
import SessionHistory from './components/SessionHistory'
import SessionPanel from './components/SessionPanel'
import SetupGuide from './components/SetupGuide'
import SignalReadiness from './components/SignalReadiness'
import TrendChart from './components/TrendChart'
import { usePostureSocket } from './hooks/usePostureSocket'
import { api } from './services/api'
import type { AppConfig, HealthStatus } from './types'
import './hackathon.css'

export default function App() {
  const { posture, connected } = usePostureSocket()
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [backendReachable, setBackendReachable] = useState(true)

  useEffect(() => {
    let disposed = false
    const load = async () => {
      try {
        const [cfg, currentHealth] = await Promise.all([api.config(), api.health()])
        if (!disposed) {
          setConfig(cfg)
          setHealth(currentHealth)
          setBackendReachable(true)
        }
      } catch {
        if (!disposed) setBackendReachable(false)
      }
    }
    load()
    const id = setInterval(load, 5000)
    return () => {
      disposed = true
      clearInterval(id)
    }
  }, [])

  const setupProblem =
    health &&
    !health.demo_mode &&
    (!health.camera_available || !health.model_loaded)

  return (
    <div className="app">
      <header className="header hackathon-header">
        <div>
          <h1 className="title">ErgoVision</h1>
          <p className="subtitle">Personalized · confidence-aware · temporal screen ergonomics</p>
        </div>
        <div className="header-badges">
          <span className="badge local">LOCAL AI</span>
          {health?.demo_mode && <span className="badge demo">DEMO</span>}
          {connected ? <span className="badge live">LIVE</span> : <span className="badge offline">OFFLINE</span>}
        </div>
      </header>

      {!backendReachable && (
        <div className="system-banner error">The ErgoVision backend is not reachable. Start the local server and refresh this page.</div>
      )}

      {setupProblem && (
        <div className="system-banner warning">
          {!health.camera_available && <span>Camera unavailable. </span>}
          {!health.model_loaded && <span>MediaPipe models unavailable. </span>}
          Check camera permissions and the local setup.
        </div>
      )}

      <main className="grid">
        <section className="grid-main">
          <PostureScore posture={posture} connected={connected} />
          <SignalReadiness posture={posture} />
          <div className="insight-pair">
            <ExposurePanel posture={posture} />
            <OcularPanel posture={posture} />
          </div>
          <CameraFeed />
          <TrendChart posture={posture} />
          <Feedback posture={posture} />
        </section>

        <aside className="grid-side">
          <SetupGuide posture={posture} />
          <CalibrationPanel posture={posture} />
          <Metrics posture={posture} config={config} />
          <SessionPanel />
          <ReminderPanel />
          <SessionHistory />
          <div className="card privacy-card">
            <div className="card-title">Privacy by design</div>
            <p>Inference runs on this computer. Raw camera footage is not uploaded or persistently recorded. Calibration and summaries stay local.</p>
          </div>
        </aside>
      </main>

      <footer className="footer">
        <span>ErgoVision · personalized temporal ergonomic coaching</span>
        <span className="muted">Ergonomic guidance only · not a medical device</span>
      </footer>

      <CorrectionOverlay posture={posture} />
    </div>
  )
}
