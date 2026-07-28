#!/bin/bash
# Raycast Script Command — status-inline (proposal Part 3.3). A menu-bar/inline one-liner.
#
# @raycast.schemaVersion 1
# @raycast.title Plainkeep Status
# @raycast.mode inline
# @raycast.refreshTime 30s
# @raycast.packageName plainkeep
# @raycast.icon 🧭
# @raycast.description Plainkeep orientation in one line (tasks / inbox / index / git).
# @raycast.author plainkeep
#
# `plainkeep orient --line` is a ≤60-char cached string built for exactly this kind of prompt hook.
set -euo pipefail
PLAINKEEP="$(command -v plainkeep || true)"
[ -n "$PLAINKEEP" ] || PLAINKEEP="${PLAINKEEP_HOME:-$HOME/plainkeep}/plainkeep"
exec "$PLAINKEEP" orient --line
