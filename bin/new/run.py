#!/usr/bin/env python3
"""
ops new project "<name>" [--kind labs|products|tools] | new client "<name>"
    | new verb <name> [--risk <class>] [--summary "<text>"]
— scaffold a unit of work (§4.1, §12.3) or a new command. A PROJECT gets a wiki hub AND a ~/work repo
scaffolded from templates/project-repo/ (git-initialized). A CLIENT gets a wiki hub AND a
~/files/clients/<slug>/ material tree. A VERB stamps out bin/<name>/{run.py,cmd.json} from
templates/verb/ (defaulting to confirm-class, per §5) and regenerates the manifest — turning "add a
verb" into a one-command, guardrailed act instead of hand-wiring the surface. Slugs are globally
unique and IDENTICAL across wiki ↔ ~/work ↔ ~/files (§2).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

TEMPLATE = paths.OPS_HOME / "templates" / "project-repo"
VERB_TEMPLATE = paths.OPS_HOME / "templates" / "verb"
BIN = Path(__file__).resolve().parents[1]           # verbs live with the CODE (bin/), not OPS_HOME
RISK_CLASSES = ("read", "safe_write", "draft_only", "confirm", "deny")


def _new_verb(rest):
    name = rest[0] if rest else ""
    risk, summary = "confirm", ""
    i = 1
    while i < len(rest):
        if rest[i] == "--risk" and i + 1 < len(rest):
            risk = rest[i + 1]; i += 2; continue
        if rest[i] == "--summary" and i + 1 < len(rest):
            summary = rest[i + 1]; i += 2; continue
        i += 1
    if not re.fullmatch(r"[a-z][a-z0-9-]*", name or ""):
        print("verb name must be lowercase [a-z0-9-], starting with a letter", file=sys.stderr); return 2
    if risk not in RISK_CLASSES:
        print(f"--risk must be one of {RISK_CLASSES}", file=sys.stderr); return 2
    dest = BIN / name
    if dest.exists():
        print(f"verb '{name}' already exists ({dest})", file=sys.stderr); return 1
    if not VERB_TEMPLATE.is_dir():
        print(f"missing template: {VERB_TEMPLATE}", file=sys.stderr); return 1
    shutil.copytree(VERB_TEMPLATE, dest)
    _fill(dest, {"{{name}}": name, "{{risk}}": risk,
                 "{{summary}}": summary or f"TODO: describe {name}"})
    from lib.manifest import write_manifest  # regenerate ops.json so `ops help` shows the new verb
    write_manifest()
    paths.append_journal(f"new verb: {name} (risk {risk})")
    print(f"scaffolded verb '{name}':")
    print(f"  code:  bin/{name}/run.py  (+ cmd.json, risk: {risk})")
    print(f"  next:  implement main() in bin/{name}/run.py, then `ops {name}`"
          + ("" if risk != "confirm" else "  (confirm-class → runs with --yes until you lower risk)"))
    return 0


def _all_slugs() -> set:
    return {p.stem for p in paths.WIKI.rglob("*.md")} if paths.WIKI.exists() else set()


def _hub(folder: str, typ: str, slug: str, name: str) -> Path:
    d = paths.WIKI / folder
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.md"
    f.write_text(f"---\ntype: {typ}\ntitle: {name}\nstatus: active\ncreated: {paths.today()}\n"
                 f"updated: {paths.today()}\ntags: []\naliases: []\nremote:\n---\n# {name}\n\n"
                 f"## Timeline\n- {paths.today()} created via `ops new {typ}`\n", encoding="utf-8")
    return f


def _fill(root: Path, repl: dict):
    for p in root.rglob("*"):
        if p.is_file():
            t = p.read_text(encoding="utf-8")
            for k, v in repl.items():
                t = t.replace(k, v)
            p.write_text(t, encoding="utf-8")


def main(argv):
    if len(argv) < 2 or argv[0] not in ("project", "client", "verb"):
        print('usage: ops new project "<name>" [--kind labs|products|tools] | new client "<name>"\n'
              '       | new verb <name> [--risk <class>] [--summary "<text>"]', file=sys.stderr); return 2
    if argv[0] == "verb":
        return _new_verb(argv[1:])
    typ = argv[0]
    kind = "labs"
    rest = []
    i = 1
    while i < len(argv):
        if argv[i] == "--kind" and i + 1 < len(argv):
            kind = argv[i + 1]; i += 2; continue
        rest.append(argv[i]); i += 1
    name = " ".join(rest).strip()
    if not name:
        print("a name is required", file=sys.stderr); return 2
    slug = paths.slugify(name)
    if slug in _all_slugs():
        print(f"slug '{slug}' already exists — slugs are unique (§10.1)", file=sys.stderr); return 1

    if typ == "client":
        hub = _hub("clients", "client", slug, name)
        tree = paths.FILES_ROOT / "clients" / slug
        for sub in ("in", "out", "work"):
            (tree / sub).mkdir(parents=True, exist_ok=True)
        paths.append_journal(f"new client: {slug}")
        print(f"created client '{name}':")
        print(f"  wiki hub:  {hub.relative_to(paths.OPS_HOME)}")
        print(f"  material:  {tree}/  (in/ = read-only originals, out/ = deliverables, work/ = drafts)")
        return 0

    # project
    if kind not in paths.WORK_KINDS:
        print(f"--kind must be one of {paths.WORK_KINDS}", file=sys.stderr); return 2
    if not TEMPLATE.is_dir():
        print(f"missing template: {TEMPLATE}", file=sys.stderr); return 1
    repo = paths.WORK_ROOT / kind / slug
    if repo.exists():
        print(f"repo already exists: {repo}", file=sys.stderr); return 1
    hub = _hub("projects", "project", slug, name)
    repo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, repo)
    _fill(repo, {"{{name}}": name, "{{slug}}": slug, "{{date}}": paths.today()})
    subprocess.run(["git", "init", "-q", str(repo)], check=False)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=False)
    subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false",
                    "commit", "-qm", f"scaffold {name} via ops new"], check=False,
                   capture_output=True)
    paths.append_journal(f"new project: {slug} ({kind})")
    print(f"created project '{name}':")
    print(f"  wiki hub:  {hub.relative_to(paths.OPS_HOME)}")
    print(f"  repo:      {repo}/  (git-initialized from templates/project-repo)")
    print(f"  next:      cd {repo} && script/setup   ·   set the hub's remote: field when you push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
