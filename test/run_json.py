#!/usr/bin/env python3
"""
run_json.py — the machine-contract suite (proposal Part 1.1/1.2/0.5), offline + stdlib only:
  1. every non-hidden verb's cmd.json declares an `output` block and `hints` (the I/O contract lives
     in ops.json, so a third party never imports lib);
  2. the declared `dry_run` verbs actually declare it;
  3. ops.json v2 top-level shape (schema/ops_version/api_version/json_envelope/capabilities);
  4. `--json` round-trips: each read-class verb, run against a fixture world, emits the frozen
     envelope and every field its cmd.json `output` block declares;
  5. `--dry-run` on a mutating verb emits a valid envelope and writes NOTHING.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "bin"
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def run(env, verb, *args):
    return subprocess.run([sys.executable, str(BIN / verb / "run.py"), *args],
                          capture_output=True, text=True, env=env)


def _cmd(verb) -> dict:
    return json.loads((BIN / verb / "cmd.json").read_text(encoding="utf-8"))


def parse_ndjson(out: str):
    return [json.loads(ln) for ln in out.splitlines() if ln.strip()]


def validate_scalar(name, r, verb, fields):
    try:
        objs = parse_ndjson(r.stdout)
    except Exception as e:
        check(f"{name}: valid JSON", False, f"{e}: {r.stdout[:160]}{r.stderr[:160]}"); return
    if len(objs) != 1:
        check(f"{name}: single envelope", False, r.stdout[:200]); return
    e = objs[0]
    ok = (e.get("ops_json") == 1 and e.get("ok") is True and e.get("verb") == verb
          and isinstance(e.get("data"), dict))
    check(f"{name}: scalar envelope", ok, str(e)[:200])
    data = e.get("data", {})
    missing = [f for f in fields if f not in data]
    check(f"{name}: declared fields round-trip", not missing, f"missing {missing}")


def validate_rows(name, r, verb, fields, check_fields=True):
    try:
        objs = parse_ndjson(r.stdout)
    except Exception as e:
        check(f"{name}: valid NDJSON", False, f"{e}: {r.stdout[:160]}{r.stderr[:160]}"); return
    if not objs:
        check(f"{name}: has header", False, r.stdout[:200]); return
    head, rows = objs[0], objs[1:]
    ok = (head.get("ops_json") == 1 and head.get("ok") is True and head.get("verb") == verb
          and head.get("count") == len(rows))
    check(f"{name}: rows header + count", ok, str(head)[:200])
    if check_fields and rows:
        missing = [f for f in fields if f not in rows[0]]
        check(f"{name}: declared row fields round-trip", not missing, f"missing {missing} in {rows[0]}")


def mkrepo(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=False)
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=False)
    subprocess.run(["git", "-C", str(path), "-c", "user.email=t@t", "-c", "user.name=t",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "init"], check=False,
                   capture_output=True)


def main() -> int:
    # --- static contract: every non-hidden verb declares output + hints (+ dry_run where required) ---
    DRY = {"capture", "task", "wiki", "triage", "files", "archive", "sweep",
           "invoice", "index", "consolidate", "job", "new", "bookmark"}
    verbs = []
    for cj in sorted(BIN.glob("*/cmd.json")):
        d = json.loads(cj.read_text(encoding="utf-8"))
        if d.get("hidden"):
            continue
        verbs.append(d["verb"])
        out = d.get("output")
        check(f"{d['verb']}: cmd.json has output block",
              isinstance(out, dict) and isinstance(out.get("fields"), dict) and out.get("mode") in ("scalar", "rows"),
              str(out))
        check(f"{d['verb']}: cmd.json has hints", bool(d.get("hints")))
    for v in sorted(DRY):
        check(f"{v}: declares dry_run", _cmd(v).get("dry_run") is True)

    # --- ops.json v2 top-level shape ---
    with tempfile.TemporaryDirectory() as td:
        env0 = {**os.environ, "OPS_HOME": td, "OPS_ROOTS_HOME": td}
        run(env0, "help")  # regenerates ops.json into the temp OPS_HOME
        doc = json.loads((Path(td) / "ops.json").read_text(encoding="utf-8"))
    for key in ("schema", "ops_version", "api_version", "json_envelope", "capabilities", "verbs"):
        check(f"ops.json v2 top-level: {key}", key in doc)
    check("ops.json schema is ops.json/2", doc.get("schema") == "ops.json/2")
    caps = doc.get("capabilities", {})
    check("capabilities keys present", all(k in caps for k in ("vectors", "rerank", "agent", "plugins")))
    check("every verb tagged source=engine", all(v.get("source") == "engine" for v in doc.get("verbs", [])))

    # --- live --json round-trip against a seeded fixture world ---
    with tempfile.TemporaryDirectory() as td:
        ops = Path(td) / "ops"
        roots = Path(td) / "roots"
        ops.mkdir(); roots.mkdir()
        env = {**os.environ, "OPS_HOME": str(ops), "OPS_ROOTS_HOME": str(roots),
               "OPS_NO_OPEN": "1"}
        # seed content
        run(env, "wiki", "new", "note", "Alpha Note About Testing")
        run(env, "task", "add", "Fix the alpha widget")
        png = Path(td) / "pic.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        run(env, "files", "ingest", str(png))
        # jobs registry (user-owned; copy the repo's for the fixture)
        (ops / "jobs").mkdir(parents=True, exist_ok=True)
        (ops / "jobs" / "registry.json").write_text(
            (REPO / "jobs" / "registry.json").read_text(encoding="utf-8"), encoding="utf-8")
        mkrepo(roots / "work" / "labs" / "demo")
        run(env, "index")

        # canonical read-class round-trips (verb, args) validated against their cmd.json output block
        canon = [("backup", []), ("status", []), ("help", []), ("search", ["alpha"]),
                 ("task", ["list"]), ("wiki", ["list"]), ("files", ["list"]),
                 ("repo", ["health"]), ("job", ["list"]), ("doctor", [])]
        for verb, args in canon:
            r = run(env, verb, *args, "--json")
            block = _cmd(verb)["output"]
            fields = list(block["fields"])
            if block["mode"] == "scalar":
                validate_scalar(f"{verb} {' '.join(args)}".strip(), r, verb, fields)
            else:
                validate_rows(f"{verb} {' '.join(args)}".strip(), r, verb, fields)

        # other read sub-actions: envelope must be well-formed even if row shape differs from the block
        for verb, args in [("wiki", ["stale"]), ("wiki", ["orphans"])]:
            r = run(env, verb, *args, "--json")
            validate_rows(f"{verb} {' '.join(args)}".strip(), r, verb, [], check_fields=False)

        # OPS_JSON env toggles JSON too (no --json flag)
        r = run({**env, "OPS_JSON": "1"}, "status")
        validate_scalar("status via OPS_JSON=1", r, "status", list(_cmd("status")["output"]["fields"]))

        # --dry-run emits a valid envelope AND writes nothing
        before = len(list((ops / "tasks" / "active").glob("T-*.md")))
        r = run(env, "task", "add", "Should not persist", "--dry-run", "--json")
        objs = parse_ndjson(r.stdout) if r.stdout.strip() else []
        check("task add --dry-run: ok envelope",
              len(objs) == 1 and objs[0].get("ok") is True and objs[0]["data"].get("dry_run") is True, r.stdout[:200])
        after = len(list((ops / "tasks" / "active").glob("T-*.md")))
        check("task add --dry-run writes nothing", before == after, f"{before} -> {after}")

        inbox_before = len(list((ops / "inbox").glob("cap-*.md")))
        r = run(env, "capture", "ephemeral", "--dry-run", "--json")
        check("capture --dry-run writes nothing",
              len(list((ops / "inbox").glob("cap-*.md"))) == inbox_before, r.stdout[:160])

        # error path: fail() emits the error envelope + protocol exit code under --json
        r = run(env, "search", "--json")  # empty query -> usage (2)
        errs = parse_ndjson(r.stdout) if r.stdout.strip() else []
        check("search usage error: JSON error envelope",
              r.returncode == 2 and errs and errs[0].get("ok") is False and errs[0]["error"].get("code") == 2,
              f"rc={r.returncode} {r.stdout[:160]}")

        # human rendering unchanged when --json is absent (spot check)
        r = run(env, "task", "list")
        check("human mode still renders (no envelope)", "active/" in r.stdout and "ops_json" not in r.stdout, r.stdout[:160])

    print(f"{BOLD}Machine contract: --json envelope + ops.json v2 + dry-run — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<48}" + (f" {DIM}{detail.strip()[:80]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
