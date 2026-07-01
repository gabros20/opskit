#!/bin/bash
# Raycast Script Command — search (proposal Part 3.3).
#
# @raycast.schemaVersion 1
# @raycast.title Ops Search
# @raycast.mode fullOutput
# @raycast.packageName ops
# @raycast.icon 🔎
# @raycast.argument1 { "type": "text", "placeholder": "query" }
# @raycast.description Ranked file#heading hits from the ops index.
# @raycast.author ops
#
# Uses `ops search --json` (the stable machine contract) and extracts the top hit paths with
# bash-only tools — no python, no lib import. Open a hit in the terminal with `ops open <slug>`.
set -euo pipefail
OPS="$(command -v ops || true)"
[ -n "$OPS" ] || OPS="${OPS_HOME:-$HOME/ops}/ops"
"$OPS" search "$1" --json 2>/dev/null \
  | grep -o '"path":"[^"]*"' \
  | sed 's/^"path":"//; s/"$//' \
  || echo "no hits (try: ops index)"
