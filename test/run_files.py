#!/usr/bin/env python3
"""run_files.py — exercises `ops files ingest` (work material filed + shadow note; personal/legal
proposed-not-moved) and `ops files open`, against temp ~/ops + ~/files."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))


def run(ops, roots, *args, extra=None):
    env = {**os.environ, "OPS_HOME": str(ops), "OPS_ROOTS_HOME": str(roots), **(extra or {})}
    return subprocess.run([sys.executable, str(REPO / "bin" / "files" / "run.py"), *args],
                          capture_output=True, text=True, env=env)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ops, roots = Path(td) / "ops", Path(td) / "home"
        (ops / "wiki").mkdir(parents=True); (ops / "journal").mkdir()
        inbox = ops / "inbox"; inbox.mkdir()
        (inbox / "acme-brief.pdf").write_bytes(b"%PDF work material")
        (inbox / "tax-return-2025.pdf").write_bytes(b"%PDF personal")
        (inbox / "cap-note.md").write_text("a text capture — not a binary")

        r = run(ops, roots, "ingest")
        filed = roots / "files" / "inbox" / "acme-brief.pdf"
        shadow = ops / "wiki" / "files" / "acme-brief.md"
        check("ingest files work material into ~/files", filed.exists(), r.stdout + r.stderr)
        check("ingest writes a shadow note", shadow.exists() and "path:" in shadow.read_text())
        check("ingest leaves personal/legal in place (iCloud proposed)",
              (inbox / "tax-return-2025.pdf").exists() and "PROPOSE iCloud" in r.stdout, r.stdout)
        check("ingest ignores text captures", (inbox / "cap-note.md").exists()
              and not (ops / "wiki" / "files" / "cap-note.md").exists())
        check("shadow note points at the moved file", str(filed) in shadow.read_text())

        r = run(ops, roots, "open", "acme-brief", extra={"OPS_NO_OPEN": "1"})
        check("files open resolves the path from the shadow note", str(filed) in r.stdout, r.stdout)

    print(f"{BOLD}files verb (binary-assets plane) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<46}" + (f" {DIM}{detail.strip()[:80]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
