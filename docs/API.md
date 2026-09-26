# API Reference

Base URL for local use: `http://127.0.0.1:8000`

Interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`

## Health

### `GET /health`

Returns backend health, camera/model state, demo mode, uptime and capture FPS.

## Current posture

### `GET /api/posture/current`

Returns the ErgoVision Index, posture status, measurements, tracking confidence, personal-calibration state, ocular indicators, temporal exposure, intervention state, feedback, timestamp and person-detection state.

Measurements include head tilt, shoulder alignment, neck offset, forward-head indicator, gaze, torso lean, torso geometry and the calibrated slouch indicator.

Readiness metadata includes:
- `posture_calibrated`
- exposure `baseline_ready`, observed baseline seconds and required baseline seconds
- ocular baseline observation/requirement fields and `blink_ready`

Status values are `GOOD`, `WARNING`, `BAD`, `NO_PERSON` and `LOW_CONFIDENCE`. LOW_CONFIDENCE means current landmark quality is not reliable enough for ergonomic scoring.

## Calibration

### `GET /api/calibration`

Returns the current local calibration profile.

### `POST /api/calibration/capture`

Captures a neutral baseline from recent valid posture samples. The user should sit upright for 2–3 seconds before calling this endpoint. Returns `409` when there are not enough valid samples yet.

### `DELETE /api/calibration`

Clears the saved calibration profile and returns to default heuristics.

## Session

### `GET /api/session/stats`

Returns duration by posture state, percentages, counts, average/current score, longest poor-posture interval, prototype exposure state, blink rate, intervention outcomes and whether session accounting is active.

### `POST /api/session/start`

Resumes session accounting.

### `POST /api/session/stop`

Pauses session accounting.

### `POST /api/session/reset`

Clears session statistics and starts a fresh session.

The browser dashboard archives completed session summaries in local browser storage before reset. No images are stored.

## Configuration

### `GET /api/config`

Returns runtime ergonomic and capture configuration, including torso/slouch thresholds.

## Camera stream

### `GET /api/stream`

Returns an MJPEG stream of the most recent annotated frame.

### `GET /api/stream/frame`

Returns the latest annotated JPEG frame with `Cache-Control: no-store`.

## WebSocket

### `WS /ws/posture`

Streams the same posture event shape returned by `/api/posture/current`. The frontend automatically reconnects after temporary disconnects.

## Errors

FastAPI errors use the standard shape:

```json
{
  "detail": "Pipeline not initialized"
}
```

Typical status codes are `200`, `404`, `409` and `503`.
