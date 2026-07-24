#!/usr/bin/env python3
"""
ops ui [args…] — the entry shim for the ops terminal UI (proposal: the ops.json/3 TUI).

The TUI ships as a SEPARATE binary (`ops-ui`) that lives OUTSIDE this repo and drives ops purely over
the machine contract (`ops <verb> --json`, `ops complete --json`, `ops help --json`). This shim just
hands the terminal to it: it locates `ops-ui` on PATH (or via $OPS_UI_BIN) and `execv`s it — it never
re-resolves the `ops` dispatcher, so there is no recursion. When the binary isn't installed it prints
a blocked-style, exact-remediation hint (mirroring the setup-layer `status: blocked` / `next` pattern)
and exits cleanly — a missing optional frontend is not a crash. Risk `read` (launching a UI has no
side effects of its own; every mutation the UI performs still goes back through a gated `ops` verb).
"""
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output  # noqa: E402

INSTALL_HINT = ("install the ops terminal UI (a separate binary) and put `ops-ui` on your PATH, "
                "or set OPS_UI_BIN=/path/to/ops-ui; then re-run `ops ui`")


def _resolve() -> str | None:
    """Absolute path to an EXECUTABLE ops-ui binary — an explicit $OPS_UI_BIN wins, else PATH lookup.
    `shutil.which` already guarantees an executable regular file; the explicit-path branch must check
    the same (isfile + X_OK) so a stale/dir/non-exec OPS_UI_BIN degrades to the blocked hint rather
    than crashing the later execv."""
    override = os.environ.get("OPS_UI_BIN")
    if override:
        p = override if os.path.isabs(override) else shutil.which(override)
        return p if (p and os.path.isfile(p) and os.access(p, os.X_OK)) else None
    return shutil.which("ops-ui")


def main(argv):
    _, argv = output.parse_argv(argv)
    exe = _resolve()
    if exe:
        # hand off the terminal to the TUI — replaces this process, never returns (no recursion:
        # we exec ops-ui directly, not the `ops` dispatcher). Guard execv so a race/permission error
        # still falls through to the blocked hint instead of a traceback (the "never a crash" contract).
        try:
            os.execv(exe, [os.path.basename(exe), *argv])
        except OSError:
            pass
    data = {"installed": False, "status": "blocked", "next": INSTALL_HINT}
    return output.emit(data, "ui", human=lambda _: f"ops-ui is not installed.\n  {INSTALL_HINT}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
