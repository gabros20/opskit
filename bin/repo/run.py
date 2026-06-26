#!/usr/bin/env python3
"""
ops repo health | clone <slug> [--kind k] | clone --all | adopt <path> --kind <k> | nuke-modules --stale <days>
— the ~/work fleet manager (§4.1, §12.3). health scans every repo (dirty/unpushed/stale); clone
restores repos from their wiki hub's `remote:`; adopt moves an already-cloned repo into the routing
tree + writes its hub; nuke-modules reclaims node_modules untouched N+ days (the §15 job — regenerable).
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

GREEN, RED, YEL, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
DAY = 86400
STALE = 90


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout


def _find_repos():
    if not paths.WORK_ROOT.exists():
        return []
    repos = []
    for g in paths.WORK_ROOT.rglob(".git"):
        repo = g.parent
        if ".worktrees" in repo.parts or "archive" in repo.parts:
            continue
        repos.append(repo)
    return sorted(repos)


def _hub(slug, name, remote=""):
    d = paths.WIKI / "projects"; d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.md"
    if not f.exists():
        f.write_text(f"---\ntype: project\ntitle: {name}\nstatus: active\ncreated: {paths.today()}\n"
                     f"updated: {paths.today()}\ntags: []\naliases: []\nremote: {remote}\n---\n# {name}\n\n"
                     f"## Timeline\n- {paths.today()} adopted via `ops repo adopt`\n", encoding="utf-8")
    return f


def cmd_health():
    repos = _find_repos()
    if not repos:
        print("no repos under ~/work yet."); return 0
    risky = 0
    print(f"{len(repos)} repo(s) under {paths.WORK_ROOT}:\n")
    for r in repos:
        rel = r.relative_to(paths.WORK_ROOT)
        dirty = len([x for x in _git(r, "status", "--porcelain").splitlines() if x.strip()])
        up = _git(r, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
        ahead = 0
        if up:
            o = _git(r, "rev-list", "--count", "@{u}..HEAD").strip(); ahead = int(o) if o.isdigit() else 0
        ct = _git(r, "log", "-1", "--format=%ct").strip()
        age = int((time.time() - int(ct)) / DAY) if ct.isdigit() else -1
        flags = []
        if dirty: flags.append(f"{dirty} dirty")
        if not up: flags.append("no remote")
        elif ahead: flags.append(f"{ahead} unpushed")
        if age >= STALE: flags.append(f"stale {age}d")
        bad = bool(flags); risky += bad
        mark = f"{RED}●{RESET}" if bad else f"{GREEN}●{RESET}"
        print(f"  {mark} {str(rel):<34} {DIM}{', '.join(flags) if flags else 'clean'}{RESET}")
    print(f"\nrepo health: {len(repos)-risky} clean, {risky} need attention")
    return 1 if risky else 0


def cmd_clone(argv):
    if argv and argv[0] == "--all":
        hubs = sorted((paths.WIKI / "projects").glob("*.md")) if (paths.WIKI / "projects").exists() else []
        n = 0
        for h in hubs:
            remote = paths.fm_field(h, "remote")
            if remote:
                _clone_one(h.stem, remote, "labs"); n += 1
        print(f"\ncloned {n} repo(s) with a remote set")
        return 0
    if not argv:
        print("usage: ops repo clone <slug> [--kind k] | clone --all", file=sys.stderr); return 2
    slug = argv[0]
    kind = argv[argv.index("--kind") + 1] if "--kind" in argv else "labs"
    hub = paths.WIKI / "projects" / f"{slug}.md"
    if not hub.exists():
        print(f"no project hub: wiki/projects/{slug}.md", file=sys.stderr); return 1
    remote = paths.fm_field(hub, "remote")
    if not remote:
        print(f"hub '{slug}' has no remote: set", file=sys.stderr); return 1
    return _clone_one(slug, remote, kind)


def _clone_one(slug, remote, kind):
    dest = paths.WORK_ROOT / kind / slug
    if dest.exists():
        print(f"  skip {slug}: already at {dest}"); return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "-q", remote, str(dest)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {RED}clone failed {slug}: {r.stderr.strip()}{RESET}", file=sys.stderr); return 1
    print(f"  cloned {slug} -> {dest.relative_to(paths.WORK_ROOT)}")
    return 0


def cmd_adopt(argv):
    if not argv or "--kind" not in argv:
        print("usage: ops repo adopt <path> --kind <products|labs|tools>", file=sys.stderr); return 2
    src = Path(argv[0]).expanduser().resolve()
    kind = argv[argv.index("--kind") + 1]
    if kind not in paths.WORK_KINDS:
        print(f"--kind must be one of {paths.WORK_KINDS}", file=sys.stderr); return 2
    if not (src / ".git").is_dir():
        print(f"not a git repo: {src}", file=sys.stderr); return 1
    slug = paths.slugify(src.name)
    dest = paths.WORK_ROOT / kind / slug
    if dest.exists():
        print(f"destination exists: {dest}", file=sys.stderr); return 1
    remote = _git(src, "remote", "get-url", "origin").strip()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    hub = _hub(slug, src.name, remote)
    paths.append_journal(f"repo adopt {slug} -> {kind}")
    print(f"adopted {src.name} -> {dest.relative_to(paths.WORK_ROOT)}")
    print(f"  wiki hub: {hub.relative_to(paths.OPS_HOME)}" + (f"  (remote: {remote})" if remote else ""))
    return 0


def cmd_nuke(argv):
    days = int(argv[argv.index("--stale") + 1]) if "--stale" in argv else 30
    if not paths.WORK_ROOT.exists():
        print("no ~/work yet."); return 0
    freed = 0
    for nm in paths.WORK_ROOT.rglob("node_modules"):
        if not nm.is_dir() or list(nm.parts).count("node_modules") > 1:
            continue  # skip nested node_modules
        if (time.time() - nm.stat().st_mtime) / DAY >= days:
            print(f"  removed: {nm.relative_to(paths.WORK_ROOT)} (untouched {int((time.time()-nm.stat().st_mtime)/DAY)}d)")
            shutil.rmtree(nm); freed += 1
    print(f"\nnuke-modules: removed {freed} node_modules dir(s) untouched {days}+ days (regenerable)")
    return 0


def main(argv):
    action = argv[0] if argv else "health"
    rest = argv[1:]
    if action == "health":
        return cmd_health()
    if action == "clone":
        return cmd_clone(rest)
    if action == "adopt":
        return cmd_adopt(rest)
    if action == "nuke-modules":
        return cmd_nuke(rest)
    print("usage: ops repo health | clone <slug>|--all | adopt <path> --kind <k> | nuke-modules --stale <days>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
