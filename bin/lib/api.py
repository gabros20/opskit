"""
api.py — the frozen public SDK (proposal Part 2.3). The ONE module a plugin verb may import: a small,
blessed re-export of lib internals with a versioned contract. Everything else in lib/ is PRIVATE and
may change without notice; only the names in `__all__` here are stable across an `OPS_API_VERSION`.

Why this exists: a plugin verb is the same shape as an engine verb (run.py + cmd.json, re-entering
through `ops <verb>`), so it MUST inherit the Iron Law seam — `classify()` gives a plugin the same
path-wall + transmit-block a core verb gets, instead of reaching around lib to skip it. The rest is
the minimum a useful verb needs: where things live (`paths`), how to journal, how to load/render note
types, how to borrow the model (`run_agent`), and how to emit the `--json` envelope (`output`).

A plugin declares the range it needs in plugin.json (`"api": ">=1,<2"`); `ops plugin add` refuses a
pack outside it. `test/run_plugin.py` snapshots every exported name's signature and fails on a
silent removal or change — the contract is checkable, not implicit.
"""
from __future__ import annotations

from . import paths            # type: ignore  # (namespace sibling)
from . import guardrail        # type: ignore
from . import notetype         # type: ignore
from . import agent            # type: ignore
from . import output           # type: ignore

OPS_API_VERSION = "1.0"

# --- filesystem roots + helpers (paths essentials) ---------------------------------------------
OPS_HOME = paths.OPS_HOME
WIKI = paths.WIKI
INBOX = paths.INBOX
append_journal = paths.append_journal
slugify = paths.slugify
today = paths.today
fm_field = paths.fm_field
link_targets = paths.link_targets

# --- the Iron Law seam: a plugin verb inherits the path-wall + transmit-block --------------------
classify = guardrail.classify

# --- note types (loaders + template render) ------------------------------------------------------
load_types = notetype.load_types
type_dir = notetype.type_dir
is_type = notetype.is_type
render_note = notetype.render

# --- agent indirection (deterministic fallback when no model is configured) ----------------------
run_agent = agent.run_agent

# --- the --json envelope ------------------------------------------------------------------------
emit = output.emit
emit_rows = output.emit_rows
fail = output.fail

__all__ = [
    "OPS_API_VERSION",
    "OPS_HOME", "WIKI", "INBOX", "append_journal", "slugify", "today", "fm_field", "link_targets",
    "classify",
    "load_types", "type_dir", "is_type", "render_note",
    "run_agent",
    "emit", "emit_rows", "fail",
]
