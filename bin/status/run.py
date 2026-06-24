#!/usr/bin/env python3
"""ops status — one-screen dashboard: tasks, inbox, last index, repo state (§4.1)."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

DB = paths.OPS_HOME / ".index" / "ops.sqlite"


def _count(d: Path, pat: str) -> int:
    return len(list(d.glob(pat))) if d.exists() else 0


def main():
    active = sorted((paths.TASKS / "active").glob("T-*.md")) if (paths.TASKS / "active").exists() else []
    waiting = sorted((paths.TASKS / "waiting").glob("T-*.md")) if (paths.TASKS / "waiting").exists() else []
    inbox = _count(paths.INBOX, "*.md")
    wiki = _count(paths.WIKI, "**/*.md")

    print(f"ops status — {paths.OPS_HOME}")
    print(f"  tasks:   {len(active)} active, {len(waiting)} waiting")
    for f in active[:7]:
        print(f"    • {f.stem}  {paths.title_of(f)}")
    if len(active) > 7:
        print(f"    … +{len(active)-7} more active")
    for f in waiting[:5]:
        print(f"    ⏸ {f.stem}  {paths.title_of(f)}")
    print(f"  inbox:   {inbox} item(s) to triage")
    print(f"  wiki:    {wiki} note(s)")
    if DB.exists():
        age = datetime.now() - datetime.fromtimestamp(DB.stat().st_mtime)
        mins = int(age.total_seconds() // 60)
        print(f"  index:   built {mins} min ago" if mins else "  index:   built just now")
    else:
        print("  index:   not built (run: ops index)")
    try:
        dirty = subprocess.run(["git", "-C", str(paths.OPS_HOME), "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        n = len(dirty.splitlines()) if dirty else 0
        print(f"  git:     {'clean' if n == 0 else str(n) + ' uncommitted change(s)'}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
