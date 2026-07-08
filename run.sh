#!/usr/bin/env bash
# Sets up whatever is missing, then starts the app. Safe to run every time.
#
# One script for both first run and every run after, because you should not
# have to know which one you are doing. Every step checks before it acts, so
# the second run skips straight to starting the app.
#
# There is no database to install: everything lives in data/jobsearch.db.
#
#   ./run.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
WEB="$ROOT/web"
VENV="$BACKEND/.venv/bin/python"
MODEL="llama3.2:3b"

say() { printf "\n==> %s\n" "$1"; }
ok() { printf "    %s\n" "$1"; }
die() { printf "\n%s\n" "$1" >&2; exit 1; }

need() {
  command -v "$1" >/dev/null 2>&1 || die "$2 is not installed.
  $3
  Then open a new terminal and run this script again."
}

# --- 1. Prerequisites -------------------------------------------------------
say "Checking prerequisites"
if [ "$(uname)" = "Darwin" ]; then
  HINT_NODE="brew install node"; HINT_PY="brew install python@3.12"
  HINT_OLLAMA="brew install ollama"
else
  HINT_NODE="sudo apt install nodejs npm"; HINT_PY="sudo apt install python3 python3-venv"
  HINT_OLLAMA="curl -fsSL https://ollama.com/install.sh | sh"
fi

need node "Node.js" "$HINT_NODE"
need python3 "Python" "$HINT_PY"
need ollama "Ollama" "$HINT_OLLAMA"

# Only a floor, not a ceiling: requirements.txt uses minimum bounds so pip
# resolves whatever has wheels for this interpreter.
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  || die "Python 3.10 or newer is required (found $(python3 --version)).
  $HINT_PY"
ok "node, python and ollama all present"

# --- 2. Model ---------------------------------------------------------------
say "Checking the language model"
# `brew install ollama` installs the binary but starts no server, so every
# ollama command would fail with a connection error. Start one ourselves if
# nothing is listening; a desktop install that already runs is left alone.
if ! curl -sf http://localhost:11434/api/version >/dev/null 2>&1; then
  ok "Starting the Ollama server..."
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  waited=0
  until curl -sf http://localhost:11434/api/version >/dev/null 2>&1; do
    sleep 2; waited=$((waited + 2))
    [ "$waited" -ge 60 ] && die "Ollama would not start. See /tmp/ollama-serve.log"
  done
fi

if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
  ok "Downloading $MODEL (about 2 GB, one time)..."
  ollama pull "$MODEL" || die "Model download failed. Check your connection and re-run."
fi
ok "$MODEL ready"

# --- 3. Backend -------------------------------------------------------------
say "Preparing the backend"
[ -x "$VENV" ] || (cd "$BACKEND" && python3 -m venv .venv)

# Has the install already happened? `find_spec` answers that without importing
# anything - importing sentence_transformers drags in PyTorch and takes seconds,
# on every run, to answer a question about file layout.
CHECK='import importlib.util as u; import sys; sys.exit(0 if all(u.find_spec(m) for m in ("fastapi","sentence_transformers","alembic")) else 1)'
if ! "$VENV" -c "$CHECK" >/dev/null 2>&1; then
  ok "Installing Python packages (a few minutes - PyTorch is large)..."
  "$VENV" -m pip install --disable-pip-version-check -q --upgrade pip
  "$VENV" -m pip install --disable-pip-version-check -r "$BACKEND/requirements.txt"
fi

# Creates data/jobsearch.db on the first run and is a no-op on every one after.
ok "Applying database migrations..."
(cd "$BACKEND" && "$VENV" -m alembic upgrade head)
ok "Backend ready"

# --- 4. Frontend ------------------------------------------------------------
say "Preparing the frontend"
[ -d "$WEB/node_modules" ] || (cd "$WEB" && npm install)
ok "Frontend ready"

# --- 5. Start ---------------------------------------------------------------
say "Starting the app"

# Starting a second copy on a taken port dies on arrival, and the health check
# below would still pass against the *old* one - success that is really someone
# else's process. Refuse instead.
for port in 8000 3000; do
  if curl -sf -m 2 "http://localhost:$port" >/dev/null 2>&1 \
     || curl -sf -m 2 "http://localhost:$port/health" >/dev/null 2>&1; then
    die "Port $port is already in use.
  Another copy of this app is probably still running. Stop it, then run this
  script again."
  fi
done

(cd "$BACKEND" && "$VENV" -m uvicorn app.main:app --reload --port 8000) &
BACK_PID=$!
(cd "$WEB" && npm run dev) &
WEB_PID=$!

# Ctrl+C should take the whole app down, not orphan half of it.
trap 'kill $BACK_PID $WEB_PID 2>/dev/null || true' INT TERM EXIT

waited=0
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  sleep 2; waited=$((waited + 2))
  [ "$waited" -ge 120 ] && die "The backend did not come up. Check the output above."
done

printf "\n  The app is running at http://localhost:3000\n"
printf "  Press Ctrl+C to stop. Next time, just run this script again.\n\n"
wait
