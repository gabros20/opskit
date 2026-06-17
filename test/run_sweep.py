#!/usr/bin/env python3
"""
run_sweep.py — assert the §9.4 decay machine behaves as designed. Offline, no LLM.

Each test seeds files, advances a virtual clock running the daily sweep, and checks the timers
and the three guarantees (move-not-delete, ingest-removes-from-decay, ~67-day floor before loss).

Usage:  python3 test/run_sweep.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sweepsim import Machine, FileState, SWEEP_DAYS, TRASH_DAYS  # noqa: E402

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = ""):
    results.append((name, cond, detail))


def t_stays_within_7():
    m = Machine([FileState("fresh.pdf", "downloads", last_touched_day=0)])
    m.advance_to(SWEEP_DAYS - 1)            # day 6
    check("untouched <7d stays put", m.files["fresh.pdf"].zone == "downloads",
          f"zone={m.files['fresh.pdf'].zone}")


def t_moves_at_7():
    m = Machine([FileState("old.pdf", "desktop", last_touched_day=0)])
    m.advance_to(SWEEP_DAYS)                # day 7
    f = m.files["old.pdf"]
    check("untouched >=7d moves to _swept", f.zone == "swept", f"zone={f.zone}")
    check("move is dated (YYYY-MM bucket)", getattr(f, "bucket", None) == "2026-06",
          f"bucket={getattr(f, 'bucket', None)}")
    check("move not delete (not trashed at 7d)", f.name not in [n for _, n in m.trash_log])


def t_touch_resets_timer():
    m = Machine([FileState("active.md", "desktop", last_touched_day=0)])
    m.advance_to(12, actions={5: [("touch", "active.md")]})
    f = m.files["active.md"]
    # touched on day 5 -> would sweep at day 12 (5+7); at day 12 it should JUST move
    check("touch resets the 7-day timer", f.zone == "swept" and f.swept_on_day == 12,
          f"zone={f.zone}, swept_on_day={f.swept_on_day}")


def t_trashed_at_67():
    m = Machine([FileState("doomed.zip", "downloads", last_touched_day=0)])
    m.advance_to(SWEEP_DAYS + TRASH_DAYS - 1)   # day 66
    check("not trashed before 67 days", m.files["doomed.zip"].zone == "swept",
          f"day66 zone={m.files['doomed.zip'].zone}")
    m.advance_to(SWEEP_DAYS + TRASH_DAYS)        # day 67
    check("trashed at day 67 (7+60)", m.files["doomed.zip"].zone == "trash",
          f"day67 zone={m.files['doomed.zip'].zone}")


def t_ingest_removes_from_decay():
    m = Machine([FileState("keepme.pdf", "downloads", last_touched_day=0)])
    m.advance_to(20, actions={3: [("ingest", "keepme.pdf")]})
    f = m.files["keepme.pdf"]
    check("ingest removes file from decay path", f.zone == "ingested", f"zone={f.zone}")
    check("ingested file never trashed", f.name not in [n for _, n in m.trash_log])


def t_idempotent_same_day():
    # advance_to already calls run_sweep twice per day; verify no double-move artifacts:
    m = Machine([FileState("x.pdf", "desktop", last_touched_day=0)])
    m.advance_to(8)
    f = m.files["x.pdf"]
    moves = [h for h in f.history if "MOVED" in h]
    check("sweep is idempotent (single move)", len(moves) == 1, f"move events={len(moves)}")


def t_nothing_lost_silently():
    # over 90 days, every file is accounted for in exactly one terminal/known zone
    files = [FileState(f"f{i}.bin", "downloads", last_touched_day=0) for i in range(5)]
    m = Machine(files)
    m.advance_to(90)
    for f in files:
        ok = f.zone in ("swept", "trash", "ingested")
        check(f"{f.name} accounted for", ok, f"zone={f.zone}")


def main() -> int:
    for t in (t_stays_within_7, t_moves_at_7, t_touch_resets_timer, t_trashed_at_67,
              t_ingest_removes_from_decay, t_idempotent_same_day, t_nothing_lost_silently):
        t()
    print(f"{BOLD}Sweep decay-machine simulation{RESET} — {len(results)} assertions "
          f"(SWEEP_DAYS={SWEEP_DAYS}, TRASH_DAYS={TRASH_DAYS})\n")
    passed = 0
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        passed += 1 if ok else 0
        print(f"  {mark} {name:<40} {DIM}{detail}{RESET}")
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} assertions")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
