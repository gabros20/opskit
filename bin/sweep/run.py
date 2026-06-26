#!/usr/bin/env python3
"""
ops sweep [--dry-run] — the §9.4 macOS-inbox decay machine. Desktop/Downloads files untouched for
7 days MOVE (never delete) into <zone>/_swept/YYYY-MM/; items that have sat in _swept for 60 days go
to the Trash. So you get a week to `ops files ingest` what matters, then a 60-day net. Idempotent —
safe to run repeatedly and as the nightly job. Rescue is by ingest, not by reopening (§9.4).
"""
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

HOME = Path(os.environ.get("OPS_SWEEP_HOME", os.environ.get("HOME", "")))
SWEEP_DAYS = int(os.environ.get("OPS_SWEEP_DAYS", "7"))
TRASH_DAYS = int(os.environ.get("OPS_TRASH_DAYS", "60"))
ZONES = ["Desktop", "Downloads"]
DAY = 86400


def _age_days(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / DAY


def main(argv):
    dry = "--dry-run" in argv
    now = datetime.now()
    bucket = f"{now.year:04d}-{now.month:02d}"
    trash = HOME / ".Trash"
    promoted = trashed = 0

    for zname in ZONES:
        zone = HOME / zname
        if not zone.is_dir():
            continue
        swept = zone / "_swept"

        # phase 1 — promote: untouched 7+ days → _swept/YYYY-MM/ (move, never delete)
        for item in sorted(zone.iterdir()):
            if item.name == "_swept" or item.name.startswith("."):
                continue
            if _age_days(item) >= SWEEP_DAYS:
                dest_dir = swept / bucket
                dest = dest_dir / item.name
                i = 2
                while dest.exists():
                    dest = dest_dir / f"{item.stem}-{i}{item.suffix}"; i += 1
                print(f"  {'would move' if dry else 'moved'}: {zname}/{item.name} -> _swept/{bucket}/")
                if not dry:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(item), str(dest))
                    os.utime(dest, None)  # stamp swept-time into mtime (starts the 60-day clock)
                promoted += 1

        # phase 2 — trash: in _swept 60+ days → Trash (still recoverable there)
        if swept.is_dir():
            for b in sorted(swept.iterdir()):
                if not b.is_dir():
                    continue
                for item in sorted(b.iterdir()):
                    if _age_days(item) >= TRASH_DAYS:
                        print(f"  {'would trash' if dry else 'trashed'}: _swept/{b.name}/{item.name}")
                        if not dry:
                            trash.mkdir(parents=True, exist_ok=True)
                            tdest = trash / item.name
                            i = 2
                            while tdest.exists():
                                tdest = trash / f"{item.stem}-{i}{item.suffix}"; i += 1
                            shutil.move(str(item), str(tdest))
                        trashed += 1
                if not dry and b.is_dir() and not any(b.iterdir()):
                    b.rmdir()

    print(f"\nsweep: {promoted} promoted to _swept, {trashed} trashed"
          + (" (dry run)" if dry else ""))
    if not dry and (promoted or trashed):
        paths.append_journal(f"swept {promoted} to _swept, {trashed} to Trash")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
