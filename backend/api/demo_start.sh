#!/usr/bin/env bash
# Pornește API (uvicorn) + tunel cloudflared și afișează linkul de demo.
# Folosire: demo_start.sh [--port N] [--restart] [--reset-model]
#   --restart      oprește și repornește uvicorn de pe port, apoi asigură tunelul
#   --reset-model  doar repornește uvicorn (model curat); tunelul rămâne
set -u
PORT=8000; RESTART=0; RESET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift;;
    --restart) RESTART=1;; --reset-model) RESET=1;;
    [0-9]*) PORT="$1";;
    *) echo "opțiune necunoscută: $1"; exit 1;;
  esac; shift
done
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP=/tmp/claude-1000; mkdir -p "$TMP"
if [ "$PORT" = 8000 ]; then SUF=""; else SUF="-$PORT"; fi
LOG_API="$TMP/uvicorn$SUF.log"; LOG_TUN="$TMP/cloudflared$SUF.log"; URLF="$TMP/tunnel$SUF.url"
LOVABLE="https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app/"

api_pid() { ss -ltnpH "sport = :$PORT" 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2; }
health() { curl -fsS -m 3 "http://127.0.0.1:$PORT/health" 2>/dev/null; }

PID="$(api_pid)"
if [ -n "$PID" ] && { [ $RESTART = 1 ] || [ $RESET = 1 ]; }; then
  kill "$PID"; for _ in $(seq 20); do [ -z "$(api_pid)" ] && break; sleep 0.3; done
  PID=""
fi
if [ -z "$PID" ]; then
  cd "$ROOT"
  setsid nohup "$ROOT/.venv/bin/uvicorn" backend.api.main:app --host 127.0.0.1 --port "$PORT" >"$LOG_API" 2>&1 &
  for _ in $(seq 40); do health >/dev/null && break; sleep 0.5; done
fi
health >/dev/null || { echo "API nu răspunde pe :$PORT, vezi $LOG_API"; exit 1; }
echo "API: $(health)"

if [ $RESET = 1 ] && [ -s "$URLF" ]; then
  echo "Model resetat; tunelul rămâne."
else
  if ! pgrep -f "cloudflared tunnel .*--url http://localhost:$PORT\$" >/dev/null; then
    setsid nohup "$HOME/.local/bin/cloudflared" tunnel --no-autoupdate --url "http://localhost:$PORT" >"$LOG_TUN" 2>&1 &
  fi
  URL=""
  for _ in $(seq 60); do
    URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_TUN" 2>/dev/null | head -1)"
    [ -n "$URL" ] && break; sleep 1
  done
  [ -n "$URL" ] || { echo "Nu am găsit URL-ul tunelului, vezi $LOG_TUN"; exit 1; }
  echo "$URL" > "$URLF"
fi
URL="$(cat "$URLF")"
echo "Tunel: $URL"
echo
echo "Link de deschis:  ${LOVABLE}?api=$URL"
echo "Plan B (local):   http://localhost:$PORT/ui/"
