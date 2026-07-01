#!/usr/bin/env python3
"""
ops files ingest [<path>] [--client|--project|--area <slug> | --research] | link <file> <hub>
        | list [--hub <slug>] | open <slug>  — the binary-assets plane (§9).

ingest routes a binary out of inbox/ into ~/files and writes a wiki SHADOW NOTE (wiki/files/<slug>.md)
that points at it — the graph references material it never stores. Routing (the §9 MAP):
  --client X / --project X / --area X  → ~/files/<kind>/X/in/  and the file is LINKED from that hub
  --research                           → ~/files/research/
  (none)                               → ~/files/inbox/        (unrouted; link later with `files link`)
When routed to a hub, the shadow note is added under the hub's `## Files` section (bidirectional link).
Re-ingesting the same bytes is de-duped by sha256 (no name-2 copies) and just (re)links the existing
shadow note. Personal/legal/family docs are only PROPOSED for iCloud and left in place — the §5 wall.

link  attaches an already-ingested asset to a hub note after the fact.
list  shows the asset catalogue (optionally one hub's files).
open  reveals a file in Finder via its shadow note.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output, paths  # noqa: E402

YEL, GREEN, DIM, CYAN, RESET = "\033[33m", "\033[32m", "\033[2m", "\033[36m", "\033[0m"
PERSONAL = ("tax", "szja", "nav", "ado", "adó", "medical", "orvos", "contract", "szerzod", "szerződ",
            "legal", "passport", "utlevel", "útlevel", "birth", "szulet", "szület", "insurance",
            "biztosit", "biztosít", "marriage", "hazas", "házas", "will", "vegrendel")
TEXT_SUFFIXES = {".md", ".txt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".heic"}
HUB_KIND = {"--client": "clients", "--project": "projects", "--area": "areas"}


def _is_personal(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in PERSONAL)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _shadows() -> list[Path]:
    d = paths.WIKI / "files"
    return sorted(d.glob("*.md")) if d.exists() else []


def _find_by_hash(sha: str):
    for p in _shadows():
        if paths.fm_field(p, "sha256") == sha:
            return p
    return None


def _hub_note(slug: str):
    """Resolve a hub slug to its wiki note (any folder), or None."""
    hits = [p for p in paths.WIKI.rglob(f"{slug}.md")] if paths.WIKI.exists() else []
    return hits[0] if hits else None


def _link_into_hub(hub: Path, shadow_slug: str, title: str) -> bool:
    """Add `- [[shadow_slug]] — title` under the hub's `## Files` section (idempotent)."""
    text = hub.read_text(encoding="utf-8")
    line = f"- [[{shadow_slug}]] — {title}"
    if line in text:
        return False
    if "## Files" in text:
        out, done = [], False
        for ln in text.splitlines():
            out.append(ln)
            if ln.strip() == "## Files" and not done:
                out.append(line); done = True
        text = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    else:
        text = text.rstrip("\n") + f"\n\n## Files\n{line}\n"
    hub.write_text(text, encoding="utf-8")
    return True


def _shadow(dest: Path, title: str, sha: str, hub_slug: str | None) -> Path:
    d = paths.WIKI / "files"; d.mkdir(parents=True, exist_ok=True)
    base = paths.slugify(Path(title).stem)
    existing = {p.stem for p in paths.WIKI.rglob("*.md")}
    slug, i = base, 2
    while slug in existing:
        slug, i = f"{base}-{i}", i + 1
    f = d / f"{slug}.md"
    hub_fm = f"hub: {hub_slug}\n" if hub_slug else ""
    hub_body = f"\nFiled under [[{hub_slug}]].\n" if hub_slug else ""
    is_image = dest.suffix.lower() in IMAGE_SUFFIXES
    # images stay binaries in ~/files (the wiki is plaintext-only), but the shadow note EMBEDS them so
    # an editor that resolves the path previews inline; other files get a plain reference.
    asset = (f"![{title}]({dest})\n" if is_image
             else f"Shadow note for a binary in `~/files` (not stored in git). File: `{dest}`.\n")
    kind_fm = "kind: image\n" if is_image else ""
    f.write_text(f"---\ntype: file\n{kind_fm}title: {title}\nstatus: active\nsource: ingest\n"
                 f"ingested: {paths.today()}\npath: {dest}\nsha256: {sha}\n{hub_fm}tags: []\n---\n# {title}\n\n"
                 f"{asset}{hub_body}", encoding="utf-8")
    return f


