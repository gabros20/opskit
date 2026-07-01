#!/usr/bin/env python3
"""run_setup.py — exercises script/setup + script/update against a throwaway clone, with the roots
and PATH redirected into a temp dir (OPS_ROOTS_HOME / OPS_BIN_DIR) so real ~/ is never touched."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = "https://example.com/template.git"
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        vault, home, bindir, compdir = tmp / "ops", tmp / "home", tmp / "bin", tmp / "comp"
        cl = subprocess.run(["git", "clone", "-q", str(REPO), str(vault)], capture_output=True, text=True)
        if cl.returncode != 0:
            print("git clone failed:", cl.stderr); return 1
        env = {**os.environ, "OPS_ROOTS_HOME": str(home), "OPS_BIN_DIR": str(bindir),
               "OPS_COMP_DIR": str(compdir), "OPS_HOME": str(vault)}

        # dry-run changes nothing
        subprocess.run([str(vault / "script" / "setup"), "--lean", "--yes", "--dry-run",
                        "--upstream", UPSTREAM], capture_output=True, text=True, env=env)
        check("dry-run creates no symlink", not (bindir / "ops").exists())
        check("dry-run installs no completion", not (compdir / "_ops").exists())
        check("dry-run leaves test/ intact", bool(git(vault, "ls-files", "test/").stdout.strip()))

        # real run
        r = subprocess.run([str(vault / "script" / "setup"), "--lean", "--yes", "--no-commit",
                            "--upstream", UPSTREAM], capture_output=True, text=True, env=env)
        ok = r.returncode == 0
        check("setup completes", ok, r.stdout + r.stderr)
        check("ops put on PATH (symlink)", (bindir / "ops").is_symlink()
              and os.readlink(bindir / "ops") == str(vault / "ops"))
        check("zsh completion installed (symlink)", (compdir / "_ops").is_symlink()
              and os.readlink(compdir / "_ops") == str(vault / "script" / "completions" / "_ops"))
        check("sibling roots created", (home / "work").is_dir() and (home / "files").is_dir())
        check("sibling roots are NOT inside the repo", not (vault / "work").exists())
        check("upstream remote set", git(vault, "remote", "get-url", "upstream").stdout.strip() == UPSTREAM)
        check("upstream is fetch-only (push disabled)",
              "DISABLED" in git(vault, "remote", "get-url", "--push", "upstream").stdout)
        check("lean: test/ dropped from the vault", not git(vault, "ls-files", "test/").stdout.strip())
        check("lean: engine kept (bin/)", bool(git(vault, "ls-files", "bin/").stdout.strip()))
        check("lean: design docs kept", bool(git(vault, "ls-files", "docs/design/").stdout.strip()))
        check("doctor passes after setup", subprocess.run(
            [str(vault / "ops"), "doctor"], capture_output=True, text=True, env=env).returncode == 0)

        # update guards cleanly with no reachable remote
        u = subprocess.run([str(vault / "script" / "update"), "--remote", "nope"],
                           capture_output=True, text=True, env=env)
        check("update refuses a missing remote", u.returncode == 1 and "no 'nope' remote" in u.stderr, u.stderr)
        # engine manifest (path lines only, ignoring comments) excludes content + dev-only paths
        paths = [ln.strip() for ln in (vault / "script" / "engine.txt").read_text().splitlines()
                 if ln.strip() and not ln.startswith("#")]
        content = {"wiki", "tasks", "journal", "inbox", "test", "ref", "jobs"}
        check("engine manifest lists only framework paths",
              "bin" in paths and "skills" in paths and not (content & set(paths)), str(paths))

    print(f"{BOLD}Setup/update flow (script/setup, script/update) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<44}" + (f" {DIM}{detail.strip()[:80]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
