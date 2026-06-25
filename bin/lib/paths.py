"""paths.py — shared filesystem roots + small helpers for the ops verbs."""
from __future__ import annotations
import os
import re
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


def journal_path(d: date | None = None) -> Path:
    d = d or date.today()
    return JOURNAL / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.isoformat()}.md"


def ensure_journal(d: date | None = None) -> tuple[Path, bool]:
    """Return (path, created). Creates today's journal note with a header if missing."""
    d = d or date.today()
    note = journal_path(d)
    created = not note.exists()
    if created:
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\ntype: journal\ndate: {d.isoformat()}\n---\n# {d.isoformat()}\n\n", encoding="utf-8")
    return note, created


def append_journal(line: str) -> Path:
    """Append one timestamped line to today's journal note (the shared activity record, §8)."""
    note, _ = ensure_journal()
    with open(note, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.now().strftime('%H:%M')} {line}\n")
    return note


def git(*args) -> str:
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(OPS_HOME), *args],
                              capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return ""


def slugify(s: str, n: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s[:n].rstrip("-")) or "note"


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def link_targets(text: str) -> list[str]:
    """Normalized [[wikilink]] targets (strip #heading / |alias)."""
    return [t.split("#", 1)[0].split("|", 1)[0].strip() for t in LINK_RE.findall(text)]


def fm_field(path: Path, key: str) -> str:
    """Read a single frontmatter `key:` value from a markdown file ('' if absent)."""
    try:
        m = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", path.read_text(encoding="utf-8"))
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def title_of(path: Path) -> str:
    """First markdown heading, else the slug."""
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.startswith("# "):
                return ln[2:].strip()
    except Exception:
        pass
    return path.stem
