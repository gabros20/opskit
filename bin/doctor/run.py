#!/usr/bin/env python3
"""
ops doctor [--init] — self-check (§14.4): tools, folder structure, manifest↔bin consistency, agent
adapters, no tracked secrets/binaries, index freshness. --init creates any missing skeleton folders.
Exit 1 if any check FAILs (WARN does not fail).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

GREEN, RED, YEL, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
BIN = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = ["wiki", "tasks/inbox", "tasks/active", "tasks/waiting", "tasks/done",
                 "journal", "inbox", "templates", "jobs", "skills", "bin"]
checks = []  # (level, msg)


def ok(m): checks.append(("ok", m))
def warn(m): checks.append(("warn", m))
def fail(m): checks.append(("fail", m))


def main(argv):
    init = "--init" in argv

    # 1. tools
    for t in ("git", "python3", "sqlite3"):
        (ok if shutil.which(t) else (warn if t == "sqlite3" else fail))(f"tool: {t} {'present' if shutil.which(t) else 'MISSING'}")
    for mod, why in (("lancedb", "stage-2 vectors"), ("fastembed", "stage-3 rerank")):
        try:
            __import__(mod); ok(f"optional: {mod} present ({why})")
        except Exception:
            warn(f"optional: {mod} not installed ({why} disabled)")

    # 2. folders
    for d in REQUIRED_DIRS:
        p = paths.OPS_HOME / d
        if p.is_dir():
            ok(f"folder: {d}/")
        elif init:
            p.mkdir(parents=True, exist_ok=True)
            (p / ".gitkeep").touch()
            ok(f"folder: {d}/ (created)")
        else:
            fail(f"folder: {d}/ MISSING (run: ops doctor --init)")

    # 3. manifest <-> bin  (hidden verbs, e.g. __complete, are intentionally absent from ops.json)
    def _hidden(v):
        f = BIN / v / "cmd.json"
        try:
            return bool(json.loads(f.read_text(encoding="utf-8")).get("hidden"))
        except Exception:
            return False
    verbs_on_disk = {p.parent.name for p in BIN.glob("*/run.py") if not _hidden(p.parent.name)}
    for v in sorted(verbs_on_disk):
        if not (BIN / v / "cmd.json").exists():
            warn(f"verb '{v}' has run.py but no cmd.json (won't show in ops help)")
    opsjson = paths.OPS_HOME / "ops.json"
    if opsjson.exists():
        try:
            man = {c["verb"] for c in json.loads(opsjson.read_text())["verbs"]}
            missing = verbs_on_disk - man
            ok("ops.json parses and matches bin/" if not missing else f"ops.json stale: missing {missing} (run: ops help)")
            if missing:
                warn(f"ops.json missing verbs: {missing}")
        except Exception as e:
            fail(f"ops.json does not parse: {e}")
    else:
        warn("ops.json not generated yet (run: ops help)")

    # 4. agent adapters
    agents, claude, skill = (paths.OPS_HOME / "AGENTS.md", paths.OPS_HOME / "CLAUDE.md",
                             paths.OPS_HOME / "skills" / "operate-ops" / "SKILL.md")
    (ok if agents.exists() else fail)(f"adapter: AGENTS.md {'present' if agents.exists() else 'MISSING'}")
    (ok if (claude.exists() and "@AGENTS.md" in claude.read_text()) else fail)(
        "adapter: CLAUDE.md bridges @AGENTS.md" if claude.exists() else "adapter: CLAUDE.md MISSING")
    (ok if skill.exists() else fail)(f"adapter: skills/operate-ops/SKILL.md {'present' if skill.exists() else 'MISSING'}")

    # per-agent adapters: warn if absent (a vault may not use every agent), FAIL if present-but-broken
    cdx_cfg, cdx_sk = paths.OPS_HOME / ".codex" / "config.toml", paths.OPS_HOME / ".codex" / "skills"
    if cdx_cfg.exists() or cdx_sk.is_symlink() or cdx_sk.exists():
        (ok if cdx_cfg.exists() else warn)(".codex/config.toml" + ("" if cdx_cfg.exists() else " MISSING"))
        (ok if (cdx_sk / "operate-ops").exists() else fail)(".codex/skills → skills/ resolves"
            if (cdx_sk / "operate-ops").exists() else ".codex/skills symlink is BROKEN")
    else:
        warn(".codex/ adapter not set up (Codex & Grok read AGENTS.md natively regardless)")
    cl_set, cl_sk = paths.OPS_HOME / ".claude" / "settings.json", paths.OPS_HOME / ".claude" / "skills"
    if cl_set.exists() or cl_sk.is_symlink() or cl_sk.exists():
        try:
            json.loads(cl_set.read_text()); ok(".claude/settings.json parses")
        except FileNotFoundError:
            warn(".claude/settings.json MISSING")
        except Exception as e:
            fail(f".claude/settings.json is INVALID json: {e}")
        (ok if (cl_sk / "operate-ops").exists() else fail)(".claude/skills → skills/ resolves"
            if (cl_sk / "operate-ops").exists() else ".claude/skills symlink is BROKEN")
    else:
        warn(".claude/ adapter not set up (add it to lock Claude Code to the ops surface)")

    # 5. no tracked secrets / binaries in wiki
    tracked = paths.git("ls-files").splitlines()
    if tracked:
        env = [t for t in tracked if Path(t).name.startswith(".env") or t.endswith(".env")]
        (fail if env else ok)(f"no tracked .env files" if not env else f"SECRET RISK: tracked {env}")
        wiki_bin = [t for t in tracked if t.startswith("wiki/") and not t.endswith((".md", ".gitkeep"))]
        (fail if wiki_bin else ok)("wiki is plaintext-only" if not wiki_bin else f"binaries tracked in wiki: {wiki_bin}")
    else:
        warn("not a git repo (or nothing tracked) — skipped secret/binary scan")

    # 6. index
    db = paths.OPS_HOME / ".index" / "ops.sqlite"
    (ok if db.exists() else warn)("index built" if db.exists() else "index not built (run: ops index)")

    nfail = sum(1 for lv, _ in checks if lv == "fail")
    nwarn = sum(1 for lv, _ in checks if lv == "warn")
    for lv, m in checks:
        c = {"ok": GREEN + "ok  ", "warn": YEL + "warn", "fail": RED + "FAIL"}[lv]
        print(f"  {c}{RESET} {m}")
    print(f"\ndoctor: {len(checks)-nfail-nwarn} ok, {nwarn} warn, {nfail} fail")
    return 1 if nfail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
