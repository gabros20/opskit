#!/usr/bin/env python3
"""
ops files ingest [<path>] | open <slug> — the binary-assets plane (§9). ingest routes binaries out
of inbox/ into ~/files with a wiki SHADOW NOTE pointing at each (so the knowledge graph references
material it never stores). Work material is auto-filed (safe_write); anything that looks
personal/legal/family is only PROPOSED for iCloud and left in place — the §5 wall, made operational.
open reveals a file in Finder via its shadow note.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

YEL, GREEN, DIM, RESET = "\033[33m", "\033[32m", "\033[2m", "\033[0m"
# names that signal irreplaceable personal/legal/family docs → propose iCloud, never auto-file (§5)
PERSONAL = ("tax", "szja", "nav", "ado", "adó", "medical", "orvos", "contract", "szerzod", "szerződ",
            "legal", "passport", "utlevel", "útlevel", "birth", "szulet", "szület", "insurance",
            "biztosit", "biztosít", "marriage", "hazas", "házas", "will", "vegrendel")
TEXT_SUFFIXES = {".md", ".txt"}


def _is_personal(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in PERSONAL)


def _shadow(dest: Path, title: str) -> Path:
    d = paths.WIKI / "files"; d.mkdir(parents=True, exist_ok=True)
    base = paths.slugify(Path(title).stem)
    existing = {p.stem for p in paths.WIKI.rglob("*.md")}
    slug, i = base, 2
    while slug in existing:
        slug, i = f"{base}-{i}", i + 1
    f = d / f"{slug}.md"
    f.write_text(f"---\ntype: file\ntitle: {title}\nstatus: active\nsource: ingest\n"
                 f"ingested: {paths.today()}\npath: {dest}\ntags: []\n---\n# {title}\n\n"
                 f"Shadow note for a binary in `~/files`. The file itself is at `{dest}` "
                 f"(not stored in git).\n", encoding="utf-8")
    return f


def cmd_ingest(argv):
    if argv:
        sources = [Path(argv[0]).expanduser()]
    else:
        sources = [p for p in paths.INBOX.iterdir()
                   if p.is_file() and p.suffix.lower() not in TEXT_SUFFIXES and p.name != ".gitkeep"] \
            if paths.INBOX.exists() else []
    if not sources:
        print("nothing to ingest (drop a binary into inbox/, or pass a path)."); return 0
    dest_dir = paths.FILES_ROOT / "inbox"
    filed = proposed = 0
    for src in sources:
        if not src.exists():
            print(f"  not found: {src}"); continue
        if _is_personal(src.name):
            print(f"  {YEL}PROPOSE iCloud{RESET}: '{src.name}' looks personal/legal — move it yourself to "
                  f"iCloud (the wall forbids any verb writing there). Left in place.")
            proposed += 1
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        i = 2
        while dest.exists():
            dest = dest_dir / f"{src.stem}-{i}{src.suffix}"; i += 1
        shutil.move(str(src), str(dest))
        note = _shadow(dest, src.name)
        paths.append_journal(f"files ingest {src.name} -> {dest}")
        print(f"  {GREEN}filed{RESET}: {src.name} -> ~/files/inbox/  ({note.relative_to(paths.OPS_HOME)})")
        filed += 1
    print(f"\nfiles ingest: {filed} filed, {proposed} proposed for iCloud (left in place)")
    return 0


def cmd_open(argv):
    if not argv:
        print("usage: ops files open <slug>", file=sys.stderr); return 2
    note = paths.WIKI / "files" / f"{argv[0]}.md"
    if not note.exists():
        print(f"no shadow note: wiki/files/{argv[0]}.md", file=sys.stderr); return 1
    target = paths.fm_field(note, "path")
    if not target:
        print("shadow note has no path:", file=sys.stderr); return 1
    print(target)
    if not os.environ.get("OPS_NO_OPEN") and sys.platform == "darwin" and Path(target).exists():
        subprocess.run(["open", "-R", target], check=False)
    return 0


def main(argv):
    action = argv[0] if argv else "ingest"
    if action == "ingest":
        return cmd_ingest(argv[1:])
    if action == "open":
        return cmd_open(argv[1:])
    print("usage: ops files ingest [<path>] | open <slug>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
