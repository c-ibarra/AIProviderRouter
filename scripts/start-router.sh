#!/usr/bin/env bash
# Starts the ai-provider-router in the background if it isn't already running.
#
# Intended to be called from shell startup (a guard in .zshrc), not launchd or
# a Warp Launch Configuration — Warp always spawns the user's shell, so this
# ties the router's lifecycle to "opening Warp" in practice without depending
# on a Warp-specific hook (none exists) or an OS-level service that outlives
# the reason it was started. See docs/adr and the resolved operational
# decisions in openspec/PROJECT_SPEC.md for the rationale.
#
# Idempotent: safe to call from every new shell session (every new Warp tab).

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
STATE_DIR="$HOME/Library/Application Support/ai-provider-router"
PID_FILE="$STATE_DIR/router.pid"

mkdir -p "$STATE_DIR"

is_running() {
  [[ -f "$PID_FILE" ]] || return 1
  kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

if is_running; then
  exit 0
fi

(
  cd "$PROJECT_DIR"
  nohup uv run python -m router.adapters.http.main >/dev/null 2>&1 &
  echo $! > "$PID_FILE"
)
