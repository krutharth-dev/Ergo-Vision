# Architecture

## Overview

ErgoVision is a local-first application. A Python process owns the webcam, performs computer-vision inference, computes ergonomic indicators and exposes live state to a React dashboard through FastAPI.

```text
React dashboard
  ↓ REST / WebSocket / MJPEG
FastAPI application
  ↓ cached pipeline state
PosturePipeline
  ↓
OpenCV + MediaPipe Tasks
```

## Core design decisions

### Single camera owner

`PosturePipeline` is the only continuous webcam consumer. It processes each captured frame and caches the most recent annotated JPEG. The MJPEG route reads this cache instead of calling the camera independently.

This avoids frame starvation, inconsistent FPS and multiple OpenCV consumers competing for the same device.

### Separate ergonomic math

Geometry, measurements, smoothing, classification, scoring, temporal exposure, ocular analysis and intervention state are independent of FastAPI. That keeps the calculations unit-testable and allows the transport layer to evolve without rewriting the ergonomic model.

### Readiness before interpretation

The pipeline exposes whether the required tracking and baselines are ready. Personal posture calibration, exposure baseline readiness and ocular warm-up are separate states from the final ergonomic outputs. LOW_CONFIDENCE does not accumulate exposure or verify an intervention.

### Local-first data flow

The current deployment model intentionally runs both the camera pipeline and API on the user's computer. Raw frames are not sent to a remote inference service and are not persisted by ErgoVision.

### Local session state

Backend session timing and posture aggregates are kept in memory and clear when the backend exits. The dashboard may retain completed summary rows in browser local storage; raw video is not part of that history.

## Backend modules

| Module | Responsibility |
|---|---|
| `app/main.py` | application lifecycle, MJPEG stream and built frontend serving |
| `app/config.py` | environment and ergonomic thresholds |
| `app/pipeline.py` | single-owner real-time processing pipeline |
| `app/vision/camera.py` | OpenCV capture and FPS management |
| `app/vision/detector.py` | MediaPipe face/pose inference and overlays |
| `app/vision/landmarks.py` | semantic landmark abstraction |
| `app/vision/models.py` | MediaPipe model provisioning |
| `app/ergonomics/geometry.py` | pure geometry helpers |
| `app/ergonomics/measurements.py` | ergonomic indicators from landmarks |
| `app/ergonomics/smoothing.py` | temporal smoothing |
| `app/ergonomics/classifier.py` | GOOD/WARNING/BAD temporal classification |
| `app/ergonomics/scoring.py` | weighted 0–100 score |
| `app/ergonomics/feedback.py` | human-readable posture feedback |
| `app/ergonomics/exposure.py` | confidence-weighted temporal exposure and session drift |
| `app/ergonomics/ocular.py` | personalized EAR, blink and visual ergonomic indicators |
| `app/ergonomics/intervention.py` | closed-loop correction and verified recovery state |
| `app/session/tracker.py` | thread-safe session statistics |
| `app/api/routes.py` | REST endpoints |
| `app/api/websocket.py` | live posture WebSocket |
| `app/api/schemas.py` | Pydantic API contracts |

## Frontend

The frontend uses React, TypeScript and Vite. Development traffic is proxied to the local FastAPI server. For normal local use, `npm run build` produces `frontend/dist`, which FastAPI serves directly so only one local process is required.

## MediaPipe models

The official `.task` model bundles are not committed to Git. `app.vision.models` provisions them into `backend/app/models`. The downloader uses the `certifi` certificate bundle to avoid relying on a broken or incomplete local Python certificate chain.

## Failure handling

- Missing camera: backend remains available and reports camera state through `/health`.
- Missing models: automatic provisioning is attempted unless disabled.
- Missing landmarks: ergonomic calculations degrade gracefully rather than raising.
- Lost WebSocket: frontend reconnects with bounded backoff.
- Port collision: the macOS launcher exits with a clear diagnostic.
- Ctrl+Z / suspended launcher: the launcher traps the signal and releases the child backend process.

## Deployment boundary

The current architecture should not be deployed unchanged to a remote server for public browser users. A remote Python process would look for a webcam on the server, not on the visitor's device.

A hosted version should move camera capture into the browser and explicitly redesign where inference occurs.
