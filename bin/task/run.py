#!/usr/bin/env python3
"""ops task list|add "<title>"|show <id>|move <id> <status>|done <id> — the task system (§7)."""
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

STATUSES = ("inbox", "active", "waiting", "done")
TEMPLATE = """\
---
type: task
id: {id}
status: {status}
created: {created}
updated: {created}
source: manual
risk: green
why:
---
# {title}

## Intent
{title}

## Plan

## Outcome
<!-- COMPILED TRUTH: current best state, rewritten as it changes -->

## Log
<!-- TIMELINE: append-only; commands run, files changed -->
"""


def _find(task_id: str):
    for st in STATUSES:
        f = paths.TASKS / st / f"{task_id}.md"
        if f.exists():
            return f, st
    return None, None


def _next_id() -> str:
    day = date.today().strftime("%Y%m%d")
    n = 0
    for st in STATUSES:
        for f in (paths.TASKS / st).glob(f"T-{day}-*.md"):
            m = re.search(rf"T-{day}-(\d+)", f.stem)
            if m:
                n = max(n, int(m.group(1)))
    return f"T-{day}-{n + 1:02d}"


def _set_status(f: Path, status: str):
    txt = f.read_text(encoding="utf-8")
    txt = re.sub(r"(?m)^status:.*$", f"status: {status}", txt, count=1)
    txt = re.sub(r"(?m)^updated:.*$", f"updated: {paths.today()}", txt, count=1)
    f.write_text(txt, encoding="utf-8")


def cmd_list():
    any_ = False
    for st in ("active", "waiting"):
        files = sorted((paths.TASKS / st).glob("T-*.md"))
        if files:
            any_ = True
            print(f"{st}/")
            for f in files:
                print(f"  {f.stem}  {paths.title_of(f)}")
    if not any_:
        print("no active or waiting tasks. add one: ops task add \"<title>\"")


def main(argv):
    action = argv[0] if argv else "list"
    if action == "list":
        cmd_list()
    elif action == "add":
        title = " ".join(argv[1:]).strip()
        if not title:
            print('usage: ops task add "<title>"', file=sys.stderr); return 2
        tid = _next_id()
        d = paths.TASKS / "active"
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{tid}.md"
        f.write_text(TEMPLATE.format(id=tid, status="active", created=paths.today(), title=title),
                     encoding="utf-8")
        paths.append_journal(f"task added {tid}: {title[:60]}")
        print(f"added {tid} -> {f.relative_to(paths.OPS_HOME)}")
    elif action in ("show",):
        f, _ = _find(argv[1]) if len(argv) > 1 else (None, None)
        if not f:
            print(f"task not found: {argv[1] if len(argv)>1 else ''}", file=sys.stderr); return 1
        print(f.read_text(encoding="utf-8"))
    elif action in ("move", "done"):
        if action == "done":
            tid, status = (argv[1] if len(argv) > 1 else ""), "done"
        else:
            if len(argv) < 3:
                print("usage: ops task move <id> <status>", file=sys.stderr); return 2
            tid, status = argv[1], argv[2]
        if status not in STATUSES:
            print(f"status must be one of {STATUSES}", file=sys.stderr); return 2
        f, cur = _find(tid)
        if not f:
            print(f"task not found: {tid}", file=sys.stderr); return 1
        dest = paths.TASKS / status
        dest.mkdir(parents=True, exist_ok=True)
        new = dest / f.name
        f.rename(new)
        _set_status(new, status)
        paths.append_journal(f"task {tid} -> {status}")
        print(f"{tid}: {cur} -> {status}")
    else:
        print("usage: ops task list|add \"<title>\"|show <id>|move <id> <status>|done <id>", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