def _parse_route(rest):
    """Return (dest_dir, hub_slug, hub_note, leftover_args). Exits via message on a bad hub."""
    hub_kind = hub_slug = None
    research = False
    leftover = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in HUB_KIND and i + 1 < len(rest):
            hub_kind, hub_slug = HUB_KIND[a], rest[i + 1]; i += 2; continue
        if a == "--research":
            research = True; i += 1; continue
        leftover.append(a); i += 1

    if hub_slug:
        dest_dir = paths.FILES_ROOT / hub_kind / hub_slug / "in"
        hub_note = _hub_note(hub_slug)
        return dest_dir, hub_slug, hub_note, leftover
    if research:
        return paths.FILES_ROOT / "research", None, None, leftover
    return paths.FILES_ROOT / "inbox", None, None, leftover


def cmd_ingest(argv, dry=False):
    dest_dir, hub_slug, hub_note, rest = _parse_route(argv)
    if hub_slug and hub_note is None:
        output.fail(output.EXIT_UNEXPECTED,
                    f"{YEL}no wiki hub '{hub_slug}'{RESET} — create it first (e.g. `ops new client {hub_slug}`), "
                    f"then re-run. Nothing ingested.", verb="files")

    if rest:
        sources = [Path(rest[0]).expanduser()]
    else:
        sources = [p for p in paths.INBOX.iterdir()
                   if p.is_file() and p.suffix.lower() not in TEXT_SUFFIXES and p.name != ".gitkeep"] \
            if paths.INBOX.exists() else []
    if not sources:
        return output.emit_rows([], "files",
                                human=lambda _: "nothing to ingest (drop a binary into inbox/, or pass a path).",
                                header={"filed": 0, "proposed": 0, "linked": 0, "deduped": 0, "dry_run": dry})

    events, rows = [], []
    filed = proposed = linked = deduped = 0
    for src in sources:
        if not src.exists():
            events.append(f"  not found: {src}"); continue
        if _is_personal(src.name):
            events.append(f"  {YEL}PROPOSE iCloud{RESET}: '{src.name}' looks personal/legal — move it yourself to "
                          f"iCloud (the wall forbids any verb writing there). Left in place.")
            rows.append({"action": "propose", "name": src.name})
            proposed += 1
            continue

        sha = _sha256(src)
        dup = _find_by_hash(sha)
        if dup:
            events.append(f"  {DIM}duplicate{RESET}: '{src.name}' == {dup.stem} (same bytes) — not copied again.")
            rows.append({"action": "dedup", "name": src.name, "slug": dup.stem})
            deduped += 1
            if hub_note and (dry or _link_into_hub(hub_note, dup.stem, paths.fm_field(dup, "title") or dup.stem)):
                events.append(f"    {GREEN}linked{RESET} -> [[{hub_slug}]]"); linked += 1
            continue

        where = dest_dir.relative_to(paths.FILES_ROOT)
        if dry:
            events.append(f"  {GREEN}would file{RESET}: {src.name} -> ~/files/{where}/")
            rows.append({"action": "file", "name": src.name, "dest": f"~/files/{where}/"})
            filed += 1
            if hub_note:
                events.append(f"    {GREEN}would link{RESET} -> [[{hub_slug}]]"); linked += 1
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        i = 2
        while dest.exists():
            dest = dest_dir / f"{src.stem}-{i}{src.suffix}"; i += 1
        shutil.move(str(src), str(dest))
        note = _shadow(dest, src.name, sha, hub_slug)
        paths.append_journal(f"files ingest {src.name} -> {dest}" + (f" [[{hub_slug}]]" if hub_slug else ""))
        events.append(f"  {GREEN}filed{RESET}: {src.name} -> ~/files/{where}/  ({note.relative_to(paths.OPS_HOME)})")
        rows.append({"action": "file", "name": src.name, "dest": f"~/files/{where}/",
                     "slug": note.stem})
        filed += 1
        if hub_note and _link_into_hub(hub_note, note.stem, src.name):
            events.append(f"    {GREEN}linked{RESET} -> [[{hub_slug}]]"); linked += 1

    def render(_):
        for e in events:
            print(e)
        tail = f", {linked} linked" if hub_slug else ""
        tail += f", {deduped} de-duped" if deduped else ""
        print(f"\nfiles ingest: {filed} filed{tail}, {proposed} proposed for iCloud (left in place)"
              + (" (dry run)" if dry else ""))

    return output.emit_rows(rows, "files", human=render,
                            header={"filed": filed, "proposed": proposed, "linked": linked,
                                    "deduped": deduped, "dry_run": dry})


