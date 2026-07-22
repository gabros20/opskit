"""Shared setup layer registry for `ops setup` and `ops doctor`.

This module is deliberately verb-agnostic. It may invoke sibling verbs by path, but it does not
import their `run.py` modules, so setup status can be reused without cross-verb import side effects.
"""
from __future__ import annotations
from dataclasses import dataclass
import importlib.util
import os
import platform
import shutil
import subprocess
import sys

from lib import embed, enrichlib, imagelib, paths

BIN = paths.BIN
REQUIRED_DIRS = ["wiki", "tasks/inbox", "tasks/active", "tasks/waiting", "tasks/done",
                 "journal", "inbox", "templates", "jobs", "skills", "bin"]
STATUSES = {"ready", "partial", "absent", "blocked"}


@dataclass(frozen=True)
class Layer:
    id: str
    title: str
    why: str
    required: bool
    gate: str
    handoff: str = ""


LAYERS: list[Layer] = [
    Layer("skeleton", "Vault structure", "Required folders and Obsidian seed files", True, "safe_write"),
    Layer("search", "Semantic search", "Vector index dependencies and embedding model", False, "confirm"),
    Layer("backups", "Durability", "Encrypted off-machine backup configuration", False, "blocked", "ops backup init"),
    Layer("models", "File-processing / LLM", "Local models and optional file-processing runtimes", False, "confirm"),
    Layer("automation", "Schedules", "Rendered launchd job plists", False, "safe_write"),
]


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "on")


def _fake(fake: bool = False) -> bool:
    return fake or _truthy(os.environ.get("OPS_SETUP_FAKE"))


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _ollama_has(model: str) -> bool:
    """Probe `ollama list` for a model tag.

    This intentionally copies the small probe from `bin/models/run.py` instead of importing that verb:
    setup is shared library code and must avoid cross-verb imports.
    """
    if not shutil.which("ollama"):
        return False
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
    except Exception:
        return False
    if r.returncode != 0:
        return False
    base = model.split(":")[0]
    for ln in r.stdout.strip().splitlines()[1:]:
        if not ln.strip():
            continue
        tag = ln.split()[0]
        if tag == model or tag.split(":")[0] == base:
            return True
    return False


def _embed_model() -> str:
    return os.environ.get("OPS_EMBED_MODEL", embed.model_name())


def _platform_system() -> str:
    return platform.system()


def _platform_machine() -> str:
    return platform.machine()


def _run(cmd: list[str], *, fake: bool = False) -> str:
    display = " ".join(cmd)
    if _fake(fake):
        return display
    subprocess.run(cmd, check=True)
    return display


def _run_verb(verb: str, *args: str, fake: bool = False) -> str:
    return _run([sys.executable, str(BIN / verb / "run.py"), *args], fake=fake)


def _pip(*pkgs_or_reqs: str, fake: bool = False) -> str:
    return _run([sys.executable, "-m", "pip", "install", *pkgs_or_reqs], fake=fake)


def _layer(layer_id: str) -> Layer:
    for layer in LAYERS:
        if layer.id == layer_id:
            return layer
    raise ValueError(f"unknown layer '{layer_id}' (one of: {', '.join(l.id for l in LAYERS)})")


def _items_status(items: list[dict], *, optional: bool = True) -> str:
    oks = [bool(i.get("ok")) for i in items]
    if all(oks):
        return "ready"
    if any(oks):
        return "partial"
    return "absent" if optional else "partial"


def _row(layer: Layer, state: str, detail: str, items: list[dict], next_: str = "") -> dict:
    return {"id": layer.id, "title": layer.title, "status": state, "required": layer.required,
            "detail": detail, "items": items, "next": next_}


def _status_skeleton(layer: Layer) -> dict:
    # Required-readiness depends ONLY on REQUIRED_DIRS. The .obsidian/* config-pack items stay
    # visible in the row (so `ops setup` shows their state) but are advisory: they report ok/not-ok
    # and never flip this required layer to non-ready (a fresh clone that hasn't seeded .obsidian/
    # must still let `ops doctor` pass). Seeding is handled by `ops doctor --init`.
    required = [{"id": str(rel), "title": str(rel), "ok": (paths.OPS_HOME / rel).is_dir()} for rel in REQUIRED_DIRS]
    items = list(required)
    pack = paths.OPS_HOME / "templates" / "obsidian"
    if pack.is_dir():
        for src in sorted(pack.glob("*.json")):
            rel = f".obsidian/{src.name}"
            items.append({"id": rel, "title": rel, "advisory": True,
                          "ok": (paths.OPS_HOME / ".obsidian" / src.name).is_file()})
    state = _items_status(required, optional=False)
    detail = "vault skeleton ready" if state == "ready" else "required vault structure is incomplete"
    return _row(layer, state, detail, items, "ops setup skeleton" if state != "ready" else "")


