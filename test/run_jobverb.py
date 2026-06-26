#!/usr/bin/env python3
"""run_jobverb.py — exercises the `ops job` verb: list (with legality flags), run <name>
(manual fallback), apply (render launchd plists, skipping non-schedulable jobs). Temp OPS_HOME."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []

REGISTRY = {
    "external_allowlist": [],
    "jobs": {
        "index":       {"command": "ops index",      "schedule": {"interval_minutes": 60}, "risk": "read"},
        "consolidate": {"command": "ops consolidate", "schedule": {"daily": "02:30"},       "risk": "safe_write"},
        "danger":      {"command": "ops capture x",   "schedule": {"daily": "09:00"},       "risk": "confirm"},
    },
}


def check(name, cond, detail=""):
    results.append((name, cond, detail))


def run(home, *args):
    env = {**os.environ, "OPS_HOME": str(home)}
    return subprocess.run([sys.executable, str(REPO / "bin" / "job" / "run.py"), *args],
                          capture_output=True, text=True, env=env)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        h = Path(td)
        (h / "wiki" / "notes").mkdir(parents=True)
        (h / "wiki" / "notes" / "alpha.md").write_text(
            "---\ntype: note\nupdated: 2026-06-20\n---\n# Alpha\nretrieval and ranking\n")
        (h / "jobs").mkdir()
        (h / "jobs" / "registry.json").write_text(json.dumps(REGISTRY), encoding="utf-8")

        r = run(h, "list")
        check("job list shows the jobs", "index" in r.stdout and "consolidate" in r.stdout, r.stdout)
        check("job list flags a non-schedulable job", "danger" in r.stdout and "not schedulable" in r.stdout, r.stdout)

        r = run(h, "run", "index")
        check("job run index builds the index (rc 0)", r.returncode == 0 and (h / ".index" / "ops.sqlite").exists(), r.stdout + r.stderr)

        r = run(h, "run", "consolidate")
        j = "\n".join(p.read_text() for p in (h / "journal").rglob("*.md")) if (h / "journal").exists() else ""
        check("job run consolidate writes a digest", r.returncode == 0 and "## Consolidate" in j, r.stdout + r.stderr)

        r = run(h, "run", "danger")
        check("job run refuses a non-schedulable job", r.returncode == 1 and "refusing" in (r.stdout + r.stderr), r.stdout + r.stderr)

        r = run(h, "apply")
        ld = h / "jobs" / "launchd"
        check("job apply renders schedulable plists", (ld / "com.ops.index.plist").exists() and (ld / "com.ops.consolidate.plist").exists(), r.stdout + r.stderr)
        check("job apply skips non-schedulable", not (ld / "com.ops.danger.plist").exists() and "skipped" in r.stdout, r.stdout)
        if (ld / "com.ops.index.plist").exists():
            pl = (ld / "com.ops.index.plist").read_text()
            check("plist is well-formed launchd", "StartInterval" in pl and "com.ops.index" in pl and "OPS_HOME" in pl, pl[:200])
        r = run(h, "run", "nope")
        check("job run rejects an unknown job name", r.returncode == 2, r.stdout + r.stderr)

    print(f"{BOLD}Jobs scheduler verb (job list/run/apply) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<46}" + (f" {DIM}{detail.strip()[:80]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
