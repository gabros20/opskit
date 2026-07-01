#!/bin/bash
# Raycast Script Command — task-add (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Ops Task Add
# @raycast.mode compact
# @raycast.packageName ops
# @raycast.icon ✅
# @raycast.argument1 { "type": "text", "placeholder": "task title" }
# @raycast.description Add a task to the ops task system.
# @raycast.author ops
set -euo pipefail
OPS="$(command -v ops || true)"
[ -n "$OPS" ] || OPS="${OPS_HOME:-$HOME/ops}/ops"
exec "$OPS" task add "$1"
