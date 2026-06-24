"""
guardrail.py — the §5 safety layer, ENFORCED (not just modeled). Mirrors the validated spec model
in test/lib/guardrail.py (kept in lock-step by test/run_guardrail.py's parity check). Two jobs:

  1. classify(action) — the path-wall + risk decision for a concrete action (write/read/transmit/
     delete/verb). Reusable: a write-verb calls this on the path IT computes (Iron Law — the verb
     owns placement), so the wall holds where the path is actually known.
  2. gate(verb, args, risk) + the CLI — the dispatcher's per-verb risk gate: deny is refused,
     confirm needs an explicit --yes, new/undeclared verbs default to confirm. Logs every call.

The dispatcher runs `guardrail.py <verb> <args...>` before exec; nonzero exit blocks the verb.
"""
from __future__ import annotations
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HOME = os.environ.get("OPS_TEST_HOME", os.environ.get("HOME", "/Users/tamas"))
OPS_HOME = Path(os.environ.get("OPS_HOME", Path(__file__).resolve().parents[2]))
BIN = Path(__file__).resolve().parents[1]

OPS = f"{HOME}/ops"
WORK = f"{HOME}/work"
FILES = f"{HOME}/files"
DOTFILES = f"{HOME}/dotfiles"

WALLED_OFF_MARKERS = [
    f"{HOME}/Library/Mobile Documents", f"{HOME}/iCloud Drive",
    "Mobile Documents", "iCloud", f"{HOME}/Pictures/Photos Library.photoslibrary", f"{HOME}/Pictures",
]
ALLOW, CONFIRM, DENY = "allow", "confirm", "deny"
_ORDER = {ALLOW: 0, CONFIRM: 1, DENY: 2}
SCHEDULABLE = {"read", "safe_write"}

TRANSMIT_PATTERNS = [
    (r"\bgit\s+push\b", "git push"), (r"\b(npm|pnpm|yarn|bun)\s+publish\b", "package publish"),
    (r"\b(vercel|netlify|flyctl|fly|wrangler|gcloud|heroku|render|railway)\b.*\bdeploy", "deploy"),
    (r"\baws\s+s3\b", "aws s3"), (r"\bgsutil\b", "gsutil"), (r"\bscp\b", "scp"),
    (r"\brsync\b.*(::|\S+@\S+:)", "rsync remote"),
    (r"\bgh\s+(pr\s+merge|release\s+create|api\b.*-X\s*(POST|PUT|PATCH|DELETE))", "gh write"),
    (r"\bcurl\b.*(-X\s*(POST|PUT|PATCH|DELETE)|--data\b|--data-\w+|-d\b|--upload-file\b|-T\b)", "curl write"),
    (r"\bwget\b.*--post", "wget post"),
]
DANGER_RM = [r"\brm\s+-[a-z]*r[a-z]*f", r"\brm\s+-[a-z]*f[a-z]*r",
             r"\brm\s+-r\b.*\s-f\b", r"\brm\s+-f\b.*\s-r\b",
             r"\brm\s+--recursive\b.*--force\b", r"\brm\s+--force\b.*--recursive\b"]


@dataclass
class Decision:
    verdict: str
    reason: str
    risk_class: str

    def __str__(self) -> str:
        return f"{self.verdict.upper()} [{self.risk_class}] — {self.reason}"


def _norm(path):
    if not path:
        return None
    p = path.strip()
    if p.startswith("~"):
        p = HOME + p[1:]
    return os.path.normpath(p)


def _under(path, root):
    pl, rl = path.lower(), root.lower()
    return pl == rl or pl.startswith(rl + "/")


def _walled(path):
    pl = path.lower()
    return any(m.lower() in pl for m in WALLED_OFF_MARKERS)


def _in_originals(path):
    return _under(path, FILES) and re.search(r"/in(/|$)", path, re.IGNORECASE) is not None


def _write_verdict(path, action):
    if _walled(path):
        return Decision(DENY, "iCloud/family path is walled off — propose, never write", "deny")
    if _in_originals(path):
        return Decision(DENY, "~/files/**/in/ originals are read-only evidence", "deny")
    if _under(path, OPS):
        return Decision(ALLOW, "write inside ~/ops is a revertible git diff", "safe_write")
    if _under(path, FILES):
        return Decision(ALLOW, "write inside ~/files (out/work/research)", "safe_write")
    if _under(path, f"{WORK}/.worktrees"):
        return Decision(ALLOW, "write inside ~/work/.worktrees (sanctioned agent worktree)", "safe_write")
    if _under(path, WORK):
        task_repo = _norm(action.get("task_repo"))
        repo = _norm(action.get("repo")) or path
        if task_repo and (repo == task_repo or _under(path, task_repo)):
            return Decision(ALLOW, "write inside the task's ~/work repo", "safe_write")
        return Decision(DENY, "write to a ~/work repo that is not the current task's repo", "deny")
    if _under(path, DOTFILES):
        return Decision(CONFIRM, "~/dotfiles: inspect, don't change without being asked", "confirm")
    return Decision(DENY, f"path escapes the three roots: {path}", "deny")


