#!/usr/bin/env python3
"""
ops archive <slug> — retire a dead ~/work repo (§4.1, §14). git-bundles the WHOLE repo (all history,
one file) into ~/work/archive/<year>/<slug>.bundle, marks its wiki hub status: archived, and removes
the working tree. The bundle is a complete, restorable repo (`git clone <bundle>`), so nothing is lost.
"""
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402


def _find_repo(slug: str):
    if not paths.WORK_ROOT.exists():
        return None
    for g in paths.WORK_ROOT.rglob(".git"):
        repo = g.parent
        if "archive" in repo.parts or ".worktrees" in repo.parts:
            continue
        if repo.name == slug:
            return repo
    return None


def main(argv):
    if not argv:
        print("usage: ops archive <slug>", file=sys.stderr); return 2
    slug = argv[0]
    repo = _find_repo(slug)
    if not repo:
        print(f"no ~/work repo named '{slug}'", file=sys.stderr); return 1

    year = str(date.today().year)
    dest_dir = paths.WORK_ROOT / "archive" / year
    dest_dir.mkdir(parents=True, exist_ok=True)
    bundle = dest_dir / f"{slug}.bundle"
    r = subprocess.run(["git", "-C", str(repo), "bundle", "create", str(bundle), "--all"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"bundle failed: {r.stderr.strip()}", file=sys.stderr); return 1

    hub = paths.WIKI / "projects" / f"{slug}.md"
    if hub.exists():
        import re
        t = hub.read_text(encoding="utf-8")
        t = re.sub(r"(?m)^status:.*$", "status: archived", t, count=1)
        t = re.sub(r"(?m)^updated:.*$", f"updated: {paths.today()}", t, count=1)
        if "## Timeline" in t:
            t = t.replace("## Timeline", f"## Timeline\n- {paths.today()} archived → {bundle}", 1)
        hub.write_text(t, encoding="utf-8")

    shutil.rmtree(repo)
    paths.append_journal(f"archived {slug} -> {bundle}")
    print(f"archived '{slug}':")
    print(f"  bundle:  {bundle}  (restore: git clone {bundle} <dir>)")
    print(f"  working tree removed; wiki hub marked status: archived" if hub.exists()
          else "  working tree removed (no wiki hub found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
