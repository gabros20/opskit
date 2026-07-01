"""
manifest.py — the capability manifest (§4.3). Each verb carries a `cmd.json` sidecar; this
concatenates them into the authoritative list that `ops help` renders from and `ops.json` exposes
to agents. Agents learn the surface from this — they never hardcode or invent verbs.
"""
from __future__ import annotations
import json
from pathlib import Path

from . import paths  # type: ignore  # (namespace sibling)

BIN = Path(__file__).resolve().parents[1]   # the verbs live with the CODE (bin/), not under OPS_HOME
MANIFEST = paths.OPS_HOME / "ops.json"       # ...but ops.json is written to the data root (OPS_HOME)

# display grouping (design §4.1); verbs not listed fall under "OTHER"
GROUPS = [
    ("SYSTEM", ["help", "status", "doctor", "backup", "index", "consolidate"]),
    ("FLOW", ["capture", "triage", "start", "close", "week"]),
    ("KNOWLEDGE", ["search", "wiki", "bookmark"]),
    ("TASKS", ["task"]),
    ("WORK", ["new", "repo", "archive", "files", "sweep"]),
    ("BUSINESS", ["invoice"]),
    ("JOBS", ["job"]),
]


def load_cmds() -> list[dict]:
    """Visible verbs, from the cmd.json sidecars. `"hidden": true` verbs (e.g. __complete, an
    internal shell-completion helper) are omitted from the surface, `ops help`, and ops.json —
    but still exist on disk, so the guardrail reads their risk directly."""
    cmds = []
    for cmd in sorted(BIN.glob("*/cmd.json")):
        try:
            d = json.loads(cmd.read_text(encoding="utf-8"))
            if d.get("hidden"):
                continue
            d["_built"] = (cmd.parent / "run.py").exists()
            cmds.append(d)
        except Exception:
            pass
    return cmds


def write_manifest() -> Path:
    """(Re)generate ops.json from the cmd.json sidecars (committed; rebuilt by `ops index`)."""
    cmds = [{k: v for k, v in c.items() if not k.startswith("_")} for c in load_cmds()]
    MANIFEST.write_text(json.dumps({"verbs": cmds}, indent=2) + "\n", encoding="utf-8")
    return MANIFEST


def render(verb: str | None = None) -> str:
    cmds = {c["verb"]: c for c in load_cmds()}
    if verb:
        c = cmds.get(verb)
        if not c:
            return f"unknown verb: {verb} (try: ops help)"
        lines = [f"ops {c['verb']} — {c.get('summary','')}", f"  usage: {c.get('usage','')}",
                 f"  risk:  {c.get('risk','?')}"]
        if c.get("args"):
            lines.append("  args:")
            for a in c["args"]:
                req = "required" if a.get("required") else f"optional (default: {a.get('default','-')})"
                lines.append(f"    {a['name']:<12} {req}")
        if not c.get("_built", True):
            lines.append("  status: DESIGNED — not built yet")
        return "\n".join(lines)
    out = ["ops <verb> — the personal OS command surface", ""]
    placed = set()
    for group, verbs in GROUPS:
        rows = []
        for v in verbs:
            if v in cmds:
                placed.add(v)
                c = cmds[v]
                mark = "" if c.get("_built") else "  (designed, not built)"
                rows.append(f"  ops {c['verb']:<10} {c.get('summary','')}{mark}")
        if rows:
            out.append(group)
            out += rows
            out.append("")
    extra = [c for v, c in cmds.items() if v not in placed]
    if extra:
        out.append("OTHER")
        out += [f"  ops {c['verb']:<10} {c.get('summary','')}" for c in extra]
        out.append("")
    out.append("`ops help <verb>` for one verb. Search stages: OPS_VECTORS=1 (LanceDB), OPS_RERANK=1 (rerank).")
    return "\n".join(out)