def _status_search(layer: Layer) -> dict:
    model = _embed_model()
    items = [
        {"id": "lancedb", "title": "lancedb", "ok": _has("lancedb")},
        {"id": "fastembed", "title": "fastembed", "ok": _has("fastembed")},
        {"id": "embed_model", "title": model, "ok": _ollama_has(model)},
    ]
    state = _items_status(items)
    detail = "semantic search ready" if state == "ready" else "semantic search prerequisites are missing"
    return _row(layer, state, detail, items, "ops setup search --yes" if state != "ready" else "")


def _status_backups(layer: Layer) -> dict:
    items = [
        {"id": "config", "title": ".backup/config.json", "ok": (paths.OPS_HOME / ".backup" / "config.json").exists()},
        {"id": "restic", "title": "restic", "ok": shutil.which("restic") is not None},
    ]
    if all(i["ok"] for i in items):
        return _row(layer, "ready", "backup configuration ready", items)
    if any(i["ok"] for i in items):
        return _row(layer, "blocked", "backup setup needs human initialization", items, layer.handoff)
    return _row(layer, "absent", "backup setup has not been initialized", items, layer.handoff)


def _status_models(layer: Layer) -> dict:
    vlm_model = (os.environ.get("OPS_VLM", "qwen3-vl:4b") or "qwen3-vl:4b").strip()
    vlm_ok = False if vlm_model.lower() == "none" else (imagelib._has_mlx() or (_ollama_has(vlm_model) if imagelib._has_ollama() else False))
    items = [
        {"id": "enrich", "title": enrichlib.DEFAULT_MODEL, "ok": _ollama_has(enrichlib.DEFAULT_MODEL)},
        {"id": "ocr", "title": imagelib.ocr_backend_label() or "none", "ok": imagelib.ocr_backend_label() is not None},
        {"id": "vlm", "title": vlm_model, "ok": vlm_ok},
        {"id": "stt", "title": "speech-to-text runtime", "ok": any(_has(m) for m in ("parakeet_mlx", "mlx_whisper", "faster_whisper"))},
    ]
    state = _items_status(items)
    detail = "file-processing models ready" if state == "ready" else "file-processing model layer is incomplete"
    return _row(layer, state, detail, items, "ops setup models --yes" if state != "ready" else "")


def _status_automation(layer: Layer) -> dict:
    launchd = paths.OPS_HOME / "jobs" / "launchd"
    plists = sorted(launchd.glob("*.plist")) if launchd.exists() else []
    items = [{"id": "launchd", "title": "jobs/launchd/*.plist", "ok": bool(plists)}]
    state = "ready" if plists else "absent"
    detail = "job plists rendered" if state == "ready" else "job plists have not been rendered"
    return _row(layer, state, detail, items, "ops setup automation" if state != "ready" else "")


def status(layer_id=None) -> list[dict]:
    selected = [_layer(layer_id)] if layer_id else list(LAYERS)
    out = []
    for layer in selected:
        if layer.id == "skeleton":
            out.append(_status_skeleton(layer))
        elif layer.id == "search":
            out.append(_status_search(layer))
        elif layer.id == "backups":
            out.append(_status_backups(layer))
        elif layer.id == "models":
            out.append(_status_models(layer))
        elif layer.id == "automation":
            out.append(_status_automation(layer))
    return out


def _result() -> dict:
    return {"ran": [], "skipped": [], "handoff": [], "confirm_needed": False}


def _confirm(layer: Layer, yes: bool, res: dict) -> bool:
    if layer.gate == "confirm" and not yes:
        res["confirm_needed"] = True
        res["skipped"].append(layer.id)
        return False
    return True


def advance(layer_id, *, yes: bool, fake: bool) -> dict:
    layer = _layer(layer_id)
    res = _result()
    if status(layer.id)[0]["status"] == "ready":
        res["skipped"].append(layer.id)
        return res
    if layer.gate == "blocked":
        if layer.handoff:
            res["handoff"].append(layer.handoff)
        res["skipped"].append(layer.id)
        return res
    if not _confirm(layer, yes, res):
        return res

    if layer.id == "skeleton":
        res["ran"].append(_run_verb("doctor", "--init", fake=fake))
    elif layer.id == "search":
        res["ran"].append(_pip("-r", str(paths.OPS_HOME / "requirements.txt"), fake=fake))
        res["ran"].append(_run(["ollama", "pull", _embed_model()], fake=fake))
    elif layer.id == "models":
        res["ran"].append(_run_verb("models", "pull", "--all", "--yes", fake=fake))
        pkgs = ["Pillow", "trafilatura"]
        if _platform_system() == "Darwin" and _platform_machine().lower() in ("arm64", "aarch64"):
            pkgs.append("mlx-vlm")
        res["ran"].append(_pip(*pkgs, fake=fake))
    elif layer.id == "automation":
        res["ran"].append(_run_verb("job", "apply", fake=fake))
    return res
