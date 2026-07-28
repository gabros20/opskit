"""
jobsmodel.py — invariant checks over the §15 jobs registry.

The design states hard rules for scheduled jobs (§15):
  - only `read` / `safe_write` risk classes may be scheduled,
  - jobs call verbs, never inline logic,
  - every job is manually runnable,
  - a scheduled job must be safe to run mid-work.

This module turns those prose rules into checks, and also cross-checks each job command
against the §5 guardrail model + the documented verb surface to catch drift (a job that
writes outside the roots, references an undocumented subaction, or transmits while declared
`read`).
"""
from __future__ import annotations
import re
from dataclasses import dataclass

from .guardrail import KNOWN_VERBS, classify, DENY

SCHEDULABLE_RISK = {"read", "safe_write"}
# Repo subactions documented in §4.1 (health|clone|adopt|nuke-modules as of v3.7).
DOCUMENTED_REPO_SUBACTIONS = {"health", "clone", "adopt", "nuke-modules"}
# Filesystem zones a job may write beyond the three roots — the §5 sweep-zone carve-out (v3.7):
# Desktop/Downloads are the move-only macOS-inbox domain of `plainkeep sweep`.
SANCTIONED_EXTRA_WRITE_ZONES: set[str] = {"~/Desktop", "~/Downloads"}


@dataclass
class Finding:
    job: str
    rule: str
    ok: bool
    detail: str


def _verb_of(command: str) -> str:
    toks = command.split()
    if not toks:
        return ""
    if toks[0] != "plainkeep":
        return ""  # external command
    return toks[1] if len(toks) > 1 else ""


def _has_inline_logic(command: str) -> bool:
    # jobs call ONE verb; pipes/&&/;/$() = inline logic
    return bool(re.search(r"(\|\||&&|;|\||\$\(|`)", command))


def check_jobs(registry: dict) -> list[Finding]:
    findings: list[Finding] = []
    external = set(registry.get("external_allowlist", []))
    for name, job in registry["jobs"].items():
        cmd = job["command"]
        risk = job.get("risk", "")
        toks = cmd.split()
        is_external = bool(toks) and toks[0] != "plainkeep"

        # rule 1 — only read/safe_write may be scheduled
        findings.append(Finding(name, "schedulable-risk", risk in SCHEDULABLE_RISK,
                                f"risk={risk!r} (must be one of {sorted(SCHEDULABLE_RISK)})"))

        # rule 2 — calls a verb (or an allowlisted external), never inline logic
        if is_external:
            ok = toks[0] in external
            findings.append(Finding(name, "verb-or-allowlisted", ok,
                                    f"external command {toks[0]!r} {'allowlisted' if ok else 'NOT allowlisted'}"))
        else:
            verb = _verb_of(cmd)
            ok = verb in KNOWN_VERBS
            findings.append(Finding(name, "known-verb", ok,
                                    f"verb={verb!r} {'known' if ok else 'NOT in plainkeep.json surface'}"))
            # repo subaction documentation
            if verb == "repo" and len(toks) > 2:
                sub = toks[2]
                findings.append(Finding(name, "documented-subaction", sub in DOCUMENTED_REPO_SUBACTIONS,
                                        f"repo subaction {sub!r} {'documented' if sub in DOCUMENTED_REPO_SUBACTIONS else 'NOT in §4.1'}"))

        findings.append(Finding(name, "no-inline-logic", not _has_inline_logic(cmd),
                                "single verb call" if not _has_inline_logic(cmd) else f"inline logic in: {cmd!r}"))

        # rule 3 — declared risk vs what the writes/transmit actually imply (guardrail cross-check)
        # A transmit is confirm-class UNLESS it is the §5 pre-authorized backup carve-out
        # (fixed destination, no per-run human decision) declared via `sanctioned_transmit`.
        if job.get("transmits") and risk == "read":
            sanctioned = bool(job.get("sanctioned_transmit"))
            findings.append(Finding(name, "risk-matches-effect", sanctioned,
                                    f"sanctioned pre-authorized backup transmit ({job.get('sanctioned_transmit')})"
                                    if sanctioned else
                                    "declared 'read' but transmits externally with no sanctioned-transmit carve-out (§5)"))
        # rule 4 — write targets must stay inside the three roots (or a sanctioned extra zone)
        for w in job.get("writes", []):
            if w.startswith("(") or w.startswith("~/plainkeep") or w.startswith("~/files") or w.startswith("~/work"):
                continue
            sanctioned = any(w.startswith(z) for z in SANCTIONED_EXTRA_WRITE_ZONES)
            findings.append(Finding(name, "writes-inside-roots", sanctioned,
                                    f"write target {w!r} is outside the three roots and not a sanctioned zone (§5 path wall would DENY)"))
    return findings
