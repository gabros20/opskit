"""
op_runner.py — plug a real LLM in as the SYSTEM OPERATOR.
(Named op_runner, not operator, so it never shadows Python's stdlib `operator` module.)

Given the contract + manual + world + a scenario, it asks the model for a PLAN of actions as
JSON (it does not let the model touch the real filesystem). Defaults to the `claude -p` CLI
(the same agent indirection the design's agent.sh uses), but any command can be supplied so the
agnosticism test can run two different models and diff them.

A --dry-run mode returns a deterministic stub so the whole pipeline (parse -> judge -> report)
can be exercised offline with zero cost.
"""
from __future__ import annotations
import json
import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class OperatorResult:
    raw: str
    plan: dict
    ok: bool
    error: str = ""
    model: str = ""
    meta: dict = field(default_factory=dict)


def _extract_json(text: str) -> dict:
    """Find the first balanced {...} JSON object in arbitrary model output."""
    # fast path
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # fenced ```json
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # first balanced brace scan
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start:i + 1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        break
        start = text.find("{", start + 1)
    raise ValueError("no parseable JSON object in operator output")


def _normalize_plan(plan: dict) -> dict:
    plan.setdefault("searched_first", False)
    plan.setdefault("refused", False)
    plan.setdefault("asked_user", False)
    plan.setdefault("actions", [])
    plan.setdefault("notes", "")
    for a in plan["actions"]:
        a.setdefault("type", "run_verb")
        a.setdefault("verb", None)
        a.setdefault("target_path", None)
        a.setdefault("transmits_externally", False)
        a.setdefault("rationale", "")
    return plan


# A deterministic offline stub keyed by simple intent detection — lets us validate the
# judge/report wiring without any LLM. Intentionally imperfect so failures are visible too.
def _dry_run_plan(prompt: str) -> dict:
    s = prompt.lower()
    request = prompt.split("THE REQUEST =====", 1)[-1].lower()
    if "tax" in request or "nav" in request or "medical" in request:
        return {"searched_first": False, "refused": False, "asked_user": True,
                "actions": [{"type": "propose", "verb": None,
                             "target_path": "iCloud Személyes/pénzügyek/adó/",
                             "transmits_externally": False,
                             "rationale": "personal/legal doc -> propose iCloud move, do not write"}],
                "notes": "stub"}
    if "email" in request and ("send" in request or "now" in request):
        return {"searched_first": False, "refused": True, "asked_user": True,
                "actions": [{"type": "refuse", "verb": None, "target_path": None,
                             "transmits_externally": False, "rationale": "no transmit without --yes"}],
                "notes": "stub"}
    if "decide" in request or "what did we" in request:
        return {"searched_first": True, "refused": False, "asked_user": False,
                "actions": [{"type": "search", "verb": "ops search \"webhook retry\"",
                             "target_path": None, "transmits_externally": False,
                             "rationale": "brain-first"}], "notes": "stub"}
    return {"searched_first": True, "refused": False, "asked_user": True,
            "actions": [{"type": "ask", "verb": None, "target_path": None,
                         "transmits_externally": False, "rationale": "ambiguous; stub asks"}],
            "notes": "stub"}


def run_operator(prompt: str, model: str = "sonnet", dry_run: bool = False,
                 cmd_template: list[str] | None = None, timeout: int = 180) -> OperatorResult:
    if dry_run:
        plan = _normalize_plan(_dry_run_plan(prompt))
        return OperatorResult(raw="<dry-run>", plan=plan, ok=True, model="dry-run")

    cmd = cmd_template or ["claude", "-p", "--output-format", "text", "--model", model]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        return OperatorResult(raw="", plan={}, ok=False, error=f"operator command not found: {e}", model=model)
    except subprocess.TimeoutExpired:
        return OperatorResult(raw="", plan={}, ok=False, error=f"operator timed out after {timeout}s", model=model)

    raw = proc.stdout or ""
    if proc.returncode != 0 and not raw:
        return OperatorResult(raw=proc.stderr, plan={}, ok=False,
                              error=f"operator exited {proc.returncode}: {proc.stderr[:300]}", model=model)
    try:
        plan = _normalize_plan(_extract_json(raw))
    except Exception as e:
        return OperatorResult(raw=raw, plan={}, ok=False, error=f"parse error: {e}", model=model)
    return OperatorResult(raw=raw, plan=plan, ok=True, model=model)
