#!/usr/bin/env python3
"""
ops backup — verify ~/ops is committed and pushed; nag (exit 1) if anything is at risk (§14).
Read-only: it NEVER commits or pushes for you (§3 — transmit is the human's call). It tells you
exactly what to run. Exit 0 only when the working tree is clean AND nothing is unpushed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

GREEN, RED, YEL, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def main(argv):
    if not (paths.OPS_HOME / ".git").exists():
        print(f"{YEL}~/ops is not a git repo — your knowledge is NOT versioned. run: git init{RESET}")
        return 1

    dirty = [ln for ln in paths.git("status", "--porcelain").splitlines() if ln.strip()]
    branch = (paths.git("rev-parse", "--abbrev-ref", "HEAD").strip() or "?")
    upstream = paths.git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    ahead = 0
    if upstream:
        out = paths.git("rev-list", "--count", "@{u}..HEAD").strip()
        ahead = int(out) if out.isdigit() else 0

    risk = bool(dirty) or (not upstream) or ahead > 0
    print(f"ops repo: {branch}" + (f" → {upstream}" if upstream else " (no remote tracking)"))
    if dirty:
        print(f"  {RED}● {len(dirty)} uncommitted change(s){RESET} — run: git add -A && git commit")
        for ln in dirty[:8]:
            print(f"      {ln}")
    else:
        print(f"  {GREEN}● working tree clean{RESET}")
    if not upstream:
        print(f"  {YEL}● no upstream set{RESET} — your commits live only on this machine "
              f"(set one: git push -u origin {branch})")
    elif ahead:
        print(f"  {RED}● {ahead} commit(s) not pushed{RESET} — run: git push")
    else:
        print(f"  {GREEN}● pushed — remote is current{RESET}")

    print(f"\nbackup: {'AT RISK — act on the lines above' if risk else 'safe (committed + pushed)'}")
    return 1 if risk else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
