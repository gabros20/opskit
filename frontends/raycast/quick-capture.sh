#!/bin/bash
# Raycast Script Command — quick-capture (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Ops Capture
# @raycast.mode compact
# @raycast.packageName ops
# @raycast.icon 🧠
# @raycast.argument1 { "type": "text", "placeholder": "note text" }
# @raycast.description Capture a note into the ops inbox for later triage.
# @raycast.author ops
#
# Shells to `ops` on PATH (fallback: $OPS_HOME/ops) so the guardrail + .logs apply — the frontend
# has zero privileged access; every write re-enters through the dispatcher.
set -euo pipefail
OPS="$(command -v ops || true)"
[ -n "$OPS" ] || OPS="${OPS_HOME:-$HOME/ops}/ops"
exec "$OPS" capture "$1"
