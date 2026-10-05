#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
MODELS="$ROOT/backend/app/models"
FRONTEND_DIST="$ROOT/frontend/dist/index.html"

# Finder/app launches and some shells omit Homebrew paths.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

PYTHON=""
for candidate in python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] in ((3, 11), (3, 12)) else 1)
PY
    then
      PYTHON="$(command -v "$candidate")"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "ErgoVision requires Python 3.11 or 3.12."
  echo "Install one of those versions, then run this script again."
  echo "Python 3.13 is not used because the pinned computer-vision stack is not validated on it."
  exit 1
fi

echo "Using $($PYTHON --version 2>&1) at $PYTHON"

if [ ! -f "$FRONTEND_DIST" ]; then
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "The frontend is not built and Node.js/npm were not found."
    echo "Install Node.js 18 or newer, reopen Terminal, then rerun setup."
    echo "Checked common Homebrew locations: /opt/homebrew/bin and /usr/local/bin."
    exit 1
  fi
fi

if [ ! -x "$VENV/bin/python" ]; then
  rm -rf "$VENV"
  "$PYTHON" -m venv "$VENV"
fi

VENV_PY="$VENV/bin/python"
VENV_VERSION="$($VENV_PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$VENV_VERSION" != "3.11" ] && [ "$VENV_VERSION" != "3.12" ]; then
  echo "Existing virtual environment uses Python $VENV_VERSION; rebuilding it with a supported Python."
  rm -rf "$VENV"
  "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$ROOT/backend/requirements-dev.txt"

if [ ! -f "$FRONTEND_DIST" ]; then
  (
    cd "$ROOT/frontend"
    npm ci
    npm run build
  )
else
  echo "Using bundled frontend production build."
fi

mkdir -p "$MODELS"
if ! (
  cd "$ROOT/backend"
  "$VENV/bin/python" -m app.vision.models
); then
  if ! command -v curl >/dev/null 2>&1; then
    echo "Model download failed and curl is unavailable. See docs/TROUBLESHOOTING.md."
    exit 1
  fi

  echo "Python model download failed; retrying with curl..."
  curl -L --fail --retry 3     "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"     -o "$MODELS/face_landmarker.task"
  curl -L --fail --retry 3     "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"     -o "$MODELS/pose_landmarker_lite.task"
fi

for model in face_landmarker.task pose_landmarker_lite.task; do
  if [ ! -s "$MODELS/$model" ]; then
    echo "Missing MediaPipe model: $MODELS/$model"
    exit 1
  fi
done

echo
echo "ErgoVision setup is complete."
echo "Run diagnostics: bash scripts/doctor_mac.sh"
echo "Start ErgoVision: bash scripts/run_mac.sh"
