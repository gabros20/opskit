#!/usr/bin/env python3
"""
run_all.py — run every OFFLINE suite (no LLM, no cost) and summarize.

Covers: guardrail (§5), jobs registry (§15), sweep decay machine (§9.4), wiki integrity (§10),
and searchability/vector analysis (§10.2). The LLM-operator simulation (run_simulation.py) is
separate because it needs a model and network.

Usage:  python3 test/run_all.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GREEN, RED, BOLD, DIM, RESET = "\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[1m\033[0m"

SUITES = [
    ("guardrail model (§5)", "run_deterministic.py"),
    ("guardrail enforcement (§5)", "run_guardrail.py"),
    ("jobs registry (§15)", "run_jobs.py"),
    ("sweep decay (§9.4)", "run_sweep.py"),
    ("wiki integrity (§10)", "run_wiki.py"),
    ("wiki link edges (§10)", "run_wiki_edges.py"),
    ("state & consistency (§7/§8/§10/§14)", "run_state.py"),
    ("searchability model (§10.2)", "run_search.py"),
    ("stage-1 search impl (§10.2)", "run_search_impl.py"),
    ("stage-2 hybrid LanceDB (§10.2)", "run_search_vec.py"),
    ("daily-driver verbs (§4/§7)", "run_verbs.py"),
    ("triage flow (§4/§10)", "run_triage.py"),
    ("daily/weekly rhythm (§16)", "run_loops.py"),
    ("health verbs: doctor, wiki (§14/§10)", "run_health.py"),
]


def main() -> int:
    print(f"\033[1m{'='*60}\nOffline design-validation suites\n{'='*60}\033[0m\n")
    statuses = []
    for label, script in SUITES:
        proc = subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stdout.write(proc.stderr)
        ok = proc.returncode == 0
        statuses.append((label, ok))
        print(f"\033[2m{'-'*60}\033[0m\n")

    print("\033[1mSUMMARY\033[0m")
    allok = True
    for label, ok in statuses:
        allok = allok and ok
        mark = f"{GREEN}PASS\033[0m" if ok else f"{RED}FAIL\033[0m"
        print(f"  {mark}  {label}")
    print()
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
