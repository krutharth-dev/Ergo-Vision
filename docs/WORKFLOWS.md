# ErgoVision workflows and visual guide

This guide explains the application's **actual data flow**, its privacy boundary, and practical setup and validation paths. Mermaid diagrams render directly on GitHub.

## 1. Runtime architecture

```mermaid
flowchart TD
  CAM["Webcam (or demo data)"] --> CAP["Single-owner OpenCV capture"]
  CAP --> MP["MediaPipe Face + Pose landmarks"]
  MP --> GATE{"Enough visible, confident landmarks?"}
  GATE -- No --> UNK["Tracking / framing guidance\n(no false GOOD classification)"]
  GATE -- Yes --> MET["Posture geometry + neutral calibration"]
  MET --> CLASS["Smoothing + ergonomic classification\nGOOD / WARNING / BAD"]
  CLASS --> PIPE["Shared posture pipeline"]
  PIPE --> WS["FastAPI REST / WebSocket"]
  PIPE --> MJ["Cached annotated MJPEG"]
  PIPE --> SESSION["In-memory session summaries"]
  WS --> UI["Local React dashboard"]
  MJ --> UI
  SESSION --> UI
  UNK --> UI
```

The backend owns the camera; streaming and other consumers access its cached results rather than competing to capture frames. Classifications are ergonomic indicators, **not medical diagnoses**.

## 2. Camera and privacy lifecycle

```mermaid
sequenceDiagram
    actor User
    participant Browser as Local browser
    participant API as FastAPI
    participant Camera as Webcam/pipeline
    User->>Browser: Open dashboard
    Browser->>API: Connect
    API->>Camera: Start on first dashboard connection
    Camera-->>API: Landmarks + derived state
    API-->>Browser: Live stream and events
    User->>Browser: Close last dashboard tab
    Browser--xAPI: Disconnect
    API->>Camera: Release webcam
```

Posture processing runs on the host computer. The app does not persist raw webcam footage. Neutral-posture measurements may be stored locally at `~/.ergovision/calibration.json`; browser session summaries may also be retained locally. See [privacy details](PRIVACY.md).

## 3. Installation decision flow

```mermaid
flowchart TD
  START["Choose operating system"] --> OS{"macOS or Windows?"}
  OS -- macOS --> MAC["Use GitHub Release ZIP\nor source setup_mac.sh"]
  OS -- Windows --> WIN["Install Python 3.11/3.12\nthen use release ZIP or Windows setup script"]
  MAC --> PERM["Grant camera permission"]
  WIN --> PERM
  PERM --> CHECK{"Webcam available?"}
  CHECK -- Yes --> LIVE["Run local dashboard and calibrate"]
  CHECK -- No --> DEMO["Run DEMO_MODE=1 for interface tests"]
```

For platform-specific commands use [Installation](INSTALLATION.md), [Windows](WINDOWS.md) and [macOS launcher](MAC_APP.md). **Only install software from sources you trust** and review installation scripts before executing them.

## 4. Contributor validation workflow

```mermaid
flowchart LR
  CHANGE["Code/documentation change"] --> LOCAL["Local checks"]
  LOCAL --> PR["Open pull request"]
  PR --> CI["GitHub Actions"]
  CI --> BE["Backend pytest: Linux + Windows"]
  CI --> FE["Frontend TypeScript/Vite build: Linux + Windows"]
  BE --> REVIEW["Review results and merge"]
  FE --> REVIEW
  REVIEW --> TAG["Optional v* release tag"]
  TAG --> RELEASE["macOS/Windows release bundles"]
```

Run locally before proposing changes:

```bash
bash scripts/check.sh
```

For individual tasks:

```bash
cd backend
python -m pytest tests/ -v
```

```bash
cd frontend
npm ci
npm run build
```

The CI workflow is in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Release packaging is in [`.github/workflows/release.yml`](../.github/workflows/release.yml).

## 5. Demo walkthrough

1. Start in `DEMO_MODE=1` to confirm API/dashboard integration without hardware.
2. Launch with the webcam, confirm browser/OS camera permission, and frame head and shoulders (ideally hips).
3. Calibrate from a neutral upright position and verify the GOOD/WARNING/BAD state changes with posture.
4. Move partly out of frame; verify tracking guidance rather than an undeserved GOOD state.
5. Pause/resume and observe the live trend and session counts.
6. Close every dashboard tab; verify camera release.
7. Report any glitches with OS, Python version, browser, log excerpts, and reproduction steps **without sharing identifiable webcam frames**.

## 6. Known scope boundaries

- Front-facing 2D webcam measurements approximate ergonomic indicators; they do not measure spinal curvature.
- Scores and warning thresholds are not clinically validated diagnostic results.
- Real-time performance depends on computer speed, lighting, camera framing and model availability.
- Desktop notifications require browser permission; demo mode uses simulated data.
- Cross-platform installers and release artifacts should be validated before publishing a tagged release.
