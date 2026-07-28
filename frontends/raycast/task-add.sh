#!/bin/bash
# Raycast Script Command — task-add (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Plainkeep Task Add
# @raycast.mode compact
# @raycast.packageName plainkeep
# @raycast.icon ✅
# @raycast.argument1 { "type": "text", "placeholder": "task title" }
# @raycast.description Add a task to the plainkeep task system.
# @raycast.author plainkeep
set -euo pipefail
PLAINKEEP="$(command -v plainkeep || true)"
[ -n "$PLAINKEEP" ] || PLAINKEEP="${PLAINKEEP_HOME:-$HOME/plainkeep}/plainkeep"
exec "$PLAINKEEP" task add "$1"
