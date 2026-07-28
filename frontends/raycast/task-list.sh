#!/bin/bash
# Raycast Script Command — task-list (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Plainkeep Task List
# @raycast.mode fullOutput
# @raycast.packageName plainkeep
# @raycast.icon 📋
# @raycast.description Active and waiting plainkeep tasks.
# @raycast.author plainkeep
set -euo pipefail
PLAINKEEP="$(command -v plainkeep || true)"
[ -n "$PLAINKEEP" ] || PLAINKEEP="${PLAINKEEP_HOME:-$HOME/plainkeep}/plainkeep"
exec "$PLAINKEEP" task list
