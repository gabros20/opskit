#!/bin/bash
# Raycast Script Command — quick-capture (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Plainkeep Capture
# @raycast.mode compact
# @raycast.packageName plainkeep
# @raycast.icon 🧠
# @raycast.argument1 { "type": "text", "placeholder": "note text" }
# @raycast.description Capture a note into the plainkeep inbox for later triage.
# @raycast.author plainkeep
#
# Shells to `plainkeep` on PATH (fallback: $PLAINKEEP_HOME/plainkeep) so the guardrail + .logs apply — the frontend
# has zero privileged access; every write re-enters through the dispatcher.
set -euo pipefail
PLAINKEEP="$(command -v plainkeep || true)"
[ -n "$PLAINKEEP" ] || PLAINKEEP="${PLAINKEEP_HOME:-$HOME/plainkeep}/plainkeep"
exec "$PLAINKEEP" capture "$1"
