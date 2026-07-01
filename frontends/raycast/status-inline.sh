#!/bin/bash
# Raycast Script Command — status-inline (proposal Part 3.3). A menu-bar/inline one-liner.
#
# @raycast.schemaVersion 1
# @raycast.title Ops Status
# @raycast.mode inline
# @raycast.refreshTime 30s
# @raycast.packageName ops
# @raycast.icon 🧭
# @raycast.description Ops orientation in one line (tasks / inbox / index / git).
# @raycast.author ops
#
# `ops orient --line` is a ≤60-char cached string built for exactly this kind of prompt hook.
set -euo pipefail
OPS="$(command -v ops || true)"
[ -n "$OPS" ] || OPS="${OPS_HOME:-$HOME/ops}/ops"
exec "$OPS" orient --line
