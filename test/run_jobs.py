#!/usr/bin/env python3
"""
run_jobs.py — check the §15 jobs registry against the design's own job rules. Offline, no LLM.

A FAIL here is a spec inconsistency: a job that can't legally be scheduled, references a verb
the surface doesn't document, declares the wrong risk, or writes where the path wall forbids.

Usage:  python3 test/run_jobs.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.jobsmodel import check_jobs  # noqa: E402

REG = Path(__file__).resolve().parent / "world" / "jobs.json"
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


def main() -> int:
    registry = json.loads(REG.read_text(encoding="utf-8"))
    findings = check_jobs(registry)
    passed = sum(1 for f in findings if f.ok)
    failed = len(findings) - passed
    print(f"{BOLD}Jobs-registry invariant suite{RESET} — {len(findings)} checks over {len(registry['jobs'])} jobs\n")
    cur = None
    for f in findings:
        if f.job != cur:
            cur = f.job
            print(f"  {BOLD}{f.job}{RESET}")
        mark = f"{GREEN}PASS{RESET}" if f.ok else f"{RED}FAIL{RESET}"
        print(f"      {mark} {f.rule:<22} {DIM}{f.detail}{RESET}")
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(findings)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
