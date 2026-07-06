#!/usr/bin/env python3
"""
run_backup_share.py — offline suite for the backup family (Part 5.1) + `ops share` (Part 5.2) +
sweep share hygiene. NEVER contacts a network endpoint: the share transport is short-circuited by
OPS_SHARE_FAKE, and restic paths run only their graceful-degrade branches (restic is not required).
"""
from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def _load_sharelib():
    """Load bin/lib/sharelib.py by file path (bin/lib namespace loses to test/lib on sys.path)."""
    spec = importlib.util.spec_from_file_location("sharelib", REPO / "bin" / "lib" / "sharelib.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(home, *a):
    return subprocess.run(["git", "-C", str(home), *a], capture_output=True, text=True)


def init_git(home):
    git(home, "init", "-q", "-b", "main")
    git(home, "config", "user.email", "t@e"); git(home, "config", "user.name", "t")
    git(home, "config", "commit.gpgsign", "false")


def run(verb, *args, home, roots=None, extra_env=None):
    env = {**os.environ, "OPS_HOME": str(home)}
    if roots:
        env["OPS_ROOTS_HOME"] = str(roots)
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, str(REPO / "bin" / verb / "run.py"), *args],
                          capture_output=True, text=True, env=env)


def main() -> int:
    sl = _load_sharelib()

    # ---------- sharelib: encrypt/decrypt round-trip + expiry + HTML rendering ----------
    if sl.have_crypto():
        pt = b"the quick brown fox <secret>"
        ct, key = sl.encrypt(pt)
        check("encrypt/decrypt round-trips", sl.decrypt(ct, key) == pt)
        check("ciphertext differs from plaintext", ct.encode() != pt and len(ct) > 0)
        bad = sl.encrypt(pt)[1]  # a different random key
        try:
            sl.decrypt(ct, bad); ok = False
        except Exception:
            ok = True
        check("decrypt with wrong key fails", ok)
    else:
        check("no crypto → install hint constant present", bool(sl.CRYPTO_HINT))

    check("parse_expires 7d", sl.parse_expires("7d") == 7 * 86400)
    check("parse_expires 12h", sl.parse_expires("12h") == 12 * 3600)
    try:
        sl.parse_expires("nope"); ok = False
    except ValueError:
        ok = True
    check("parse_expires rejects garbage", ok)

    # wikilink scoping: within-set link → anchor; outside-set → plain text
    docs = [
        {"slug": "alpha", "title": "Alpha", "md": "# Alpha\nsee [[beta]] and [[ghost]]\n"},
        {"slug": "beta", "title": "Beta", "md": "# Beta\nhello\n"},
    ]
    htmldoc = sl.render_bundle(docs)
    check("render: self-contained (inline CSS, no external refs)",
          "<style>" in htmldoc and "http://" not in htmldoc and "<link" not in htmldoc)
    check("render: in-set wikilink → intra-doc anchor", 'href="#note-beta"' in htmldoc)
    check("render: out-of-set wikilink → plain text (no anchor)",
          "ghost" in htmldoc and 'href="#note-ghost"' not in htmldoc)

    # image size cap: resolver returns None over cap → alt text, not a data URI
    small = sl.render_note_html("![pic](x.png)\n", set(), image_resolver=lambda p: sl.data_uri(b"x", "image/png"))
    check("render: under-cap image inlined as data URI", "data:image/png;base64" in small)
    dropped = sl.render_note_html("![pic](big.png)\n", set(), image_resolver=lambda p: None)
    check("render: over-cap image dropped to alt text", "data:image" not in dropped and "pic" in dropped)

    # ---------- share: dry-run render (offline), confirm-gate, fake-transport bookkeeping ----------
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "ops"; roots = Path(td) / "roots"
        (h / "wiki" / "notes").mkdir(parents=True); roots.mkdir()
        init_git(h)
        (h / "wiki" / "notes" / "alpha.md").write_text(
            "---\ntype: note\ntitle: Alpha\ntags: [pub]\n---\n# Alpha\nsee [[beta]] and [[ghost]]\n")
        (h / "wiki" / "notes" / "beta.md").write_text(
            "---\ntype: note\ntitle: Beta\ntags: [pub]\n---\n# Beta\nhi\n")

        # `cryptography` is an optional dep and CI runs this suite stdlib-only, so drive the share
        # CLI in --plain mode when crypto is absent. Plain exercises the identical render / ledger /
        # list / revoke / collection bookkeeping; only the E2E #key URL fragment (asserted
        # separately below) needs the AES layer. On a machine with `cryptography`, PM is empty and
        # the full E2E path runs exactly as before.
        HAVE_CRYPTO = sl.have_crypto()
        PM = [] if HAVE_CRYPTO else ["--plain"]

        # dry-run writes the HTML blob and never publishes
        outp = Path(td) / "alpha.html"
        r = run("share", "alpha", "--dry-run", "--out", str(outp), *PM, home=h)
        check("share dry-run exits 0", r.returncode == 0, r.stdout + r.stderr)
        check("share dry-run wrote HTML, no ledger",
              outp.exists() and not (h / ".share" / "ledger.json").exists())
        blob = outp.read_text() if outp.exists() else ""
        check("share dry-run: single note has no in-set links (beta/ghost plain)",
              "beta" in blob and "ghost" in blob and 'href="#note-' not in blob, blob[:200])

        # confirm-gate: no --yes → EXIT_CONFIRM(3)
        r = run("share", "alpha", *PM, home=h)
        check("share without --yes → exit 3 (needs-yes)", r.returncode == 3, r.stdout + r.stderr)

        # not-found slug
        r = run("share", "nonesuch", "--dry-run", *PM, home=h)
        check("share unknown slug → exit 4", r.returncode == 4, r.stdout + r.stderr)

        # full flow with fake transport: ledger + frontmatter + list + revoke
        fenv = {"OPS_SHARE_FAKE": "1"}
        r = run("share", "alpha", "--expires", "1d", "--yes", "--json", *PM, home=h, extra_env=fenv)
        check("share --yes (fake) exits 0", r.returncode == 0, r.stdout + r.stderr)
        env = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        sid = env.get("data", {}).get("id", "")
        url = env.get("data", {}).get("url", "")
        check("share returns an id", bool(sid), r.stdout)
        if HAVE_CRYPTO:
            check("E2E share url carries the #key fragment", "#" in url, r.stdout)
        else:
            check("plain share url has no #key fragment", bool(url) and "#" not in url, r.stdout)
        led = json.loads((h / ".share" / "ledger.json").read_text())
        check("ledger records the share", any(s["id"] == sid for s in led["shares"]))
        check("frontmatter stamped with share:", "share:" in (h / "wiki" / "notes" / "alpha.md").read_text())

        r = run("share", "list", "--json", home=h)
        rows = [json.loads(l) for l in r.stdout.splitlines()]
        check("share list shows the active share",
              any(x.get("id") == sid and x.get("state") == "active" for x in rows[1:]), r.stdout)

        # revoke: confirm-gate then delete
        r = run("share", "revoke", sid, home=h)
        check("revoke without --yes → exit 3", r.returncode == 3, r.stdout + r.stderr)
        r = run("share", "revoke", sid, "--yes", home=h, extra_env=fenv)
        check("revoke --yes exits 0", r.returncode == 0, r.stdout + r.stderr)
        led = json.loads((h / ".share" / "ledger.json").read_text())
        check("ledger marks the share revoked", any(s["id"] == sid and s.get("revoked") for s in led["shares"]))

        # collection by tag renders both notes
        r = run("share", "collection", "pub", "--dry-run", "--out", str(Path(td) / "coll.html"),
                "--json", *PM, home=h)
        cenv = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        check("collection selects both tagged notes",
              set(cenv.get("data", {}).get("notes", [])) == {"alpha", "beta"}, r.stdout)

        # ---------- sweep share hygiene: expired + edited-since warnings ----------
        import time as _t
        (h / ".share").mkdir(exist_ok=True)
        now = int(_t.time())
        ledger = {"shares": [
            {"id": "expd", "kind": "note", "key": "alpha", "expires_ts": now - 86400,
             "created_ts": now - 200000, "note_paths": ["wiki/notes/alpha.md"]},
            {"id": "editd", "kind": "note", "key": "beta", "expires_ts": now + 86400,
             "created_ts": now - 100000, "note_paths": ["wiki/notes/beta.md"]},
        ]}
        (h / ".share" / "ledger.json").write_text(json.dumps(ledger))
        r = run("sweep", "--json", home=h, extra_env={"OPS_SWEEP_HOME": str(roots)})
        head = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        srows = [json.loads(l) for l in r.stdout.splitlines()[1:]]
        check("sweep reports 2 share warnings", head.get("share_warnings") == 2, r.stdout)
        check("sweep flags the expired share", any(x.get("action") == "expired" for x in srows), r.stdout)
        check("sweep flags the edited-since share", any(x.get("action") == "edited" for x in srows), r.stdout)

    # ---------- backup: bare nag unchanged, status, bundle, drill, init, run-cloud gate ----------
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "ops"; roots = Path(td) / "roots"
        (h / "wiki").mkdir(parents=True)
        (roots / "files").mkdir(parents=True)
        init_git(h)
        (h / "wiki" / "index.md").write_text("# index\n")
        git(h, "add", "-A"); git(h, "commit", "-qm", "init")

        # bare nag still works (byte-compatible): committed but no upstream → at risk, exit 1
        r = run("backup", home=h, roots=roots)
        check("bare backup nag: no upstream → exit 1", r.returncode == 1 and "no upstream" in r.stdout,
              r.stdout + r.stderr)

        # status: unconfigured → exit 1, reports it
        r = run("backup", "status", "--json", home=h, roots=roots)
        check("status unconfigured → exit 1", r.returncode == 1, r.stdout + r.stderr)
        head = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        check("status flags at_risk when unconfigured", head.get("at_risk") is True, r.stdout)

        # run --target cloud without --yes → exit 3 (confirm), before touching restic/config
        r = run("backup", "run", "--target", "cloud", home=h, roots=roots)
        check("backup run cloud without --yes → exit 3", r.returncode == 3, r.stdout + r.stderr)

        # drill without --yes → exit 3
        r = run("backup", "drill", home=h, roots=roots)
        check("backup drill without --yes → exit 3", r.returncode == 3, r.stdout + r.stderr)
        # drill --yes unconfigured (or no restic) → clean error, not a crash
        r = run("backup", "drill", "--yes", home=h, roots=roots)
        check("backup drill --yes unconfigured → clean error (exit 1)", r.returncode == 1, r.stdout + r.stderr)

        # init without --yes → exit 3
        r = run("backup", "init", home=h, roots=roots)
        check("backup init without --yes → exit 3", r.returncode == 3, r.stdout + r.stderr)
        # init --yes → config with op:// references only + rendered plist
        r = run("backup", "init", "--yes", "--local-repo", "/Volumes/Backup/restic-ops",
                "--cloud-repo", "b2:mybucket:ops", home=h, roots=roots)
        check("backup init --yes exits 0", r.returncode == 0, r.stdout + r.stderr)
        cfg = json.loads((h / ".backup" / "config.json").read_text())
        refs = json.dumps(cfg)
        check("config stores op:// references (never resolved)", "op://" in refs)
        check("config resolves NO secret value", "password\":" not in refs.replace("password_ref", ""))
        plist = (h / ".backup" / "com.ops.backup.cloud.plist").read_text()
        check("plist renders launchd job invoking restic directly",
              "restic backup" in plist and "op read" in plist and "com.ops.backup.cloud" in plist)
        check("plist is NOT auto-installed (LaunchAgents untouched)",
              not (Path(td) / "Library").exists())

        # status now configured: local repo path unreachable/empty → still exit 1, reports stale/hint
        r = run("backup", "status", "--json", home=h, roots=roots)
        check("status configured-but-unbacked → exit 1", r.returncode == 1, r.stdout + r.stderr)

    # ---------- backup bundle: valid git bundles + retention (fully offline) ----------
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "ops"; roots = Path(td) / "roots"
        (h / "wiki").mkdir(parents=True)
        init_git(h)
        (h / "wiki" / "index.md").write_text("# index\n")
        git(h, "add", "-A"); git(h, "commit", "-qm", "init")
        # a remote-less work repo — the exact hole bundle closes
        wrepo = roots / "work" / "labs" / "demo"; wrepo.mkdir(parents=True)
        init_git(wrepo)
        (wrepo / "readme.md").write_text("# demo\n")
        git(wrepo, "add", "-A"); git(wrepo, "commit", "-qm", "init")

        r = run("backup", "bundle", "--dry-run", "--json", home=h, roots=roots)
        head = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        check("bundle dry-run writes nothing but plans repos", head.get("dry_run") is True
              and head.get("bundled") >= 2 and not (roots / "files" / "backups").exists(), r.stdout)

        r = run("backup", "bundle", "--json", home=h, roots=roots)
        check("bundle exits 0", r.returncode == 0, r.stdout + r.stderr)
        bdir = roots / "files" / "backups" / "bundles"
        bundles = sorted(bdir.glob("*.bundle")) if bdir.exists() else []
        check("bundle produced >=2 .bundle files (ops + work repo)", len(bundles) >= 2, str(bundles))
        ok = all(git(h, "bundle", "verify", str(b)).returncode == 0 for b in bundles)
        check("every produced bundle is a valid git bundle", ok)

        # retention: run 4 more times with keep=2 → at most 2 per repo
        for _ in range(4):
            run("backup", "bundle", home=h, roots=roots, extra_env={"OPS_BUNDLE_KEEP": "2"})
        ops_bundles = list(bdir.glob("ops-*.bundle"))
        check("retention keeps last N per repo", len(ops_bundles) <= 2, str(ops_bundles))

    print(f"\n{BOLD}Backup family + share (Part 5.1/5.2) — {len(results)} checks{RESET}\n")
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark} {name:<52}" + (f" {DIM}{detail.strip()[:90]}{RESET}" if (detail and not ok) else ""))
    failed = len(results) - passed
    print(f"\n{BOLD}Result:{RESET} {GREEN}{passed} passed{RESET}, "
          f"{(RED if failed else DIM)}{failed} failed{RESET}, {len(results)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
