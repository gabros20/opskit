#!/usr/bin/env python3
"""run_triage.py — exercises `ops triage`: dry-run, --yes auto-file, and the interactive
override -> filing-rule learning loop (§10). Temp OPS_HOME; stdlib only."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []

TASK_CAP = "---\ntype: capture\ncreated: 2026-06-25\n---\nfix the Designatives webhook timeout"
NOTE_CAP = "---\ntype: capture\ncreated: 2026-06-25\n---\nRRF merges BM25 and vector rankings without score scaling"


def check(name, cond, detail=""):
    results.append((name, cond, detail))


def seed(home: Path, caps: dict):
    (home / "inbox").mkdir(parents=True, exist_ok=True)
    (home / "wiki").mkdir(parents=True, exist_ok=True)
    (home / "wiki" / "conventions.md").write_text("# Conventions\n\n## Filing rules\n", encoding="utf-8")
    for name, body in caps.items():
        (home / "inbox" / name).write_text(body, encoding="utf-8")


def triage(home: Path, *args, stdin=None):
    env = {**os.environ, "OPS_HOME": str(home)}
    return subprocess.run([sys.executable, str(REPO / "bin/triage/run.py"), *args],
                          input=stdin, capture_output=True, text=True, env=env)


def main() -> int:
    # A) dry-run: proposes, changes nothing
    with tempfile.TemporaryDirectory() as td:
        h = Path(td); seed(h, {"cap-a.md": TASK_CAP, "cap-b.md": NOTE_CAP})
        r = triage(h, "--dry-run")
        check("dry-run proposes TASK and NOTE", "TASK ->" in r.stdout and "NOTE ->" in r.stdout, r.stdout)
        check("dry-run changes nothing", len(list((h / "inbox").glob("cap-*.md"))) == 2)

    # B) --yes: files both correctly and empties inbox
    with tempfile.TemporaryDirectory() as td:
        h = Path(td); seed(h, {"cap-a.md": TASK_CAP, "cap-b.md": NOTE_CAP})
        r = triage(h, "--yes")
        tasks = list((h / "tasks" / "active").glob("T-*.md")) if (h / "tasks" / "active").exists() else []
        notes = list((h / "wiki" / "notes").glob("*.md")) if (h / "wiki" / "notes").exists() else []
        check("--yes creates a task for the action item", len(tasks) == 1, r.stdout + r.stderr)
        check("--yes creates a note for the fact", len(notes) == 1)
        check("--yes empties the inbox", len(list((h / "inbox").glob("cap-*.md"))) == 0)
        if tasks:
            check("task captured the text", "webhook timeout" in tasks[0].read_text())

    # C) interactive override (note->task) records a filing rule
    with tempfile.TemporaryDirectory() as td:
        h = Path(td); seed(h, {"cap-b.md": NOTE_CAP})           # classifies as NOTE
        r = triage(h, stdin="t\ny\n")                           # override to TASK, then record rule
        tasks = list((h / "tasks" / "active").glob("T-*.md")) if (h / "tasks" / "active").exists() else []
        conv = (h / "wiki" / "conventions.md").read_text()
        check("override files as TASK", len(tasks) == 1, r.stdout + r.stderr)
        check("override records a filing rule", "-> task" in conv, conv)

    print(f"{BOLD}triage (inbox -> tasks/wiki, with learning loop) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<42}" + (f" {DIM}{detail.strip()[:80]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
