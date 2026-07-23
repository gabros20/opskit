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
# Layer status enum (documented in docs/machine-contract.md §7 and docs/setup.md). `not_applicable`
# (Task 8) means the layer cannot apply on THIS host — e.g. launchd scheduling off macOS — and is
# advisory-only: it never fails `ops doctor` and never causes a nonzero `--all` exit.
STATUSES = {"ready", "partial", "absent", "blocked", "not_applicable"}

# The SEARCH-ONLY dependency set (ADR-009): a strict subset of requirements.txt, isolated in
# $OPS_HOME/.venv so the retrieval planes never drag in the file-processing packages (Pillow /
# trafilatura / mlx-vlm) that belong to the `models` layer. requirements-search.txt is the source of
# truth when present (the committed, human-followable install story); this inline mirror is the
# fallback for a lean vault that dropped the file. Env markers ride through pip on the command line.
SEARCH_DEPS = [
    'lancedb>=0.25,<0.26 ; platform_system == "Darwin" and platform_machine == "x86_64"',
    'lancedb>=0.33 ; platform_system != "Darwin" or platform_machine != "x86_64"',
    "fastembed>=0.4",
]


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


def _ollama_present() -> bool:
    """Is the ollama binary on PATH? (The external prerequisite for pulling any local model.)"""
    return shutil.which("ollama") is not None


def _venv_python() -> "os.PathLike[str] | str":
    """The optional venv's interpreter path (may not exist yet)."""
    return paths.OPS_HOME / ".venv" / "bin" / "python3"


def _usable_venv_python() -> str | None:
    """The ONE "is the venv interpreter actually usable" probe, shared by the dispatcher's interpreter
    choice, `_search_interpreter`, and the create-if-missing logic (FIX 3). Returns the path ONLY if
    `$OPS_HOME/.venv/bin/python3` exists AND actually STARTS — mirroring the dispatcher's `-x`+start
    probe. A half-built or ABI-broken venv (dir/symlink present but python won't run) returns None so
    callers REPAIR it rather than trusting an existing `.venv` dir as complete. Never raises."""
    vp = _venv_python()
    try:
        r = subprocess.run([str(vp), "-c", ""], capture_output=True, timeout=10)
        return str(vp) if r.returncode == 0 else None
    except Exception:
        return None


def _ensure_venv(res: dict, *, fake: bool) -> None:
    """Provision `$OPS_HOME/.venv` as the single home for ALL optional deps (search + models, ADR-009 /
    FIX 2). Idempotent: a usable venv is left untouched; a MISSING or half-built/broken one is
    (re)created via the same start-probe as the dispatcher (FIX 3), so a partial `.venv` dir can't wedge
    a later `_venv_pip`. Records the create command in `res['ran']`. In fake/dry mode it only previews
    the create (records the string, runs nothing)."""
    venv = paths.OPS_HOME / ".venv"
    if _fake(fake):
        res["ran"].append(_run([sys.executable, "-m", "venv", str(venv)], fake=fake))
        return
    if _usable_venv_python() is not None:
        return
    # Missing, or present-but-unstartable (stale symlink / ABI break): clear any partial tree so the
    # create can't trip on it, then build fresh. .venv is a disposable, rebuildable cache (ADR-009).
    if venv.exists():
        shutil.rmtree(venv, ignore_errors=True)
    res["ran"].append(_run([sys.executable, "-m", "venv", str(venv)], fake=fake))


def _search_interpreter() -> str:
    """The interpreter the dispatcher would pick for verbs: the repo-local .venv python when it exists
    AND starts (ADR-009 / FIX 3), else whichever python3 is running us. What `deps-importable` must
    probe."""
    return _usable_venv_python() or sys.executable


