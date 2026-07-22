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
        valid = {"ready", "partial", "absent", "blocked"}
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

        # Search: absent / partial / ready and confirm gate.
        old = patch_probe(mod,
                          _has=lambda name: False,
                          _ollama_has=lambda model: False)
        try:
            search_absent = mod.status("search")[0]
            check("search absent when no components ready", search_absent["status"] == "absent", str(search_absent))
        finally:
            restore(mod, old)

        old = patch_probe(mod,
                          _has=lambda name: name == "lancedb",
                          _ollama_has=lambda model: False)
        try:
            search_partial = mod.status("search")[0]
            check("search partial reports item state", search_partial["status"] == "partial"
                  and any(i["id"] == "lancedb" and i["ok"] for i in search_partial["items"]), str(search_partial))
        finally:
            restore(mod, old)

        old = patch_probe(mod,
                          _has=lambda name: name in {"lancedb", "fastembed"},
                          _ollama_has=lambda model: True)
        try:
            search_ready = mod.status("search")[0]
            check("search ready when deps and embed model are ready", search_ready["status"] == "ready", str(search_ready))
        finally:
            restore(mod, old)

        old = patch_probe(mod,
                          _has=lambda name: False,
                          _ollama_has=lambda model: False)
        try:
            gated = mod.advance("search", yes=False, fake=True)
            check("search advance without yes asks for confirmation", gated["confirm_needed"] and not gated["ran"], str(gated))
            allowed = mod.advance("search", yes=True, fake=True)
            check("search fake advance records pip and ollama only after yes", len(allowed["ran"]) == 2
                  and "pip" in allowed["ran"][0] and "ollama pull" in allowed["ran"][1], str(allowed))
        finally:
            restore(mod, old)

        old = patch_probe(mod,
                          _has=lambda name: False,
                          _ollama_has=lambda model: False)
        real_run = mod.subprocess.run
        def boom(*args, **kwargs):
            raise AssertionError(f"subprocess.run should not execute in fake mode: {args}")
        mod.subprocess.run = boom
        try:
            fake_safe = mod.advance("search", yes=True, fake=True)
            check("OPS_SETUP_FAKE records without subprocess execution", len(fake_safe["ran"]) == 2, str(fake_safe))
        except AssertionError as e:
            check("OPS_SETUP_FAKE records without subprocess execution", False, str(e))
        finally:
            mod.subprocess.run = real_run
            restore(mod, old)

        # Backups: blocked handoff, never auto-run.
        backups = mod.advance("backups", yes=True, fake=True)
        check("backups advance is blocked handoff", backups["handoff"] == ["ops backup init"] and not backups["ran"], str(backups))

        # Models: fake command recording includes conditional package support but no real execution.
        old = patch_probe(mod,
                          _platform_system=lambda: "Darwin",
                          _platform_machine=lambda: "arm64")
        try:
            models = mod.advance("models", yes=True, fake=True)
            joined = " | ".join(models["ran"])
            check("models fake advance records model pull and package installs",
                  "models" in joined and "pull" in joined and "Pillow" in joined and "trafilatura" in joined and "mlx-vlm" in joined,
                  str(models))
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

        os.environ.pop("OPS_SETUP_FAKE", None)

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