def classify(action: dict) -> Decision:
    kind = action.get("kind", "verb")
    flags = action.get("flags", {}) or {}
    yes, force = bool(flags.get("yes")), bool(flags.get("force"))
    path, realpath = _norm(action.get("path")), _norm(action.get("realpath"))
    command = (action.get("command") or "").strip()

    if command:
        if any(re.search(p, command) for p in DANGER_RM):
            return Decision(DENY, f"recursive forced delete is denied: '{command}'", "deny")
        if re.search(r"git\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)", command):
            return Decision(DENY, f"force push is denied: '{command}'", "deny")
        for pat, label in TRANSMIT_PATTERNS:
            if re.search(pat, command, re.IGNORECASE):
                if force:
                    return Decision(DENY, f"forced external transmit ({label}) is denied", "deny")
                return Decision(ALLOW if yes else CONFIRM,
                                f"external transmit ({label})" + (" authorized by --yes" if yes else " needs --yes"),
                                "confirm")
    if kind == "read_secret" or (path and re.search(r"(^|/)\.env($|\.|/)", path)):
        return Decision(DENY, "reading .env / secret values is denied", "deny")
    if kind == "resolve_secret":
        return Decision(DENY, "resolving an op:// secret to its value is denied", "deny")
    if kind == "read":
        for p in (path, realpath):
            if p and _walled(p):
                return Decision(DENY, "reading the iCloud/family tree is off every command path", "deny")
        return Decision(ALLOW, "read-only", "read")
    if kind == "transmit":
        if force:
            return Decision(DENY, "forced external transmit is denied", "deny")
        return Decision(ALLOW if yes else CONFIRM, "external transmit" + (" via --yes" if yes else " needs --yes"), "confirm")
    if kind == "delete":
        return Decision(DENY if force else CONFIRM, "delete is irreversible" + (" (forced=deny)" if force else " — needs --yes"), "confirm")
    if kind == "draft":
        return Decision(ALLOW, "draft produced; a human transmits", "draft_only")
    if kind in ("propose", "ask"):
        return Decision(ALLOW, f"{kind} has no side effect", "read")
    if kind == "write":
        if not path:
            return Decision(DENY, "write with no resolvable path", "deny")
        primary = _write_verdict(path, action)
        if realpath and realpath != path:
            secondary = _write_verdict(realpath, action)
            if _ORDER[secondary.verdict] > _ORDER[primary.verdict]:
                return Decision(secondary.verdict, f"symlink resolves to {realpath}: {secondary.reason}", secondary.risk_class)
        return primary
    if kind == "verb":
        v = (action.get("verb") or "").strip()
        if v.startswith("ops "):
            verb = v[4:].split()[0] if len(v) > 4 else ""
            if verb and verb not in _known_verbs():
                return Decision(DENY, f"unknown/invented ops verb: '{verb}'", "deny")
            return Decision(ALLOW, "known ops verb", "read")
        return Decision(ALLOW, "raw shell command (path wall + adapter scoping govern it)", "read")
    return Decision(DENY, f"unrecognized action kind: {kind}", "deny")


def _known_verbs() -> set:
    return {p.parent.name for p in BIN.glob("*/cmd.json")} | {p.parent.name for p in BIN.glob("*/run.py")}


def risk_of(verb: str) -> str | None:
    """Read a verb's declared risk from its cmd.json; None if undeclared (→ default confirm)."""
    f = BIN / verb / "cmd.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("risk")
    except Exception:
        return None


def gate(verb: str, args: list[str], risk: str | None = None) -> Decision:
    """Dispatcher per-verb gate: enforce the declared risk class (new verbs default to confirm).
    `risk` override is for tests; in normal use it's read from the verb's cmd.json."""
    if verb not in _known_verbs():
        return Decision(DENY, f"unknown/invented verb: '{verb}' (not in ops.json)", "deny")
    risk = risk or risk_of(verb) or "confirm"  # §5: new/undeclared verbs default to confirm
    yes = ("--yes" in args) or ("-y" in args)
    if risk == "deny":
        return Decision(DENY, f"'{verb}' is deny-class — never run", "deny")
    if risk == "confirm" and not yes:
        return Decision(CONFIRM, f"'{verb}' is confirm-class — re-run with --yes to proceed", "confirm")
    return Decision(ALLOW, f"{risk}", risk)


def _log(verb, args, d: Decision):
    try:
        logdir = OPS_HOME / ".logs"
        logdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(logdir / "ops.log", "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{verb} {' '.join(args)}\t{d.verdict}\t{d.reason}\n")
    except Exception:
        pass


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "help"
    args = sys.argv[2:]
    d = gate(verb, args)
    _log(verb, args, d)
    if d.verdict != ALLOW:
        print(f"guardrail: {d}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