def _deps_importable() -> bool:
    """OPERATIONAL probe (Task 10): can the dispatcher-selected interpreter actually import BOTH
    vector-plane deps? A file being pip-installed isn't enough — `ops index` imports through the
    venv, so we import through the same interpreter. Never raises."""
    interp = _search_interpreter()
    try:
        r = subprocess.run([interp, "-c", "import lancedb, fastembed"],
                           capture_output=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def _index_built() -> bool:
    return (paths.OPS_HOME / ".index" / "ops.sqlite").exists()


def _search_pip_args() -> list[str]:
    """`pip install` args for the search-only set: `-r requirements-search.txt` when the committed
    file is present, else the inline SEARCH_DEPS mirror (lean vault)."""
    req = paths.OPS_HOME / "requirements-search.txt"
    if req.exists():
        return ["-r", str(req)]
    return list(SEARCH_DEPS)


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
    """Invoke a sibling verb through the DISPATCHER (Task 9, "one door") — not `bin/<verb>/run.py`
    directly — so doctor/models/job/index re-enter the guardrail + resolver + logs like any other
    caller. Non-recursive (none of these verbs call setup). OPS_SETUP_FAKE keeps a dry-run inert
    (the display string is recorded, nothing runs). The dispatcher itself prefers the .venv python
    (ADR-009), so a re-entered `ops index` sees the vector deps with no PATH surgery here."""
    return _run([str(paths.OPS_HOME / "ops"), verb, *args], fake=fake)


def _venv_pip(*pkgs_or_reqs: str, fake: bool = False) -> str:
    """`pip install` into the optional venv specifically (Task 10 / FIX 2) — the isolated interpreter
    the dispatcher prefers, never the caller's site-packages. ALL optional deps (search + models) land
    here, so the stdlib floor stays clean and the dispatcher sees every optional dep consistently."""
    return _run([str(_venv_python()), "-m", "pip", "install", *pkgs_or_reqs], fake=fake)


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
    """OPERATIONAL readiness (Task 10): "ready" means search actually works end to end, not merely
    that a wheel is on disk. Core = deps import through the dispatcher's interpreter + the embed model
    is pulled + the index is built; OPS_VECTORS/OPS_RERANK are advisory (surfaced as a handoff if
    unset, never blocking). ollama is the hard external prerequisite — absent, the layer is `blocked`
    with the exact install command (Task 8), because `advance` would otherwise crash pulling the
    model."""
    model = _embed_model()
    deps = _deps_importable()
    model_pulled = _ollama_has(model)
    index_built = _index_built()
    vectors_env = _truthy(os.environ.get("OPS_VECTORS"))
    rerank_env = _truthy(os.environ.get("OPS_RERANK"))
    items = [
        {"id": "deps-importable", "title": "lancedb + fastembed importable", "ok": deps},
        {"id": "model-pulled", "title": model, "ok": model_pulled},
        {"id": "index-built", "title": ".index/ops.sqlite", "ok": index_built},
        {"id": "OPS_VECTORS", "title": "OPS_VECTORS=1", "ok": vectors_env, "advisory": True},
        {"id": "OPS_RERANK", "title": "OPS_RERANK=1", "ok": rerank_env, "advisory": True},
    ]
    if not _ollama_present():
        return _row(layer, "blocked", "ollama is required to pull the embedding model", items,
                    "install ollama: https://ollama.com")
    core = [deps, model_pulled, index_built]
    if all(core):
        # Operational; nudge the advisory env flags so retrieval actually uses the vector/rerank arms.
        nxt = "" if (vectors_env and rerank_env) else "export OPS_VECTORS=1 OPS_RERANK=1"
        detail = "semantic search ready" if (vectors_env and rerank_env) else \
            "semantic search operational (set OPS_VECTORS=1 / OPS_RERANK=1 to enable the arms)"
        return _row(layer, "ready", detail, items, nxt)
    state = "partial" if any(core) else "absent"
    return _row(layer, state, "semantic search prerequisites are incomplete", items, "ops setup search --yes")


def _status_backups(layer: Layer) -> dict:
    config_ok = (paths.OPS_HOME / ".backup" / "config.json").exists()
    restic_ok = shutil.which("restic") is not None
    items = [
        {"id": "config", "title": ".backup/config.json", "ok": config_ok},
        {"id": "restic", "title": "restic", "ok": restic_ok},
    ]
    if config_ok and restic_ok:
        return _row(layer, "ready", "backup configuration ready", items)
    # The external binary is the hard prerequisite: name the exact install command (Task 8) rather
    # than deferring to the generic init handoff, which can't proceed without restic anyway.
    if not restic_ok:
        return _row(layer, "blocked", "restic is required for encrypted off-machine backups", items,
                    "install restic: brew install restic")
    return _row(layer, "blocked", "backup setup needs human initialization", items, layer.handoff)


def _status_models(layer: Layer) -> dict:
    vlm_model = (os.environ.get("OPS_VLM", "qwen3-vl:4b") or "qwen3-vl:4b").strip()
    vlm_ok = False if vlm_model.lower() == "none" else (imagelib._has_mlx() or (_ollama_has(vlm_model) if imagelib._has_ollama() else False))
    items = [
        {"id": "enrich", "title": enrichlib.DEFAULT_MODEL, "ok": _ollama_has(enrichlib.DEFAULT_MODEL)},
        {"id": "ocr", "title": imagelib.ocr_backend_label() or "none", "ok": imagelib.ocr_backend_label() is not None},
        {"id": "vlm", "title": vlm_model, "ok": vlm_ok},
        {"id": "stt", "title": "speech-to-text runtime", "ok": any(_has(m) for m in ("parakeet_mlx", "mlx_whisper", "faster_whisper"))},
    ]
    # ollama backs the enrich/embed model pulls; without it `advance` (→ `ops models pull`) can't run.
    # Report `blocked` with the install command (Task 8) instead of letting it crash mid-pull.
    if not _ollama_present():
        return _row(layer, "blocked", "ollama is required for local model runtimes", items,
                    "install ollama: https://ollama.com")
    state = _items_status(items)
    detail = "file-processing models ready" if state == "ready" else "file-processing model layer is incomplete"
    return _row(layer, state, detail, items, "ops setup models --yes" if state != "ready" else "")


def _status_automation(layer: Layer) -> dict:
    # launchd is macOS-only: off Darwin the layer cannot apply at all (Task 8) — report
    # `not_applicable` with a one-line reason rather than a perpetually-"absent" nag the host can
    # never satisfy. Advisory everywhere it surfaces (doctor never fails it; `--all` never attempts it).
    if _platform_system() != "Darwin":
        return _row(layer, "not_applicable", "launchd scheduling is macOS-only (no plists on this host)",
                    [{"id": "launchd", "title": "jobs/launchd/*.plist", "ok": False, "advisory": True}], "")
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
    before = status(layer.id)[0]
    if before["status"] == "ready":
        res["skipped"].append(layer.id)
        return res
    if layer.gate == "blocked":  # static human handoff (backups) — regardless of which piece is missing
        if layer.handoff:
            res["handoff"].append(layer.handoff)
        res["skipped"].append(layer.id)
        return res
    # Dynamic block (Task 8): a missing external binary (ollama) or a host that can't run the layer
    # (not_applicable). Never attempt it — surface the exact remediation from `next` and skip, so
    # `advance` cannot crash mid-install on a prerequisite the status probe already flagged.
    if before["status"] in ("blocked", "not_applicable"):
        if before.get("next"):
            res["handoff"].append(before["next"])
        res["skipped"].append(layer.id)
        return res
    if not _confirm(layer, yes, res):
        return res

    # FIX 5: if a multi-step install fails midway, `res["ran"]` holds the steps that DID succeed. A
    # bare raise loses them (the caller only sees the exception), so attach the partial progress to the
    # exception before re-raising — `_advance_all` reads `ops_partial_ran` to preserve step visibility.
    try:
        if layer.id == "skeleton":
            res["ran"].append(_run_verb("doctor", "--init", fake=fake))
        elif layer.id == "search":
            # Venv-correct, isolated search layer (Task 10 / ADR-009 / FIX 2):
            # (1) ensure $OPS_HOME/.venv (create/repair if missing or broken), (2) install ONLY the
            # search deps into it (never the whole requirements.txt), (3) pull the embed model,
            # (4) re-enter `ops index` — the dispatcher runs it on the .venv python, so lancedb/
            # fastembed import for the build.
            _ensure_venv(res, fake=fake)
            res["ran"].append(_venv_pip(*_search_pip_args(), fake=fake))
            res["ran"].append(_run(["ollama", "pull", _embed_model()], fake=fake))
            res["ran"].append(_run_verb("index", fake=fake))
        elif layer.id == "models":
            # The .venv is the CANONICAL home for ALL optional deps (FIX 2): the file-processing
            # packages install into the SAME venv the dispatcher prefers, so `ops files`/`enrich`/
            # `doctor` see Pillow/trafilatura/mlx-vlm consistently instead of the old silent capability
            # regression (installed into bare python, then invisible once .venv exists).
            res["ran"].append(_run_verb("models", "pull", "--all", "--yes", fake=fake))
            _ensure_venv(res, fake=fake)
            pkgs = ["Pillow", "trafilatura"]
            if _platform_system() == "Darwin" and _platform_machine().lower() in ("arm64", "aarch64"):
                pkgs.append("mlx-vlm")
            res["ran"].append(_venv_pip(*pkgs, fake=fake))
        elif layer.id == "automation":
            res["ran"].append(_run_verb("job", "apply", fake=fake))
    except BaseException as exc:
        exc.ops_partial_ran = list(res["ran"])
        raise
    return res
