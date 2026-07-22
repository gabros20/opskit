#!/usr/bin/env python3
"""Layered installer for the local ops system."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output, setuplib  # noqa: E402

GLYPHS = {
    "ready": "✓",
    "partial": "◐",
    "absent": "○",
    "blocked": "!",
    "not_applicable": "—",
}
AUTO_LAYERS = ("skeleton", "search", "models", "automation")
# Statuses `--all` neither attempts nor counts as a failure (Task 8): already done, gated on a missing
# prerequisite, or not applicable to this host.
SKIP_STATUSES = ("ready", "blocked", "not_applicable")


def _valid_ids() -> list[str]:
    return [layer.id for layer in setuplib.LAYERS]


def _fake() -> bool:
    return (os.environ.get("OPS_SETUP_FAKE") or "").strip().lower() in ("1", "true", "yes", "on")


def _dashboard_rows() -> list[dict]:
    # setuplib is the single source of truth for each layer's `next` remediation string; the
    # dashboard surfaces it verbatim rather than re-deriving a divergent one.
    return setuplib.status()


def _render_dashboard(rows: list[dict]) -> str:
    lines = ["setup layers:"]
    for row in rows:
        glyph = GLYPHS.get(row["status"], "?")
        required = "required" if row["required"] else "optional"
        next_cmd = row.get("next") or "-"
        lines.append(f"  {glyph} {row['id']:<10} {row['title']:<24} {row['status']:<8} {required:<8} {row['detail']}")
        lines.append(f"    next: {next_cmd}")
    return "\n".join(lines)


def _valid_or_fail(layer_id: str) -> None:
    ids = _valid_ids()
    if layer_id not in ids:
        output.fail(output.EXIT_USAGE,
                    f"unknown setup layer '{layer_id}' (valid ids: {', '.join(ids)})",
                    verb="setup")


def _confirm_message(layer_id: str) -> str:
    return f"{layer_id} installs downloads and local dependencies"


def _action_failed(layer_id: str, exc: Exception) -> None:
    layer = next(layer for layer in setuplib.LAYERS if layer.id == layer_id)
    yes = " --yes" if layer.gate == "confirm" else ""
    hint = f"fix the reported setup prerequisite, then re-run: ops setup {layer_id}{yes}"
    if isinstance(exc, subprocess.CalledProcessError):
        cmd = " ".join(str(part) for part in (exc.cmd if isinstance(exc.cmd, (list, tuple)) else [exc.cmd]))
        output.fail(output.EXIT_UNEXPECTED,
                    f"setup layer '{layer_id}' failed while running: {cmd} (exit {exc.returncode})",
                    hint=hint, verb="setup")
    output.fail(output.EXIT_UNEXPECTED, f"setup layer '{layer_id}' failed: {exc}", hint=hint, verb="setup")


def _render_result(layer_id: str, before: dict, res: dict, dry: bool = False) -> str:
    verb = "would run" if dry else "ran"
    lines = []
    if dry:
        lines.append(f"{layer_id}: dry run (nothing installed/written)")
    if before["status"] == "ready":
        lines.append(f"{layer_id}: already ready")
    elif res["confirm_needed"]:
        lines.append(f"{layer_id}: needs confirmation")
    elif res["ran"]:
        lines.append(f"{layer_id}: {'would advance' if dry else 'advanced'}")
        for cmd in res["ran"]:
            lines.append(f"  {verb}: {cmd}")
    elif res["handoff"]:
        lines.append(f"{layer_id}: handoff required")
    else:
        lines.append(f"{layer_id}: no changes")
    for item in res["handoff"]:
        lines.append(f"  handoff: {item}")
    return "\n".join(lines)


def _advance_one(layer_id: str, *, yes: bool, dry: bool = False) -> int:
    _valid_or_fail(layer_id)
    before = setuplib.status(layer_id)[0]
    layer = next(layer for layer in setuplib.LAYERS if layer.id == layer_id)
    # A --dry-run is a READ (the guardrail already downgrades it): it previews the plan with fake=True
    # and NEVER requires --yes, even for a confirm-class layer (Task 7a).
    if not dry and before["status"] != "ready" and layer.gate == "confirm" and not yes:
        output.fail(output.EXIT_CONFIRM, _confirm_message(layer_id),
                    hint=f"re-run: ops setup {layer_id} --yes", verb="setup")
    try:
        res = setuplib.advance(layer_id, yes=(yes or dry), fake=(_fake() or dry))
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        _action_failed(layer_id, exc)
    payload = {**res, "layer": layer_id, "status": before["status"]}
    if dry:
        payload["dry_run"] = True
    return output.emit(payload, "setup",
                       human=lambda _: _render_result(layer_id, before, res, dry=dry))


def _handoffs() -> list[str]:
    handoffs = []
    by_id = {row["id"]: row for row in setuplib.status()}
    backups = by_id.get("backups")
    if backups and backups["status"] != "ready" and backups.get("next"):
        handoffs.append(backups["next"])
    automation = by_id.get("automation")
    if automation and automation["status"] == "ready":
        handoffs.append("load launchd plists")
    handoffs.append("push git changes")
    return list(dict.fromkeys(handoffs))


def _describe_failure(layer_id: str, exc: Exception) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        cmd = " ".join(str(part) for part in (exc.cmd if isinstance(exc.cmd, (list, tuple)) else [exc.cmd]))
        return f"{cmd} (exit {exc.returncode})"
    return str(exc)


def _render_all(results: list[dict], handoffs: list[str], dry: bool = False) -> str:
    lines = ["setup --all (dry run — nothing installed/written):" if dry else "setup --all:"]
    verb = "would run" if dry else "ran"
    for res in results:
        layer = res["layer"]
        if res.get("failed"):
            lines.append(f"  {layer}: FAILED — {res['failed']}")
        elif res["ran"]:
            lines.append(f"  {layer}: {'would advance' if dry else 'advanced'}")
            for cmd in res["ran"]:
                lines.append(f"    {verb}: {cmd}")
        elif res.get("skipped_reason"):
            lines.append(f"  {layer}: skipped ({res['skipped_reason']})")
        elif res["skipped"]:
            lines.append(f"  {layer}: skipped")
        else:
            lines.append(f"  {layer}: no changes")
    if handoffs:
        lines.append("\noutstanding handoffs:")
        for item in handoffs:
            lines.append(f"  [ ] {item}")
    return "\n".join(lines)


def _advance_all(*, yes: bool, dry: bool = False) -> int:
    """Best-effort orchestration (Task 8): advance every AUTO layer that CAN be attempted, recording
    per-layer outcomes; a failure in one independent layer does NOT abort the rest. Layers that are
    already ready, blocked on a missing prerequisite, or not applicable to this host are skipped (not
    attempted), and never contribute to the exit code. Overall exit: 1 iff some ATTEMPTED layer
    failed; 0 otherwise. `--dry-run` previews the plan (fake=True) and needs no --yes."""
    rows = {row["id"]: row for row in setuplib.status()}
    # Confirm gate (skipped for a dry-run, which is a read): name the confirm-class layers that would
    # actually be attempted (not already-ready). Blocked/not_applicable layers can still appear here
    # so the message stays honest about what --all covers; the attempt loop then skips them.
    if not dry:
        confirm = [layer.id for layer in setuplib.LAYERS
                   if layer.id in AUTO_LAYERS and layer.gate == "confirm"
                   and rows[layer.id]["status"] != "ready"]
        if confirm and not yes:
            output.fail(output.EXIT_CONFIRM,
                        f"setup layers need --yes: {', '.join(confirm)}",
                        hint="re-run: ops setup --all --yes", verb="setup")
    results = []
    attempted_failed = False
    for layer_id in AUTO_LAYERS:
        st = rows[layer_id]["status"]
        if st in SKIP_STATUSES:
            res = setuplib._result()
            res["skipped"].append(layer_id)
            if rows[layer_id].get("next"):
                res["handoff"].append(rows[layer_id]["next"])
            results.append({**res, "layer": layer_id, "skipped_reason": st})
            continue
        try:
            res = setuplib.advance(layer_id, yes=(yes or dry), fake=(_fake() or dry))
            results.append({**res, "layer": layer_id})
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
            attempted_failed = True
            results.append({"layer": layer_id, "ran": [], "skipped": [], "handoff": [],
                            "confirm_needed": False, "failed": _describe_failure(layer_id, exc)})
    handoffs = _handoffs()
    payload = {"results": results, "handoff": handoffs}
    if dry:
        payload["dry_run"] = True
    output.emit(payload, "setup", human=lambda _: _render_all(results, handoffs, dry=dry))
    # Exit 1 is a semantic "some attempted layer failed" (machine-contract §2), not a crash — the
    # envelope's ok stays true; the aggregate `results` carries each failure.
    return output.EXIT_UNEXPECTED if attempted_failed else output.EXIT_OK


USAGE = "usage: ops setup [<layer> [--yes] | --all [--yes]] [--dry-run]"


def main(argv: list[str]) -> int:
    _, argv = output.parse_argv(argv)
    yes = "--yes" in argv or "-y" in argv
    all_ = "--all" in argv
    dry = "--dry-run" in argv  # a true preview: advance with fake=True, write nothing, never need --yes
    argv = [a for a in argv if a not in ("--yes", "-y", "--all", "--dry-run")]
    if all_ and argv:
        output.fail(output.EXIT_USAGE, USAGE, verb="setup")
    if all_:
        return _advance_all(yes=yes, dry=dry)
    if not argv:
        return output.emit_rows(_dashboard_rows(), "setup", human=_render_dashboard)
    if len(argv) > 1:
        output.fail(output.EXIT_USAGE, USAGE, verb="setup")
    return _advance_one(argv[0], yes=yes, dry=dry)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
