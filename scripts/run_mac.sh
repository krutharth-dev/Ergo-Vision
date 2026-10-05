#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

# GUI-launched shells often have a minimal PATH on macOS.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if [ -f "$ROOT/.env" ]; then
  set -a
  source "$ROOT/.env"
  set +a
fi

PORT="${PORT:-8000}"
URL="http://127.0.0.1:$PORT"
HEALTH="$URL/health"
SERVER_PID=""

if [ ! -x "$VENV/bin/python" ]; then
  echo "ErgoVision is not set up yet. Run: bash scripts/setup_mac.sh"
  exit 1
fi

health_ok() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "$HEALTH" >/dev/null 2>&1
  else
    "$VENV/bin/python" - "$HEALTH" <<'PY' >/dev/null 2>&1
import sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=2) as r:
    raise SystemExit(0 if r.status == 200 else 1)
PY
  fi
}

if health_ok; then
  echo "ErgoVision is already running at $URL"
  if [ "${ERGOVISION_NO_AUTO_OPEN:-0}" != "1" ]; then open "$URL" >/dev/null 2>&1 || true; fi
  exit 0
fi

if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is already in use by another process."
  echo "Inspect it with: lsof -nP -iTCP:$PORT -sTCP:LISTEN"
  echo "Or run ErgoVision on another port: PORT=8001 bash scripts/run_mac.sh"
  exit 1
fi

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill -TERM "$SERVER_PID" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      kill -0 "$SERVER_PID" >/dev/null 2>&1 || break
      sleep 0.1
    done
    kill -KILL "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

on_signal() {
  cleanup
  exit 130
}

trap on_signal INT TERM HUP
trap cleanup EXIT

cd "$ROOT/backend"
"$VENV/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

echo "Starting ErgoVision..."
READY=0
for _ in $(seq 1 120); do
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    break
  fi
  if health_ok; then
    READY=1
    break
  fi
  sleep 0.5
done

if [ "$READY" -ne 1 ]; then
  echo "ErgoVision backend failed to become ready."
  echo "Run diagnostics: bash scripts/doctor_mac.sh"
  exit 1
fi

echo "ErgoVision is ready at $URL"
if [ "${ERGOVISION_NO_AUTO_OPEN:-0}" != "1" ]; then
  open "$URL" >/dev/null 2>&1 || true
fi

set +e
wait "$SERVER_PID"
STATUS=$?
set -e
SERVER_PID=""
trap - EXIT INT TERM HUP
exit "$STATUS"
