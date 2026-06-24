"""paths.py — shared filesystem roots + small helpers for the ops verbs."""
from __future__ import annotations
import os
from datetime import date, datetime
from pathlib import Path

OPS_HOME = Path(os.environ.get("OPS_HOME", Path(__file__).resolve().parents[2]))
INBOX = OPS_HOME / "inbox"
TASKS = OPS_HOME / "tasks"
JOURNAL = OPS_HOME / "journal"
WIKI = OPS_HOME / "wiki"
BIN = OPS_HOME / "bin"
TASK_STATUSES = ("inbox", "active", "waiting", "done")


def today() -> str:
    return date.today().isoformat()


def now_stamp() -> str:
    # millisecond precision so rapid captures don't collide on filename
    n = datetime.now()
    return n.strftime("%Y%m%d-%H%M%S-") + f"{n.microsecond // 1000:03d}"


def append_journal(line: str) -> Path:
    """Append one timestamped line to today's journal note (the shared activity record, §8)."""
    d = date.today()
    note = JOURNAL / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.isoformat()}.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    if not note.exists():
        note.write_text(f"---\ntype: journal\ndate: {d.isoformat()}\n---\n# {d.isoformat()}\n\n")
    with open(note, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.now().strftime('%H:%M')} {line}\n")
    return note


def title_of(path: Path) -> str:
    """First markdown heading, else the slug."""
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.startswith("# "):
                return ln[2:].strip()
    except Exception:
        pass
    return path.stem
