#!/usr/bin/env python3
"""run_completion.py — Tier-1 terminal ergonomics: the __complete helper (tab-completion brain),
the zsh completion file, the built-in Markdown renderer, and `wiki open`/`wiki edit`. Offline."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, cond, bool(cond) and "" or detail))


def run(home, verb, *args, env_extra=None, stdin=None):
    env = {**os.environ, "OPS_HOME": str(home)}
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(REPO / "bin" / verb / "run.py"), *args],
                          input=stdin, capture_output=True, text=True, env=env)


def comp(home, *prior, env_extra=None):
    """Run __complete; return the list of candidate values (before the ':' description)."""
    r = run(home, "__complete", *prior, env_extra=env_extra)
    vals = [ln.split(":", 1)[0] for ln in r.stdout.splitlines() if ln.strip()]
    return vals, r


def note(home, rel, typ, title, body=""):
    p = home / "wiki" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntype: {typ}\ntitle: {title}\nstatus: active\ncreated: 2026-01-01\n"
                 f"updated: 2026-01-01\ntags: []\n---\n# {title}\n\n{body}\n", encoding="utf-8")


def task(home, tid, status, title):
    p = home / "tasks" / status / f"{tid}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntype: task\nid: {tid}\nstatus: {status}\n---\n# {title}\n", encoding="utf-8")


def main() -> int:
    # ---- __complete: the completion brain ----
    with tempfile.TemporaryDirectory() as td:
        h = Path(td)
        note(h, "notes/alpha.md", "note", "Alpha", "see [[beta]]")
        note(h, "notes/beta.md", "note", "Beta")
        task(h, "T-20260101-01", "active", "Fix the webhook")
        task(h, "T-20260101-02", "waiting", "Await reply")

        verbs, r = comp(h)
        check("__complete (no args) lists verbs", "wiki" in verbs and "task" in verbs and "search" in verbs, r.stdout)
        check("__complete hides itself (__complete not a candidate)", "__complete" not in verbs, str(verbs))
        # no drift: every visible verb in ops.json is offered
        manifest = json.loads((REPO / "ops.json").read_text())
        surface = {v["verb"] for v in manifest["verbs"]}
        check("__complete covers every verb in ops.json", surface.issubset(set(verbs)),
              str(sorted(surface - set(verbs))))
        check("ops.json itself excludes __complete", "__complete" not in surface, str(surface))

        subs, _ = comp(h, "wiki")
        check("__complete wiki → subcommands", {"open", "edit", "new", "backlinks"} <= set(subs), str(subs))
        slugs, _ = comp(h, "wiki", "open")
        check("__complete wiki open → live note slugs", {"alpha", "beta"} <= set(slugs), str(slugs))
        eslugs, _ = comp(h, "wiki", "edit")
        check("__complete wiki edit → live note slugs", "alpha" in eslugs, str(eslugs))
        types, _ = comp(h, "wiki", "new")
        check("__complete wiki new → note types", {"note", "project", "client"} <= set(types), str(types))
        tsubs, _ = comp(h, "task")
        check("__complete task → subcommands", {"add", "done", "show", "move"} <= set(tsubs), str(tsubs))
        tids, _ = comp(h, "task", "done")
        check("__complete task done → live task ids", "T-20260101-01" in tids, str(tids))
        mvst, _ = comp(h, "task", "move", "T-20260101-01")
        check("__complete task move <id> → statuses", {"active", "waiting", "done"} <= set(mvst), str(mvst))
        unknown, _ = comp(h, "definitelynotaverb")
        check("__complete unknown verb → no candidates", unknown == [], str(unknown))

    # ---- guardrail lets __complete through the real dispatcher (risk: read) ----
    d = subprocess.run([str(REPO / "ops"), "__complete", "wiki"], capture_output=True, text=True)
    check("dispatcher runs __complete (guardrail: read)", d.returncode == 0 and "open" in d.stdout, d.stdout + d.stderr)

    # ---- the built-in Markdown renderer ----
    # load bin/lib/render.py by path (test/lib/ shadows the name 'lib' on sys.path)
    import importlib.util
    spec = importlib.util.spec_from_file_location("ops_render", REPO / "bin" / "lib" / "render.py")
    render = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(render)
    out = render.render_markdown("---\ntype: note\n---\n# Title\n\n**bold** [[link]] `code`\n")
    check("renderer emits ANSI for a heading", "\033[1m" in out and "Title" in out and "#" not in out.split("Title")[0][-3:], out[:60])
    check("renderer dims frontmatter", "\033[2mtype: note\033[0m" in out, out[:80])
    check("renderer accents [[wikilinks]]", "[[link]]" in out and "\033[36m" in out, out)

    # ---- wiki open: raw when piped (tests + pipelines get plain Markdown) ----
    with tempfile.TemporaryDirectory() as td:
        h = Path(td)
        note(h, "notes/beta.md", "note", "Beta", "body text")
        r = run(h, "wiki", "open", "beta")
        check("wiki open (piped) is raw Markdown", "# Beta" in r.stdout and "\033[" not in r.stdout, r.stdout)
        r = run(h, "wiki", "open", "beta", env_extra={"OPS_RENDER": "raw"})
        check("wiki open OPS_RENDER=raw stays raw", "# Beta" in r.stdout, r.stdout)
        r = run(h, "wiki", "open", "nope")
        check("wiki open unknown slug → error", r.returncode == 1 and "no note" in r.stderr, r.stderr)
        # wiki edit shells out to $EDITOR on the right file
        r = run(h, "wiki", "edit", "beta", env_extra={"OPS_EDITOR": "echo EDIT"})
        check("wiki edit opens $EDITOR on the note", r.returncode == 0
              and "EDIT" in r.stdout and str(h / "wiki" / "notes" / "beta.md") in r.stdout, r.stdout + r.stderr)
        r = run(h, "wiki", "edit", "nope")
        check("wiki edit unknown slug → error", r.returncode == 1, r.stderr)

    # ---- the shipped zsh completion file ----
    comp_file = REPO / "script" / "completions" / "_ops"
    check("zsh completion file exists", comp_file.exists())
    if comp_file.exists():
        txt = comp_file.read_text()
        check("completion declares #compdef ops", txt.splitlines()[0].strip() == "#compdef ops", txt[:40])
        check("completion delegates to `ops __complete`", "ops __complete" in txt)
        if shutil.which("zsh"):
            z = subprocess.run(["zsh", "-n", str(comp_file)], capture_output=True, text=True)
            check("zsh parses the completion file", z.returncode == 0, z.stderr)
        else:
            check("zsh parses the completion file (skipped: no zsh)", True)

    print(f"{BOLD}Terminal ergonomics (completion, renderer, wiki open/edit) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<52}" + (f" {DIM}{detail.strip()[:70]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
