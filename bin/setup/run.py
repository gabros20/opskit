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
}
AUTO_LAYERS = ("skeleton", "search", "models", "automation")


def _valid_ids() -> list[str]:
    return [layer.id for layer in setuplib.LAYERS]


def _fake() -> bool:
    return (os.environ.get("OPS_SETUP_FAKE") or "").strip().lower() in ("1", "true", "yes", "on")


def _row_next(row: dict) -> str:
    if row["status"] == "ready":
        return ""
    if row["id"] == "backups":
        return row.get("next") or "ops backup init"
    if row["id"] in ("search", "models"):
        return f"ops setup {row['id']} --yes"
    return f"ops setup {row['id']}"


def _dashboard_rows() -> list[dict]:
    rows = setuplib.status()
    return [{**row, "next": _row_next(row)} for row in rows]


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


def _render_result(layer_id: str, before: dict, res: dict) -> str:
    lines = []
    if before["status"] == "ready":
        lines.append(f"{layer_id}: already ready")
    elif res["confirm_needed"]:
        lines.append(f"{layer_id}: needs confirmation")
    elif res["ran"]:
        lines.append(f"{layer_id}: advanced")
        for cmd in res["ran"]:
            lines.append(f"  ran: {cmd}")
    elif res["handoff"]:
        lines.append(f"{layer_id}: handoff required")
    else:
        lines.append(f"{layer_id}: no changes")
    for item in res["handoff"]:
        lines.append(f"  handoff: {item}")
    return "\n".join(lines)


def _advance_one(layer_id: str, *, yes: bool) -> int:
    _valid_or_fail(layer_id)
    before = setuplib.status(layer_id)[0]
    layer = next(layer for layer in setuplib.LAYERS if layer.id == layer_id)
    if before["status"] != "ready" and layer.gate == "confirm" and not yes:
        output.fail(output.EXIT_CONFIRM, _confirm_message(layer_id),
                    hint=f"re-run: ops setup {layer_id} --yes", verb="setup")
    try:
        res = setuplib.advance(layer_id, yes=yes, fake=_fake())
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        _action_failed(layer_id, exc)
    return output.emit({**res, "layer": layer_id, "status": before["status"]}, "setup",
                       human=lambda _: _render_result(layer_id, before, res))


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


def _render_all(results: list[dict], handoffs: list[str]) -> str:
    lines = ["setup --all:"]
    for res in results:
        layer = res["layer"]
        if res["ran"]:
            lines.append(f"  {layer}: advanced")
            for cmd in res["ran"]:
                lines.append(f"    ran: {cmd}")
        elif res["skipped"]:
            lines.append(f"  {layer}: skipped")
        else:
            lines.append(f"  {layer}: no changes")
    if handoffs:
        lines.append("\noutstanding handoffs:")
        for item in handoffs:
            lines.append(f"  [ ] {item}")
    return "\n".join(lines)


def _advance_all(*, yes: bool) -> int:
    rows = {row["id"]: row for row in setuplib.status()}
    confirm = []
    for layer in setuplib.LAYERS:
        if layer.id in AUTO_LAYERS and layer.gate == "confirm" and rows[layer.id]["status"] != "ready":
            confirm.append(layer.id)
    if confirm and not yes:
        output.fail(output.EXIT_CONFIRM,
                    f"setup layers need --yes: {', '.join(confirm)}",
                    hint="re-run: ops setup --all --yes", verb="setup")
    results = []
    for layer_id in AUTO_LAYERS:
        try:
            res = setuplib.advance(layer_id, yes=yes, fake=_fake())
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
            _action_failed(layer_id, exc)
        results.append({**res, "layer": layer_id})
    handoffs = _handoffs()
    return output.emit({"results": results, "handoff": handoffs}, "setup",
                       human=lambda _: _render_all(results, handoffs))


def main(argv: list[str]) -> int:
    _, argv = output.parse_argv(argv)
    yes = "--yes" in argv or "-y" in argv
    all_ = "--all" in argv
    argv = [a for a in argv if a not in ("--yes", "-y", "--all")]
    if all_ and argv:
        output.fail(output.EXIT_USAGE, "usage: ops setup [<layer> [--yes] | --all [--yes]]", verb="setup")
    if all_:
        return _advance_all(yes=yes)
    if not argv:
        return output.emit_rows(_dashboard_rows(), "setup", human=_render_dashboard)
    if len(argv) > 1:
        output.fail(output.EXIT_USAGE, "usage: ops setup [<layer> [--yes] | --all [--yes]]", verb="setup")
    return _advance_one(argv[0], yes=yes)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
