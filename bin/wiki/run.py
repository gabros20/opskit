#!/usr/bin/env python3
"""
ops wiki open <slug> | edit <slug> | new <type> <name> | backlinks <slug> | stale [days] | orphans | list
  [--dry-run] [--json]
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
    _, argv = output.parse_argv(argv)
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
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
            output.fail(output.EXIT_NOT_FOUND, f"no note '{slug}'", verb="wiki")
        data = {"slug": slug, "path": str(p.relative_to(paths.OPS_HOME))}
        return output.emit(data, "wiki", human=lambda _: render.open_note(p))

    elif action == "edit":
        slug = argv[1] if len(argv) > 1 else ""
        if not slug:
            slug = _choose(notes, "edit")
            if not slug:
                return 0
        p = notes.get(slug)
        if not p:
            output.fail(output.EXIT_NOT_FOUND, f"no note '{slug}'", verb="wiki")
        editor = os.environ.get("OPS_EDITOR") or os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        try:
            rc = subprocess.run([*editor.split(), str(p)]).returncode
        except FileNotFoundError:
            print(f"editor not found: {editor} (set $EDITOR)", file=sys.stderr); return 1
        return rc

    elif action == "new":
        if len(argv) < 3:
            output.fail(output.EXIT_USAGE, "usage: ops wiki new <type> <name>", verb="wiki")
        typ, name = argv[1], " ".join(argv[2:])
        if not notetype.is_type(typ):
            output.fail(output.EXIT_USAGE, f"type must be one of {sorted(notetype.load_types())}", verb="wiki")
        slug = paths.slugify(name)
        if slug in notes:
            output.fail(output.EXIT_UNEXPECTED,
                        f"slug '{slug}' already exists ({notes[slug].relative_to(paths.OPS_HOME)}) — slugs are unique",
                        verb="wiki")
        rel = (paths.WIKI / notetype.type_dir(typ) / f"{slug}.md").relative_to(paths.OPS_HOME)
        if dry:
            data = {"dry_run": True, "would_create": str(rel), "type": typ, "slug": slug}
            return output.emit(data, "wiki",
                               human=lambda _: f"would create -> {rel}  (dry run — nothing written)")
        d = paths.WIKI / notetype.type_dir(typ)
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{slug}.md"
        f.write_text(notetype.render(typ, title=name, slug=slug), encoding="utf-8")
        paths.append_journal(f"wiki new {typ}: {slug}")
        data = {"path": str(rel), "type": typ, "slug": slug}
        return output.emit(data, "wiki", human=lambda _: f"created -> {rel}")

    elif action == "backlinks":
        slug = argv[1] if len(argv) > 1 else ""
        if slug not in notes:
            output.fail(output.EXIT_NOT_FOUND, f"no note '{slug}'", verb="wiki")
        ins = sorted(_graph(notes)[slug])
        rows = [{"slug": s, "path": str(notes[s].relative_to(paths.OPS_HOME))} for s in ins]

        def render_bl(rs):
            return "\n".join([f"{len(rs)} backlink(s) to [[{slug}]]:", *[f"  {r['path']}" for r in rs]])
        return output.emit_rows(rows, "wiki", human=render_bl, header={"slug": slug})

    elif action == "stale":
        days = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 180
        cutoff = date.today().toordinal() - days
        pairs = []
        for slug, p in notes.items():
            u = paths.fm_field(p, "updated")
            try:
                if date.fromisoformat(u[:10]).toordinal() < cutoff:
                    pairs.append((u, slug))
            except Exception:
                pass
        rows = [{"updated": u, "slug": slug} for u, slug in sorted(pairs)]

        def render_stale(rs):
            return "\n".join([f"{len(rs)} note(s) not updated in {days}+ days:",
                              *[f"  {r['updated']}  {r['slug']}" for r in rs]])
        return output.emit_rows(rows, "wiki", human=render_stale, header={"days": days})

    elif action == "orphans":
        inbound = _graph(notes)
        orphans = sorted(s for s, p in notes.items()
                         if not inbound[s] and paths.fm_field(p, "type") == "note"
                         and s not in ("index", "conventions"))
        rows = [{"slug": s} for s in orphans]

        def render_orph(rs):
            return "\n".join([f"{len(rs)} orphan note(s) (type note, no inbound links):",
                              *[f"  {r['slug']}" for r in rs]])
        return output.emit_rows(rows, "wiki", human=render_orph)

    elif action == "list":
        by_type = {}
        for p in notes.values():
            t = paths.fm_field(p, "type") or "?"
            by_type[t] = by_type.get(t, 0) + 1
        total = len(notes)
        rows = [{"type": t, "count": n} for t, n in sorted(by_type.items())]

        def render_list(rs):
            return "\n".join([f"wiki: {total} note(s)", *[f"  {r['type']}: {r['count']}" for r in rs]])
        return output.emit_rows(rows, "wiki", human=render_list, header={"notes": total})
    else:
        output.fail(output.EXIT_USAGE,
                    "usage: ops wiki open <slug>|edit <slug>|new <type> <name>|backlinks <slug>|stale [days]|orphans|list",
                    verb="wiki")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
