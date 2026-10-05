#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
MODELS="$ROOT/backend/app/models"
FAILED=0

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

pass() { printf "✓ %s\n" "$1"; }
warn() { printf "! %s\n" "$1"; }
fail() { printf "✗ %s\n" "$1"; FAILED=1; }

printf "ErgoVision macOS doctor\n\n"

if command -v python3.12 >/dev/null 2>&1; then
  pass "python3.12: $(python3.12 --version 2>&1)"
elif command -v python3.11 >/dev/null 2>&1; then
  pass "python3.11: $(python3.11 --version 2>&1)"
elif command -v python3 >/dev/null 2>&1; then
  ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
  if [ "$ver" = "3.11" ] || [ "$ver" = "3.12" ]; then pass "python3: $(python3 --version 2>&1)"; else fail "Python $ver found; ErgoVision needs 3.11 or 3.12"; fi
else
  fail "Python 3.11/3.12 not found"
fi

if [ -f "$ROOT/frontend/dist/index.html" ]; then
  pass "frontend production build exists (Node.js not required to run)"
else
  if command -v node >/dev/null 2>&1; then pass "node: $(node --version)"; else fail "Node.js not found and frontend build is missing"; fi
  if command -v npm >/dev/null 2>&1; then pass "npm: $(npm --version)"; else fail "npm not found and frontend build is missing"; fi
fi

if [ -x "$VENV/bin/python" ]; then
  pass "virtual environment exists: $($VENV/bin/python --version 2>&1)"
  if "$VENV/bin/python" - <<'PY' >/dev/null 2>&1
import cv2, fastapi, mediapipe, numpy, uvicorn
PY
  then
    pass "Python runtime imports succeeded"
  else
    fail "Python runtime imports failed; rerun scripts/setup_mac.sh"
  fi
else
  fail "virtual environment missing; run scripts/setup_mac.sh"
fi

for model in face_landmarker.task pose_landmarker_lite.task; do
  if [ -s "$MODELS/$model" ]; then
    size=$(wc -c < "$MODELS/$model" | tr -d ' ')
    pass "$model present (${size} bytes)"
  else
    fail "$model missing or empty"
  fi
done

PORT="${PORT:-8000}"
if command -v curl >/dev/null 2>&1 && curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  pass "ErgoVision is already healthy on port $PORT"
elif command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  warn "port $PORT is in use by another process"
else
  pass "port $PORT is available"
fi

printf "\n"
if [ "$FAILED" -eq 0 ]; then echo "Environment looks ready."; else echo "One or more checks failed. See docs/TROUBLESHOOTING.md."; fi
exit "$FAILED"