def cmd_link(argv):
    if len(argv) < 2:
        output.fail(output.EXIT_USAGE, "usage: ops files link <file-slug> <hub-slug>", verb="files")
    file_slug, hub_slug = argv[0], argv[1]
    shadow = paths.WIKI / "files" / f"{file_slug}.md"
    if not shadow.exists():
        output.fail(output.EXIT_UNEXPECTED,
                    f"no shadow note: wiki/files/{file_slug}.md (see `ops files list`)", verb="files")
    hub = _hub_note(hub_slug)
    if hub is None:
        output.fail(output.EXIT_UNEXPECTED, f"no wiki hub '{hub_slug}'", verb="files")
    title = paths.fm_field(shadow, "title") or file_slug
    changed = _link_into_hub(hub, file_slug, title)
    # make the back-reference explicit in the shadow note too
    stext = shadow.read_text(encoding="utf-8")
    if f"[[{hub_slug}]]" not in stext:
        shadow.write_text(stext.rstrip("\n") + f"\n\nFiled under [[{hub_slug}]].\n", encoding="utf-8")
    data = {"file": file_slug, "hub": hub_slug, "already_linked": not changed}
    return output.emit(data, "files", human=lambda _:
                       f"{GREEN}linked{RESET} [[{file_slug}]] -> [[{hub_slug}]]"
                       + ("" if changed else " (already linked)"))


def cmd_list(argv):
    hub_filter = None
    if "--hub" in argv:
        j = argv.index("--hub")
        hub_filter = argv[j + 1] if j + 1 < len(argv) else None
    rows = []
    for p in _shadows():
        hub = paths.fm_field(p, "hub")
        if hub_filter and hub != hub_filter:
            continue
        rows.append({"slug": p.stem, "title": paths.fm_field(p, "title") or p.stem,
                     "hub": hub, "path": paths.fm_field(p, "path")})

    def render(rs):
        if not rs:
            return "no assets yet (ingest one: `ops files ingest <path> --client <slug>`)."
        out = [f"{len(rs)} asset(s)" + (f" under [[{hub_filter}]]" if hub_filter else "") + ":"]
        for r in rs:
            tag = f"  {CYAN}[[{r['hub']}]]{RESET}" if r["hub"] else f"  {DIM}(unlinked){RESET}"
            out.append(f"  {r['slug']:<28} {DIM}{r['title'][:40]:<40}{RESET}{tag}")
        return "\n".join(out)

    return output.emit_rows(rows, "files", human=render, header={"hub": hub_filter})


def cmd_open(argv):
    if not argv:
        output.fail(output.EXIT_USAGE, "usage: ops files open <slug>", verb="files")
    note = paths.WIKI / "files" / f"{argv[0]}.md"
    if not note.exists():
        output.fail(output.EXIT_UNEXPECTED, f"no shadow note: wiki/files/{argv[0]}.md", verb="files")
    target = paths.fm_field(note, "path")
    if not target:
        output.fail(output.EXIT_UNEXPECTED, "shadow note has no path:", verb="files")

    def render(_):
        print(target)
        if not os.environ.get("OPS_NO_OPEN") and sys.platform == "darwin" and Path(target).exists():
            subprocess.run(["open", "-R", target], check=False)

    return output.emit({"slug": argv[0], "path": target}, "files", human=render)


def main(argv):
    _, argv = output.parse_argv(argv)
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    action = argv[0] if argv else "ingest"
    if action == "ingest":
        return cmd_ingest(argv[1:], dry)
    if action == "link":
        return cmd_link(argv[1:])
    if action == "list":
        return cmd_list(argv[1:])
    if action == "open":
        return cmd_open(argv[1:])
    output.fail(output.EXIT_USAGE,
                "usage: ops files ingest [<path>] [--client|--project|--area <slug> | --research] | "
                "link <file> <hub> | list [--hub <slug>] | open <slug>", verb="files")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
