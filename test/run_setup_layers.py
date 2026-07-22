#!/usr/bin/env python3
"""Offline behavior tests for bin/lib/setuplib.py."""
from __future__ import annotations
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path = [str(REPO / "bin"), *[p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]]

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def reload_setuplib(home: Path):
    os.environ["OPS_HOME"] = str(home)
    from lib import paths  # noqa: E402
    importlib.reload(paths)
    from lib import setuplib  # noqa: E402
    return importlib.reload(setuplib)


def make_home(tmp: Path) -> Path:
    home = tmp / "ops"
    home.mkdir(parents=True)
    return home


def seed_skeleton(mod, home: Path):
    for rel in mod.REQUIRED_DIRS:
        (home / rel).mkdir(parents=True, exist_ok=True)
    (home / ".obsidian").mkdir()


def patch_probe(mod, **values):
    old = {}
    for name, value in values.items():
        old[name] = getattr(mod, name)
        setattr(mod, name, value)
    return old


def restore(mod, old):
    for name, value in old.items():
        setattr(mod, name, value)


def run_setup(args, home: Path, *, fake: bool = True):
    env = {
        **os.environ,
        "OPS_HOME": str(home),
        "PYTHONPATH": str(REPO / "bin"),
        "OPS_EMBED_MODEL": "ops-setup-test-embed-model",
    }
    if fake:
        env["OPS_SETUP_FAKE"] = "1"
    else:
        env.pop("OPS_SETUP_FAKE", None)
    return subprocess.run([sys.executable, str(REPO / "bin" / "setup" / "run.py"), *args],
                          capture_output=True, text=True, env=env)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        home = make_home(tmp)
        mod = reload_setuplib(home)

        ids = [layer.id for layer in mod.LAYERS]
        check("registry has L1-L5 in order", ids == ["skeleton", "search", "backups", "models", "automation"], str(ids))
        check("registry exposes layer shape",
              all(layer.id and layer.title and layer.gate and isinstance(layer.required, bool) for layer in mod.LAYERS),
              str(mod.LAYERS))
        check("REQUIRED_DIRS moved into shared lib", "wiki" in mod.REQUIRED_DIRS and "tasks/active" in mod.REQUIRED_DIRS,
              str(mod.REQUIRED_DIRS))

        rows = mod.status()
        valid = {"ready", "partial", "absent", "blocked", "not_applicable"}
        check("status returns public rows", len(rows) == 5 and all({"id", "title", "status", "required", "detail", "items", "next"}.issubset(r) for r in rows), str(rows))
        check("status values are valid", {r["status"] for r in rows} <= valid, str(rows))
        check("single-layer status filters", [r["id"] for r in mod.status("search")] == ["search"])

        # Skeleton: absent -> ready and idempotent advance.
        s0 = mod.status("skeleton")[0]
        check("skeleton absent in empty vault", s0["status"] in ("partial", "absent") and s0["required"], str(s0))
        os.environ["OPS_SETUP_FAKE"] = "1"
        a0 = mod.advance("skeleton", yes=False, fake=True)
        check("fake skeleton advance records doctor init", a0["ran"] and "doctor" in a0["ran"][0], str(a0))
        seed_skeleton(mod, home)
        s1 = mod.status("skeleton")[0]
        check("skeleton ready after required dirs exist", s1["status"] == "ready", str(s1))
        a1 = mod.advance("skeleton", yes=False, fake=True)
        check("skeleton advance is idempotent when ready", not a1["ran"] and "skeleton" in a1["skipped"], str(a1))

        # The Obsidian config pack is ADVISORY: its .obsidian/*.json items stay VISIBLE in the
        # skeleton row (so `ops setup` surfaces their state) but never flip the required layer to
        # non-ready — skeleton readiness depends only on REQUIRED_DIRS. A fresh clone that hasn't
        # seeded .obsidian/ yet must still let `ops doctor` pass.
        (home / "templates" / "obsidian").mkdir(parents=True, exist_ok=True)
        (home / "templates" / "obsidian" / "app.json").write_text("{}", encoding="utf-8")
        (home / "templates" / "obsidian" / "appearance.json").write_text("{}", encoding="utf-8")
        (home / ".obsidian" / "app.json").unlink(missing_ok=True)
        (home / ".obsidian" / "appearance.json").unlink(missing_ok=True)
        s_pack_missing = mod.status("skeleton")[0]
        check("skeleton stays ready when obsidian pack unseeded (advisory), but reports the item",
              s_pack_missing["status"] == "ready"
              and any(i["id"] == ".obsidian/app.json" and not i["ok"] and i.get("advisory")
                      for i in s_pack_missing["items"]),
              str(s_pack_missing))
        (home / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")
        s_pack_partial = mod.status("skeleton")[0]
        check("skeleton ready with a partially-seeded obsidian pack; missing file still reported",
              s_pack_partial["status"] == "ready"
              and any(i["id"] == ".obsidian/appearance.json" and not i["ok"] and i.get("advisory")
                      for i in s_pack_partial["items"]),
              str(s_pack_partial))
        (home / ".obsidian" / "appearance.json").write_text("{}", encoding="utf-8")
        s_pack_seeded = mod.status("skeleton")[0]
        check("skeleton ready with all obsidian json templates seeded (advisory items ok)",
              s_pack_seeded["status"] == "ready"
              and all(i["ok"] for i in s_pack_seeded["items"] if i.get("advisory")),
              str(s_pack_seeded))

        # Search: absent / partial / ready / blocked and the confirm gate. Readiness is OPERATIONAL
        # now (Task 10): deps-importable (probed via the venv/dispatcher interpreter) + model-pulled +
        # index-built; OPS_VECTORS/OPS_RERANK are advisory. ollama is the hard external prerequisite.
        # Patch the probes hermetically so the machine's real ollama/venv state never leaks in.
        def _search_probes(deps, model, index, ollama=True):
            return patch_probe(mod,
                               _deps_importable=lambda: deps,
                               _ollama_has=lambda m: model,
                               _index_built=lambda: index,
                               _ollama_present=lambda: ollama)

        old = _search_probes(False, False, False)
        try:
            search_absent = mod.status("search")[0]
            check("search absent when no components ready", search_absent["status"] == "absent", str(search_absent))
        finally:
            restore(mod, old)

        old = _search_probes(True, False, False)
        try:
            search_partial = mod.status("search")[0]
            check("search partial reports item state", search_partial["status"] == "partial"
                  and any(i["id"] == "deps-importable" and i["ok"] for i in search_partial["items"]), str(search_partial))
        finally:
            restore(mod, old)

        old = _search_probes(True, True, True)
        try:
            search_ready = mod.status("search")[0]
            check("search ready when deps, model, and index are operational", search_ready["status"] == "ready", str(search_ready))
        finally:
            restore(mod, old)

        # Task 8: ollama absent → blocked with the EXACT install command, never absent/partial.
        old = _search_probes(True, False, False, ollama=False)
        try:
            search_blocked = mod.status("search")[0]
            check("search blocked with install hint when ollama is missing",
                  search_blocked["status"] == "blocked" and "install ollama" in search_blocked["next"],
                  str(search_blocked))
        finally:
            restore(mod, old)

        old = _search_probes(False, False, False)
        try:
            gated = mod.advance("search", yes=False, fake=True)
            check("search advance without yes asks for confirmation", gated["confirm_needed"] and not gated["ran"], str(gated))
            allowed = mod.advance("search", yes=True, fake=True)
            joined = " | ".join(allowed["ran"])
            check("search fake advance records venv, search-only pip, ollama pull, index build",
                  len(allowed["ran"]) == 4 and "venv" in allowed["ran"][0] and "pip install" in allowed["ran"][1]
                  and "ollama pull" in allowed["ran"][2] and "index" in allowed["ran"][3]
                  and "lancedb" in joined and "fastembed" in joined
                  and "Pillow" not in joined and "trafilatura" not in joined,  # search-only, NOT the models deps
                  str(allowed))
        finally:
            restore(mod, old)

        old = _search_probes(False, False, False)
        real_run = mod.subprocess.run
        def boom(*args, **kwargs):
            raise AssertionError(f"subprocess.run should not execute in fake mode: {args}")
        mod.subprocess.run = boom
        try:
            fake_safe = mod.advance("search", yes=True, fake=True)
            check("OPS_SETUP_FAKE records without subprocess execution", len(fake_safe["ran"]) == 4, str(fake_safe))
        except AssertionError as e:
            check("OPS_SETUP_FAKE records without subprocess execution", False, str(e))
        finally:
            mod.subprocess.run = real_run
            restore(mod, old)

        # Backups: blocked handoff, never auto-run.
        backups = mod.advance("backups", yes=True, fake=True)
        check("backups advance is blocked handoff", backups["handoff"] == ["ops backup init"] and not backups["ran"], str(backups))

        # Models: fake command recording includes conditional package support but no real execution.
        # Patch ollama present (else Task 8 reports the layer `blocked` and advance would skip it).
        old = patch_probe(mod,
                          _platform_system=lambda: "Darwin",
                          _platform_machine=lambda: "arm64",
                          _ollama_present=lambda: True,
                          _ollama_has=lambda model: False)
        try:
            models = mod.advance("models", yes=True, fake=True)
            joined = " | ".join(models["ran"])
            check("models fake advance records model pull and package installs",
                  "models" in joined and "pull" in joined and "Pillow" in joined and "trafilatura" in joined and "mlx-vlm" in joined,
                  str(models))
        finally:
            restore(mod, old)

        # Task 8: automation off macOS is not_applicable (advisory), with a one-line reason.
        old = patch_probe(mod, _platform_system=lambda: "Linux")
        try:
            auto_na = mod.status("automation")[0]
            check("automation not_applicable off macOS with a reason",
                  auto_na["status"] == "not_applicable" and "macOS" in auto_na["detail"], str(auto_na))
            na_adv = mod.advance("automation", yes=True, fake=True)
            check("advance skips a not_applicable layer (never attempts it)",
                  not na_adv["ran"] and "automation" in na_adv["skipped"], str(na_adv))
        finally:
            restore(mod, old)

        # Task 8: models blocked (ollama absent) → advance skips with the install hint, never crashes.
        old = patch_probe(mod, _ollama_present=lambda: False, _ollama_has=lambda model: False)
        try:
            m_blocked = mod.status("models")[0]
            blk_adv = mod.advance("models", yes=True, fake=True)
            check("models blocked when ollama missing → advance skips with hint, no run",
                  m_blocked["status"] == "blocked" and not blk_adv["ran"]
                  and any("install ollama" in h for h in blk_adv["handoff"]), str((m_blocked, blk_adv)))
        finally:
            restore(mod, old)

        # Automation and repeated advance support all-style orchestration order.
        ordered = []
        for layer in mod.LAYERS:
            res = mod.advance(layer.id, yes=True, fake=True)
            ordered.append(layer.id)
            check(f"advance {layer.id} returns public result",
                  {"ran", "skipped", "handoff", "confirm_needed"}.issubset(res), str(res))
        check("repeated advance follows registry order", ordered == ids, str(ordered))

        try:
            mod.status("bogus")
            unknown_status_ok = False
        except ValueError as e:
            unknown_status_ok = "unknown layer" in str(e)
        check("unknown layer status is clear error", unknown_status_ok)

        try:
            mod.advance("bogus", yes=True, fake=True)
            unknown_advance_ok = False
        except ValueError as e:
            unknown_advance_ok = "unknown layer" in str(e)
        check("unknown layer advance is clear error", unknown_advance_ok)

        # --- Best-effort --all (Task 8): a failure in ONE attempted AUTO layer must not abort the
        # others; only an ATTEMPTED failure yields a nonzero exit; ready/blocked/not_applicable layers
        # are skipped (not attempted). Drive the real bin/setup/run.py:_advance_all with stubbed
        # status/advance so no real installs run. ---
        import contextlib as _ctx
        import io as _io
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("setup_run_besteffort", REPO / "bin" / "setup" / "run.py")
        setup_run = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(setup_run)

        _ALL_STATUS = {"skeleton": "partial", "search": "absent", "backups": "blocked",
                       "models": "not_applicable", "automation": "absent"}

        def fake_status(layer_id=None):
            def row(i):
                return {"id": i, "title": i, "status": _ALL_STATUS[i], "required": i == "skeleton",
                        "detail": "", "items": [], "next": f"next-{i}"}
            order = ["skeleton", "search", "backups", "models", "automation"]
            return [row(layer_id)] if layer_id else [row(i) for i in order]

        def fake_advance(layer_id, *, yes, fake):
            if layer_id == "search":
                raise subprocess.CalledProcessError(1, ["ops", "index"])
            r = mod._result()
            r["ran"].append(f"did {layer_id}")
            return r

        _saved = (setup_run.setuplib.status, setup_run.setuplib.advance)
        setup_run.setuplib.status = fake_status
        setup_run.setuplib.advance = fake_advance
        try:
            _buf = _io.StringIO()
            with _ctx.redirect_stdout(_buf):
                rc = setup_run._advance_all(yes=True)
            out = _buf.getvalue()
            check("best-effort --all: one failing layer does not abort the rest (exit 1)", rc == 1, out)
            check("best-effort --all: layers after the failure still ran",
                  "did skeleton" in out and "did automation" in out and "FAILED" in out, out)
            check("best-effort --all: not_applicable/blocked layers are skipped, not attempted",
                  "models: skipped" in out and "did models" not in out, out)
        finally:
            setup_run.setuplib.status, setup_run.setuplib.advance = _saved

        # --- FIX 2: the models layer installs its deps into the .venv (the dispatcher-preferred
        # interpreter), NOT bare sys.executable — closing the silent capability regression. ---
        old = patch_probe(mod, _platform_system=lambda: "Darwin", _platform_machine=lambda: "arm64",
                          _ollama_present=lambda: True, _ollama_has=lambda model: False)
        try:
            models_v = mod.advance("models", yes=True, fake=True)
            joined_v = " | ".join(models_v["ran"])
            venv_py = str(mod._venv_python())
            check("FIX 2: models ensures the .venv (records a `-m venv` create)",
                  any("-m venv" in c for c in models_v["ran"]), str(models_v["ran"]))
            check("FIX 2: models deps pip-install into the .venv interpreter, not bare python",
                  venv_py in joined_v and "Pillow" in joined_v and "trafilatura" in joined_v
                  and "mlx-vlm" in joined_v, str(models_v["ran"]))
            check("FIX 2: no models step targets the bare interpreter's pip",
                  not any(c.startswith(sys.executable + " -m pip") for c in models_v["ran"]),
                  str(models_v["ran"]))
        finally:
            restore(mod, old)

        # --- FIX 4: the confirm gate must IGNORE skipped (blocked/not_applicable/ready) layers. When
        # every confirm-class AUTO layer is blocked/not_applicable, `--all` attempts nothing and must
        # NOT demand --yes (that was a spurious exit 3, e.g. on a host with no ollama). ---
        _F4_STATUS = {"skeleton": "ready", "search": "blocked", "backups": "blocked",
                      "models": "not_applicable", "automation": "ready"}

        def f4_status(layer_id=None):
            def row(i):
                return {"id": i, "title": i, "status": _F4_STATUS[i], "required": i == "skeleton",
                        "detail": "", "items": [], "next": f"next-{i}"}
            order = ["skeleton", "search", "backups", "models", "automation"]
            return [row(layer_id)] if layer_id else [row(i) for i in order]

        def f4_advance(layer_id, *, yes, fake):
            r = mod._result()
            r["ran"].append(f"did {layer_id}")
            return r

        _saved4 = (setup_run.setuplib.status, setup_run.setuplib.advance)
        setup_run.setuplib.status = f4_status
        setup_run.setuplib.advance = f4_advance
        try:
            _buf = _io.StringIO()
            f4_exit = None
            try:
                with _ctx.redirect_stdout(_buf):
                    f4_exit = setup_run._advance_all(yes=False)  # NO --yes on purpose
            except SystemExit as e:  # a spurious confirm gate would exit 3 here
                f4_exit = e.code
            check("FIX 4 (--all): no --yes demanded when only blocked/not_applicable confirm layers",
                  f4_exit == 0, str(f4_exit) + _buf.getvalue())
            # And the single-layer path: a BLOCKED confirm layer must not exit 3 for a missing --yes.
            _buf2 = _io.StringIO()
            one_exit = None
            try:
                with _ctx.redirect_stdout(_buf2):
                    one_exit = setup_run._advance_one("search", yes=False)  # search is BLOCKED above
            except SystemExit as e:
                one_exit = e.code
            check("FIX 4 (single-layer): a BLOCKED confirm layer does not exit 3 for missing --yes",
                  one_exit != 3, str(one_exit) + _buf2.getvalue())
        finally:
            setup_run.setuplib.status, setup_run.setuplib.advance = _saved4

        # --- FIX 5: best-effort `--all` preserves partial progress (steps that ran before a failure)
        # AND aggregates every blocked/skipped layer's `next` remediation into the top-level handoff. ---
        _F5_STATUS = {"skeleton": "absent", "search": "absent", "backups": "blocked",
                      "models": "blocked", "automation": "absent"}

        def f5_status(layer_id=None):
            def row(i):
                return {"id": i, "title": i, "status": _F5_STATUS[i], "required": i == "skeleton",
                        "detail": "", "items": [], "next": f"next-{i}"}
            order = ["skeleton", "search", "backups", "models", "automation"]
            return [row(layer_id)] if layer_id else [row(i) for i in order]

        def f5_advance(layer_id, *, yes, fake):
            if layer_id == "search":  # ran 2 steps, then blew up on the 3rd
                exc = subprocess.CalledProcessError(1, ["ops", "index"])
                exc.ops_partial_ran = ["python -m venv .venv",
                                       ".venv/bin/python3 -m pip install lancedb fastembed"]
                raise exc
            r = mod._result()
            r["ran"].append(f"did {layer_id}")
            return r

        _saved5 = (setup_run.setuplib.status, setup_run.setuplib.advance)
        setup_run.setuplib.status = f5_status
        setup_run.setuplib.advance = f5_advance
        try:
            _buf5 = _io.StringIO()
            with _ctx.redirect_stdout(_buf5):
                rc5 = setup_run._advance_all(yes=True)
            out5 = _buf5.getvalue()
            check("FIX 5: an attempted-layer failure still exits 1", rc5 == 1, out5)
            check("FIX 5: partial progress (steps run before the failure) is preserved/surfaced",
                  "python -m venv .venv" in out5
                  and ".venv/bin/python3 -m pip install lancedb fastembed" in out5
                  and "FAILED" in out5, out5)
            check("FIX 5: blocked AUTO layer's `next` remediation is aggregated into the handoff",
                  "next-models" in out5, out5)
        finally:
            setup_run.setuplib.status, setup_run.setuplib.advance = _saved5

        os.environ.pop("OPS_SETUP_FAKE", None)

        # --- FIX 3: ONE usable-venv probe (start-probe, not os.path.exists) shared by the dispatcher
        # interpreter choice and the create-if-missing logic; a half-built/broken .venv is REPAIRED,
        # not trusted as complete. (fake env is popped above so _ensure_venv really creates.) ---
        probe_home = make_home(tmp / "venvprobe")
        mod3 = reload_setuplib(probe_home)
        check("FIX 3: usable-venv probe returns None when .venv is absent",
              mod3._usable_venv_python() is None)
        broken_bin = probe_home / ".venv" / "bin"
        broken_bin.mkdir(parents=True)
        (broken_bin / "python3").write_text("#!/nonexistent/interpreter\nnot a real python\n")
        os.chmod(broken_bin / "python3", 0o755)
        check("FIX 3: usable-venv probe returns None for a present-but-unstartable .venv python",
              mod3._usable_venv_python() is None)
        check("FIX 3: _search_interpreter falls back to sys.executable when the venv is broken",
              mod3._search_interpreter() == sys.executable)
        res_repair = mod3._result()
        mod3._ensure_venv(res_repair, fake=False)
        check("FIX 3: _ensure_venv repairs a half-built .venv into a startable interpreter",
              any("venv" in c for c in res_repair["ran"]) and mod3._usable_venv_python() is not None,
              str(res_repair["ran"]))
        res_idem = mod3._result()
        mod3._ensure_venv(res_idem, fake=False)
        check("FIX 3: _ensure_venv is idempotent over an already-usable venv (no re-create)",
              res_idem["ran"] == [], str(res_idem["ran"]))
        mod = reload_setuplib(home)  # restore module state for any later in-process use

        # --- FIX 1: the `ops` dispatcher must PROBE that .venv/bin/python3 actually starts, not just
        # test `-x`. A broken (executable-but-unstartable) venv python must fall back to bare python3
        # so ops keeps working, instead of returning 126/127 on every verb. Build an OPS_HOME that
        # mirrors the repo (symlinks) but carries a deliberately-broken .venv, then run `ops help`. ---
        broken_home = tmp / "brokenvenv"
        broken_home.mkdir()
        for entry in REPO.iterdir():
            if entry.name in (".venv", ".git", ".orchestrate", "__pycache__"):
                continue
            os.symlink(entry, broken_home / entry.name)
        vbin = broken_home / ".venv" / "bin"
        vbin.mkdir(parents=True)
        (vbin / "python3").write_text("#!/nonexistent/interp\nnot a real python\n")
        os.chmod(vbin / "python3", 0o755)
        f1_env = {**os.environ, "OPS_HOME": str(broken_home)}
        f1_env.pop("OPS_SETUP_FAKE", None)
        f1 = subprocess.run([str(REPO / "ops"), "help"], capture_output=True, text=True, env=f1_env)
        check("FIX 1: broken/unstartable .venv python → dispatcher falls back to bare python3, ops runs",
              f1.returncode == 0 and "126" not in (f1.stderr[-40:] or ""),
              (f1.stderr + f1.stdout)[:400])

        # Verb surface: subprocess tests exercise the real command boundary.
        cli_home = make_home(tmp / "cli")
        dashboard = run_setup([], cli_home)
        check("setup dashboard exits ok", dashboard.returncode == 0, dashboard.stderr + dashboard.stdout)
        check("setup dashboard lists five layers",
              all(layer in dashboard.stdout for layer in ("skeleton", "search", "backups", "models", "automation")),
              dashboard.stdout)
        check("setup dashboard shows next commands", "ops setup search --yes" in dashboard.stdout, dashboard.stdout)

        json_dash = run_setup(["--json"], cli_home)
        try:
            lines = [json.loads(ln) for ln in json_dash.stdout.splitlines() if ln.strip()]
            json_ok = json_dash.returncode == 0 and len(lines) == 6 and lines[0]["count"] == 5
        except Exception as e:
            lines = []
            json_ok = False
            json_dash.stderr += str(e)
        check("setup --json emits header plus five parseable layer rows", json_ok, json_dash.stdout + json_dash.stderr)
        check("setup --json rows expose public fields",
              bool(lines) and all({"id", "title", "status", "required", "detail", "items", "next"}.issubset(r) for r in lines[1:]),
              str(lines))

        gated_cli = run_setup(["search"], cli_home)
        check("setup search without yes exits confirm", gated_cli.returncode == 3, gated_cli.stderr + gated_cli.stdout)
        check("setup search confirm includes rerun hint",
              "re-run: ops setup search --yes" in (gated_cli.stderr + gated_cli.stdout),
              gated_cli.stderr + gated_cli.stdout)

        gated_json = run_setup(["search", "--json"], cli_home)
        try:
            gated_env = json.loads(gated_json.stdout)
            gated_json_ok = (gated_json.returncode == 3
                             and gated_env["ok"] is False
                             and gated_env["verb"] == "setup"
                             and gated_env["error"]["code"] == 3
                             and gated_env["error"]["hint"] == "re-run: ops setup search --yes")
        except Exception as e:
            gated_json_ok = False
            gated_json.stderr += str(e)
        check("setup search --json confirm emits stable error envelope", gated_json_ok,
              gated_json.stderr + gated_json.stdout)

        all_preview = run_setup(["--all"], cli_home)
        check("setup --all without yes exits confirm", all_preview.returncode == 3, all_preview.stderr + all_preview.stdout)
        check("setup --all names confirm layers", "search" in all_preview.stderr and "models" in all_preview.stderr,
              all_preview.stderr + all_preview.stdout)

        backups_cli = run_setup(["backups", "--yes"], cli_home)
        check("setup backups --yes exits ok", backups_cli.returncode == 0, backups_cli.stderr + backups_cli.stdout)
        check("setup backups --yes reports handoff", "ops backup init" in backups_cli.stdout,
              backups_cli.stderr + backups_cli.stdout)

        unknown_cli = run_setup(["bogus"], cli_home)
        check("setup unknown layer exits usage", unknown_cli.returncode == 2, unknown_cli.stderr + unknown_cli.stdout)
        check("setup unknown layer lists valid ids",
              all(layer in unknown_cli.stderr for layer in ("skeleton", "search", "backups", "models", "automation")),
              unknown_cli.stderr + unknown_cli.stdout)

        fake_yes = run_setup(["search", "--yes"], cli_home)
        check("setup fake search --yes records commands", fake_yes.returncode == 0 and "ollama pull" in fake_yes.stdout,
              fake_yes.stderr + fake_yes.stdout)

        fail_json = run_setup(["automation", "--yes", "--json"], cli_home, fake=False)
        try:
            fail_env = json.loads(fail_json.stdout)
            fail_json_ok = (fail_json.returncode == 1
                            and fail_env["ok"] is False
                            and fail_env["verb"] == "setup"
                            and fail_env["error"]["code"] == 1
                            and "automation" in fail_env["error"]["message"]
                            and "Traceback" not in fail_json.stderr
                            and "Traceback" not in fail_json.stdout)
        except Exception as e:
            fail_json_ok = False
            fail_json.stderr += str(e)
        check("setup action failure --json emits error envelope without traceback", fail_json_ok,
              fail_json.stderr + fail_json.stdout)

        # --- Task 7a: --dry-run previews without --yes and writes/installs NOTHING. (fake=False here:
        # --dry-run must force the inert path on its own, not lean on OPS_SETUP_FAKE.) ---
        dry_home = make_home(tmp / "dry")
        dry_one = run_setup(["search", "--dry-run", "--json"], dry_home, fake=False)
        try:
            d1 = [json.loads(ln) for ln in dry_one.stdout.splitlines() if ln.strip()]
            dry_one_ok = dry_one.returncode == 0 and d1 and d1[0]["data"].get("dry_run") is True
        except Exception as e:
            dry_one_ok = False
            dry_one.stderr += str(e)
        check("setup search --dry-run: ok envelope w/ dry_run, no --yes needed (confirm-class)",
              dry_one_ok, dry_one.stderr + dry_one.stdout)
        check("setup search --dry-run creates no .venv and no vault folders",
              not (dry_home / ".venv").exists() and not (dry_home / "wiki").exists())

        dry_all = run_setup(["--all", "--dry-run", "--json"], dry_home, fake=False)
        try:
            da = [json.loads(ln) for ln in dry_all.stdout.splitlines() if ln.strip()]
            dry_all_ok = dry_all.returncode == 0 and da and da[0]["data"].get("dry_run") is True
        except Exception as e:
            dry_all_ok = False
            dry_all.stderr += str(e)
        check("setup --all --dry-run: ok envelope w/ dry_run, no --yes needed", dry_all_ok,
              dry_all.stderr + dry_all.stdout)
        check("setup --all --dry-run renders no plists, pulls no model, creates no .venv",
              not (dry_home / ".venv").exists() and not (dry_home / "jobs" / "launchd").exists())

    print(f"\n{BOLD}Setup layer registry — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<66}" + (f" {DIM}{detail.strip()[:100]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
