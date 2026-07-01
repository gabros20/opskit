#!/bin/bash
# Raycast Script Command — task-list (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Ops Task List
# @raycast.mode fullOutput
# @raycast.packageName ops
# @raycast.icon 📋
# @raycast.description Active and waiting ops tasks.
# @raycast.author ops
set -euo pipefail
OPS="$(command -v ops || true)"
[ -n "$OPS" ] || OPS="${OPS_HOME:-$HOME/ops}/ops"
exec "$OPS" task list
