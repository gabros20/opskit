#!/usr/bin/env python3
"""
ops __complete [prior words...] — the brain behind tab-completion (Tier-1 ergonomics).

The shell passes the words already typed after `ops` (everything before the word being completed).
We print the candidates for the NEXT word, one per line, as `value:description` (the description is
optional and colon-free). The zsh function in script/completions/_ops feeds these to `_describe`.

Everything is derived live — verbs from the cmd.json sidecars, note slugs from wiki/, task ids from
tasks/ — so completion can never drift from the real surface or your real content. Hidden from
`ops help`/`ops.json` (cmd.json "hidden": true); risk `read`, so it runs freely under the guardrail.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import manifest, notetype, paths  # noqa: E402

WIKI_SUBS = {
    "open": "render a note in the terminal", "edit": "open a note in $EDITOR",
    "new": "create a structured note", "backlinks": "what links here",
    "stale": "notes untouched for N+ days", "orphans": "notes with no inbound links",
    "list": "counts by type",
}
TASK_SUBS = {"list": "list tasks", "add": "add a task", "show": "show one task",
             "move": "change status", "done": "mark done"}
TASK_STATUSES = {"inbox": "", "active": "", "waiting": "", "done": ""}
FILES_SUBS = {"ingest": "binary → ~/files + shadow note", "link": "attach an asset to a hub",
              "list": "the asset catalogue", "open": "reveal the file in Finder"}
NEW_SUBS = {"project": "wiki hub + ~/work repo", "client": "wiki hub + ~/files tree",
            "verb": "scaffold a new bin/<name>/ command"}


def _clean(s: str) -> str:
    return s.replace(":", " -").strip()


def _emit(pairs):
    for value, desc in pairs:
        print(f"{value}:{_clean(desc)}" if desc else value)


def _verbs():
    return [(c["verb"], c.get("summary", "")) for c in manifest.load_cmds()]  # hidden already filtered


def _note_slugs():
    if not paths.WIKI.exists():
        return []
    rows = []
    for p in sorted(paths.WIKI.rglob("*.md")):
        rows.append((p.stem, _clean(paths.fm_field(p, "type") or "note")))
    return rows


def _file_slugs():
    d = paths.WIKI / "files"
    return [(p.stem, _clean(paths.fm_field(p, "title") or p.stem)) for p in sorted(d.glob("*.md"))] if d.exists() else []


def _hub_slugs():
    rows = []
    for folder in ("clients", "projects", "areas"):
        d = paths.WIKI / folder
        if d.exists():
            rows += [(p.stem, folder[:-1]) for p in sorted(d.glob("*.md"))]
    return rows


def _task_ids():
    rows = []
    for st in ("active", "waiting", "inbox", "done"):
        d = paths.TASKS / st
        if not d.exists():
            continue
        for p in sorted(d.glob("T-*.md")):
            title = ""
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    title = line[2:].strip(); break
            rows.append((p.stem, f"{st} - {title}" if title else st))
    return rows


def main(prior: list[str]) -> int:
    if not prior:
        _emit(_verbs()); return 0
    verb = prior[0]

    if verb == "help":
        _emit(_verbs())
    elif verb == "wiki":
        if len(prior) == 1:
            _emit(WIKI_SUBS.items())
        elif prior[1] in ("open", "edit", "backlinks"):
            _emit(_note_slugs())
        elif prior[1] == "new" and len(prior) == 2:
            reg = notetype.load_types()
            _emit((t, "hub" if reg[t].get("hub") else reg[t].get("dir", "")) for t in sorted(reg))
    elif verb == "task":
        if len(prior) == 1:
            _emit(TASK_SUBS.items())
        elif prior[1] in ("show", "done"):
            _emit(_task_ids())
        elif prior[1] == "move":
            if len(prior) == 2:
                _emit(_task_ids())
            else:
                _emit(TASK_STATUSES.items())
    elif verb == "new":
        if len(prior) == 1:
            _emit(NEW_SUBS.items())
    elif verb == "files":
        if len(prior) == 1:
            _emit(FILES_SUBS.items())
        elif prior[1] in ("open", "link"):
            if len(prior) == 2:
                _emit(_file_slugs())
            elif prior[1] == "link":
                _emit(_hub_slugs())
    # everything else: no candidates (let the shell fall back to files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
