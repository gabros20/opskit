#!/usr/bin/env python3
"""
ops wiki open <slug> | edit <slug> | new <type> <name> | backlinks <slug> | stale [days] | orphans | list
— navigate and grow the knowledge wiki (§10). Slugs resolve by basename ([[wikilinks]] style).
"""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import notetype, output, paths, render  # noqa: E402


def _notes():
    if not paths.WIKI.exists():
        return {}
    return {p.stem: p for p in sorted(paths.WIKI.rglob("*.md"))}


def _choose(notes, label):
    """No slug given: fuzzy-pick with fzf (live preview), else list what's available. §Tier-2."""
    items = sorted(notes)
    if not items:
        print("no notes yet — capture and triage, or: ops wiki new note \"…\""); return None
    ops_bin = paths.OPS_HOME / "ops"
    preview = f'OPS_RENDER=plain "{ops_bin}" wiki open {{}}'
    sel = render.fzf_pick(items, preview=preview, prompt=f"{label} note> ")
    if sel and sel in notes:
        return sel
    print(f"{len(items)} note(s) — pass a slug (e.g. `ops wiki {label} <slug>`):")
    for s in items:
        print(f"  {s}")
    return None


def _graph(notes):
    inbound = {s: set() for s in notes}
    for slug, p in notes.items():
        for tgt in paths.link_targets(p.read_text(encoding="utf-8")):
            if tgt in inbound and tgt != slug:
                inbound[tgt].add(slug)
    return inbound


def main(argv):
    action = argv[0] if argv else "list"
    notes = _notes()

    if action == "open":
        slug = argv[1] if len(argv) > 1 else ""
        if not slug:
            slug = _choose(notes, "open")
            if not slug:
                return 0
        p = notes.get(slug)
        if not p:
            print(f"no note '{slug}'", file=sys.stderr); return output.EXIT_NOT_FOUND
        render.open_note(p)

    elif action == "edit":
        slug = argv[1] if len(argv) > 1 else ""
        if not slug:
            slug = _choose(notes, "edit")
            if not slug:
                return 0
        p = notes.get(slug)
        if not p:
            print(f"no note '{slug}'", file=sys.stderr); return output.EXIT_NOT_FOUND
        editor = os.environ.get("OPS_EDITOR") or os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        try:
            rc = subprocess.run([*editor.split(), str(p)]).returncode
        except FileNotFoundError:
            print(f"editor not found: {editor} (set $EDITOR)", file=sys.stderr); return 1
        return rc

    elif action == "new":
        if len(argv) < 3:
            print("usage: ops wiki new <type> <name>", file=sys.stderr); return 2
        typ, name = argv[1], " ".join(argv[2:])
        if not notetype.is_type(typ):
            print(f"type must be one of {sorted(notetype.load_types())}", file=sys.stderr); return 2
        slug = paths.slugify(name)
        if slug in notes:
            print(f"slug '{slug}' already exists ({notes[slug].relative_to(paths.OPS_HOME)}) — slugs are unique",
                  file=sys.stderr); return 1
        d = paths.WIKI / notetype.type_dir(typ)
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{slug}.md"
        f.write_text(notetype.render(typ, title=name, slug=slug), encoding="utf-8")
        paths.append_journal(f"wiki new {typ}: {slug}")
        print(f"created -> {f.relative_to(paths.OPS_HOME)}")

    elif action == "backlinks":
        slug = argv[1] if len(argv) > 1 else ""
        if slug not in notes:
            print(f"no note '{slug}'", file=sys.stderr); return output.EXIT_NOT_FOUND
        ins = sorted(_graph(notes)[slug])
        print(f"{len(ins)} backlink(s) to [[{slug}]]:")
        for s in ins:
            print(f"  {notes[s].relative_to(paths.OPS_HOME)}")

    elif action == "stale":
        days = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 180
        cutoff = date.today().toordinal() - days
        rows = []
        for slug, p in notes.items():
            u = paths.fm_field(p, "updated")
            try:
                if date.fromisoformat(u[:10]).toordinal() < cutoff:
                    rows.append((u, slug))
            except Exception:
                pass
        print(f"{len(rows)} note(s) not updated in {days}+ days:")
        for u, slug in sorted(rows):
            print(f"  {u}  {slug}")

    elif action == "orphans":
        inbound = _graph(notes)
        orphans = [s for s, p in notes.items()
                   if not inbound[s] and paths.fm_field(p, "type") == "note" and s not in ("index", "conventions")]
        print(f"{len(orphans)} orphan note(s) (type note, no inbound links):")
        for s in sorted(orphans):
            print(f"  {s}")

    elif action == "list":
        by_type = {}
        for p in notes.values():
            by_type.setdefault(paths.fm_field(p, "type") or "?", 0)
            by_type[paths.fm_field(p, "type") or "?"] += 1
        print(f"wiki: {len(notes)} note(s)")
        for t, n in sorted(by_type.items()):
            print(f"  {t}: {n}")
    else:
        print("usage: ops wiki open <slug>|edit <slug>|new <type> <name>|backlinks <slug>|stale [days]|orphans|list",
              file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
