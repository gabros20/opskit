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

    # ---------- E2E known-answer: the viewer's Web Crypto decrypts sharelib's ciphertext (issue #2 part 2) ----------
    # A frozen (text, blob, key) triple produced by sharelib.encrypt(). The worker VIEWER decrypts in
    # the browser with Web Crypto; Node's identical Web Crypto here pins byte-compatibility of the
    # nonce||ct||tag / b64url wire format. Runs in CI (only needs `node`) even without `cryptography`.
    import shutil as _sh
    kat = json.loads((REPO / "test" / "fixtures" / "share_kat.json").read_text(encoding="utf-8"))
    if sl.have_crypto():
        check("KAT: python sharelib.decrypt round-trips the fixture",
              sl.decrypt(kat["blob"], kat["key"]).decode("utf-8") == kat["text"])
    if _sh.which("node"):
        js = (
            'function d(s){s=s.replace(/-/g,"+").replace(/_/g,"/");s+="=".repeat((4-s.length%4)%4);'
            'return new Uint8Array(Buffer.from(s,"base64"));}'
            '(async()=>{const r=d(process.argv[2]),n=r.slice(0,12),c=r.slice(12);'
            'const k=await crypto.subtle.importKey("raw",d(process.argv[3]),{name:"AES-GCM"},false,["decrypt"]);'
            'const p=await crypto.subtle.decrypt({name:"AES-GCM",iv:n,tagLength:128},k,c);'
            'process.stdout.write(new TextDecoder().decode(p));})()'
            '.catch(e=>{process.stderr.write(String(e));process.exit(1);});')
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
            f.write(js); mjs = f.name
        p = subprocess.run(["node", mjs, kat["blob"], kat["key"]], capture_output=True, text=True)
        os.unlink(mjs)
        check("KAT: Web Crypto (Node) decrypts sharelib ciphertext to the same plaintext",
              p.stdout == kat["text"], p.stdout + p.stderr)
    else:
        check("KAT: node absent — Web Crypto cross-check skipped (informational)", True)

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

    tbl_md = (
        "| Role | Model |\n"
        "|------|-------|\n"
        "| **Default** | `gemma4:e4b` |\n"
        "| HU override | OpenEuroLLM |\n"
    )
    tbl_html = sl.render_note_html(tbl_md, set())
    check("render: GFM table → <table>", "<table>" in tbl_html and "<thead>" in tbl_html and "<tbody>" in tbl_html)
    check("render: table cells not raw pipe paragraphs",
          "<p>| Role |" not in tbl_html and "gemma4:e4b" in tbl_html)
    check("render: table-wrap for mobile scroll", "table-wrap" in sl.render_bundle(
        [{"slug": "t", "title": "T", "md": tbl_md}]))

    pipe_only = "| not a table without separator |\n"
    check("render: lone pipe line stays paragraph", "<table>" not in sl.render_note_html(pipe_only, set()))

    md_b = sl.render_markdown_bundle(docs).encode("utf-8")
    html_b = htmldoc.encode("utf-8")
    packed = sl.pack_bundle(md_b, html_b)
    check("pack/unpack round-trips markdown + html", sl.unpack_bundle(packed) == (md_b, html_b))
    check("pack starts with OPSX magic", packed[:4] == sl.BUNDLE_MAGIC)
    check("markdown bundle single note is file-identical",
          sl.render_markdown_bundle([docs[0]]) == docs[0]["md"])
    md_one = sl.render_markdown_bundle([docs[0]]).encode("utf-8")
    packed_one = sl.pack_bundle(md_one, html_b)
    check("markdown_from_blob plain OPSX", sl.markdown_from_blob(packed_one, None) == docs[0]["md"])
    if sl.have_crypto():
        ct, k = sl.encrypt(packed_one)
        check("encrypted bundle decrypts to OPSX", sl.decrypt(ct, k)[:4] == sl.BUNDLE_MAGIC)
        check("markdown_from_blob E2E ciphertext", sl.markdown_from_blob(ct.encode("ascii"), k) == docs[0]["md"])
        o, sid, key = sl.parse_share_link(f"https://w.example/{'a' * 10}#{k}")
        check("parse_share_link", o == "https://w.example" and sid == "a" * 10 and key == k)

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

        # ---------- transport: a REAL publish carries a named User-Agent (issue #2 part 1) ----------
        # Cloudflare bot-management 403s the default `Python-urllib/x.y` UA. Point the client at a
        # one-shot local server (no OPS_SHARE_FAKE) and assert the PUT's UA. --plain keeps it
        # stdlib-only. This exercises the real _publish() path, header included.
        import http.server, threading
        cap = {}

        class _H(http.server.BaseHTTPRequestHandler):
            def do_PUT(self):
                cap["ua"] = self.headers.get("User-Agent")
                cap["body"] = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(b'{"id":"testid","admin_token":"tok"}')

            def log_message(self, *a):  # keep the suite output clean
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
        th = threading.Thread(target=srv.handle_request, daemon=True); th.start()
        (h / ".share").mkdir(exist_ok=True)
        (h / ".share" / "config.json").write_text(
            json.dumps({"endpoint": f"http://127.0.0.1:{srv.server_address[1]}"}))
        run("share", "alpha", "--yes", "--plain", "--json", home=h)  # real transport, no FAKE
        th.join(timeout=5); srv.server_close()
        check("real publish sends a named User-Agent (Cloudflare 403 fix)",
              cap.get("ua") == "ops-share/1.0", str(cap))
        check("real publish body is OPSX bundle (agent .md capable)",
              cap.get("body", b"")[:4] == b"OPSX", str(cap)[:80])

        # ---------- share pull: ?raw=1 + local decrypt (Tier A human link) ----------
        pull_body = cap.get("body", b"")
        stored = {"body": pull_body}
        share_id = "abcdefghij"

        class _PullH(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if "raw=1" in self.path:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(stored["body"])
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):  # noqa: A002
                pass

        psrv = http.server.HTTPServer(("127.0.0.1", 0), _PullH)
        pth = threading.Thread(target=psrv.handle_request, daemon=True)
        pth.start()
        port = psrv.server_address[1]
        human = f"http://127.0.0.1:{port}/{share_id}"
        r = run("share", "pull", human, home=h)
        pth.join(timeout=5)
        psrv.server_close()
        check("pull plain share prints wiki markdown", r.returncode == 0 and "# Alpha" in r.stdout, r.stdout[:120] + r.stderr[:120])
        if HAVE_CRYPTO:
            ct, k = sl.encrypt(pull_body)
            stored["body"] = ct.encode("ascii")
            psrv2 = http.server.HTTPServer(("127.0.0.1", 0), _PullH)
            pth2 = threading.Thread(target=psrv2.handle_request, daemon=True)
            pth2.start()
            port2 = psrv2.server_address[1]
            enc_url = f"http://127.0.0.1:{port2}/{share_id}#{k}"
            r = run("share", "pull", enc_url, home=h)
            pth2.join(timeout=5)
            psrv2.server_close()
            check("pull E2E share decrypts to markdown", r.returncode == 0 and "# Alpha" in r.stdout, r.stdout[:120])

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
