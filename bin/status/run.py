#!/usr/bin/env python3
"""ops status — one-screen dashboard: tasks, inbox, last index, repo state (§4.1)."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output, paths  # noqa: E402

DB = paths.OPS_HOME / ".index" / "ops.sqlite"


def _count(d: Path, pat: str) -> int:
    return len(list(d.glob(pat))) if d.exists() else 0


def main(argv):
    _, argv = output.parse_argv(argv)
    active = sorted((paths.TASKS / "active").glob("T-*.md")) if (paths.TASKS / "active").exists() else []
    waiting = sorted((paths.TASKS / "waiting").glob("T-*.md")) if (paths.TASKS / "waiting").exists() else []
    inbox = _count(paths.INBOX, "*.md")
    wiki = _count(paths.WIKI, "**/*.md")

    index_age = None
    if DB.exists():
        index_age = int((datetime.now() - datetime.fromtimestamp(DB.stat().st_mtime)).total_seconds() // 60)
    git_dirty = None
    try:
        dirty = subprocess.run(["git", "-C", str(paths.OPS_HOME), "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        git_dirty = len(dirty.splitlines()) if dirty else 0
    except Exception:
        pass

    data = {
        "ops_home": str(paths.OPS_HOME),
        "active": len(active), "waiting": len(waiting),
        "active_tasks": [{"id": f.stem, "title": paths.title_of(f)} for f in active],
        "waiting_tasks": [{"id": f.stem, "title": paths.title_of(f)} for f in waiting],
        "inbox": inbox, "wiki": wiki,
        "index_age_min": index_age, "git_dirty": git_dirty,
    }

    def render(_):
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
            print(f"  index:   built {index_age} min ago" if index_age else "  index:   built just now")
        else:
            print("  index:   not built (run: ops index)")
        if git_dirty is not None:
            print(f"  git:     {'clean' if git_dirty == 0 else str(git_dirty) + ' uncommitted change(s)'}")

    return output.emit(data, "status", human=render)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
