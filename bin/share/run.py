#!/usr/bin/env python3
"""
ops share <slug> | collection <tag> | list | revoke <id> | init — zero-knowledge, confirm-gated
sharing (proposal Part 5.2). Render a note (or a tag collection) to ONE self-contained HTML blob
LOCALLY, encrypt it AES-256-GCM with a locally-generated key, PUT only the CIPHERTEXT to a vendored
Cloudflare Worker + KV, and hand back a link whose `#fragment` carries the key (the provider can
never read the note). The verb's output is a DRAFT link — the human sends it.

Governance: risk safe_write at the surface so `list` stays free, but every TRANSMITTING subaction
(share/collection/revoke, and `init` deploy) self-gates `--yes` → EXIT_CONFIRM(3). Publishing
ciphertext off-machine IS a transmission; the transport is factored into _publish()/_revoke_remote()
and is NEVER exercised by tests (OPS_SHARE_FAKE short-circuits it deterministically). `--dry-run`
renders + encrypts locally and stops before the PUT. `--plain` = unguessable slug, no E2E.
Fallback for the unprovisioned: `--gist` (secret gist via `gh gist create`, confirm-gated).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output, paths, sharelib  # noqa: E402

GREEN, YEL, DIM, RESET = "\033[32m", "\033[33m", "\033[2m", "\033[0m"

# Cloudflare bot-management 403s the default `Python-urllib/x.y` User-Agent (a PUT that succeeds
# from curl fails from urllib for this reason alone). A named UA passes the edge.
UA = "ops-share/1.0"

SHARE_DIR = paths.OPS_HOME / ".share"
CONFIG = SHARE_DIR / "config.json"
LEDGER = SHARE_DIR / "ledger.json"
IMG_CAP = int(os.environ.get("OPS_SHARE_IMG_CAP", str(512 * 1024)))  # inline-image size cap (bytes)
IMG_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}


# --------------------------------------------------------------------------- config + ledger I/O

def _config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ledger() -> dict:
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return {"shares": []}


def _write_ledger(led: dict) -> None:
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _notes() -> dict:
    if not paths.WIKI.exists():
        return {}
    return {p.stem: p for p in sorted(paths.WIKI.rglob("*.md")) if p.suffix == ".md"}


def _image_resolver(base: Path):
    def resolve(path: str):
        for root in (base, paths.FILES_ROOT, paths.WIKI):
            cand = (root / path).resolve()
            try:
                cand.relative_to(paths.FILES_ROOT.resolve())
            except Exception:
                try:
                    cand.relative_to(paths.OPS_HOME.resolve())
                except Exception:
                    continue
            if cand.is_file() and cand.stat().st_size <= IMG_CAP:
                mime = IMG_MIME.get(cand.suffix.lower())
                if mime:
                    return sharelib.data_uri(cand.read_bytes(), mime)
        return None
    return resolve


# --------------------------------------------------------------------------- transport (never in tests)

def _fake() -> bool:
    return os.environ.get("OPS_SHARE_FAKE", "").lower() in ("1", "true", "yes")


def _publish(endpoint: str, body: bytes, ttl: int) -> dict:
    """PUT ciphertext to the worker; returns {id, admin_token}. Deterministic no-network stub under
    OPS_SHARE_FAKE (the ONLY path tests take)."""
    if _fake():
        import hashlib
        h = hashlib.sha256(body).hexdigest()[:16]
        return {"id": h, "admin_token": "fake-" + h}
    req = urllib.request.Request(endpoint.rstrip("/") + "/", data=body, method="PUT",
                                 headers={"Content-Type": "application/octet-stream",
                                          "X-Expire-Seconds": str(ttl), "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:  # pragma: no cover - never run in tests
        return json.loads(r.read().decode("utf-8"))


def _revoke_remote(endpoint: str, sid: str, token: str) -> None:
    if _fake():
        return
    req = urllib.request.Request(f"{endpoint.rstrip('/')}/{sid}", method="DELETE",
                                 headers={"X-Admin-Token": token, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30):  # pragma: no cover - never run in tests
        pass


# --------------------------------------------------------------------------- frontmatter share block

def _stamp_frontmatter(path: Path, url: str) -> None:
    """Splice/replace a `share:` line in the note's frontmatter (audit trail; sweep reads the ledger)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return
    if not lines or lines[0].strip() != "---":
        return
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return
    body = [ln for ln in lines[1:end] if not ln.startswith("share:")]
    body.append(f"share: {url}")
    path.write_text("\n".join(["---", *body, "---", *lines[end + 1:]]) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- share / collection

def _collect(argv):
    """Return (kind, key, [(slug, path)]). Single note by slug, or a collection by tag."""
    notes = _notes()
    if argv and argv[0] == "collection":
        tag = argv[1] if len(argv) > 1 else ""
        if not tag:
            output.fail(output.EXIT_USAGE, "usage: ops share collection <tag>", verb="share")
        tag = tag.lstrip("#")
        sel = [(s, p) for s, p in notes.items() if tag in paths.fm_list(p, "tags")]
        return "collection", tag, sel
    slug = argv[0] if argv else ""
    p = notes.get(slug)
    if not p:
        output.fail(output.EXIT_NOT_FOUND, f"no note '{slug}'", verb="share")
    return "note", slug, [(slug, p)]


VALUE_FLAGS = ("--expires", "--out")


def _positional(argv):
    """Drop flags AND the values that follow value-flags, leaving the subcommand/slug tokens."""
    pos, skip = [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a in VALUE_FLAGS:
            skip = True
            continue
        if a.startswith("-"):
            continue
        pos.append(a)
    return pos


def cmd_share(argv):
    dry = "--dry-run" in argv
    yes = ("--yes" in argv) or ("-y" in argv)
    plain = "--plain" in argv
    gist = "--gist" in argv
    expires = argv[argv.index("--expires") + 1] if "--expires" in argv else "7d"
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    try:
        ttl = sharelib.parse_expires(expires)
    except ValueError as e:
        output.fail(output.EXIT_USAGE, str(e), verb="share")

    pos = _positional(argv)
    kind, key, sel = _collect(pos)
    if not sel:
        output.fail(output.EXIT_NOT_FOUND, f"no notes match '{key}'", verb="share")

    docs = [{"slug": s, "title": paths.title_of(p), "md": p.read_text(encoding="utf-8")}
            for s, p in sel]
    base = sel[0][1].parent
    html_bytes = sharelib.render_bundle(docs, image_resolver=_image_resolver(base)).encode("utf-8")
    md_bytes = sharelib.render_markdown_bundle(docs).encode("utf-8")
    blob = sharelib.pack_bundle(md_bytes, html_bytes)

    if not plain and not sharelib.have_crypto():
        output.fail(output.EXIT_UNEXPECTED,
                    "AES-256-GCM unavailable — E2E encryption needs `cryptography`",
                    hint=sharelib.CRYPTO_HINT, verb="share")

    url_key = None
    if plain:
        body = blob
    else:
        cipher_b64, url_key = sharelib.encrypt(blob)
        body = cipher_b64.encode("ascii")

    if dry:
        if out:
            Path(out).write_bytes(html_bytes)  # pre-encryption HTML for inspection
        data = {"kind": kind, "key": key, "notes": [d["slug"] for d in docs],
                "plain": plain, "bytes": len(body), "encrypted": not plain,
                "expires_seconds": ttl, "out": out}
        return output.emit(data, "share", human=lambda _:
                           f"{DIM}dry-run{RESET}: rendered {len(docs)} note(s), {len(body)} bytes"
                           f" ({'plain' if plain else 'AES-256-GCM'}), not published.")

    if gist:
        return _gist(docs, yes)

    if not yes:
        output.fail(output.EXIT_CONFIRM,
                    f"publishing ciphertext off-machine is a transmission ({len(body)} bytes)",
                    hint=f"re-run: ops share {' '.join(pos)} --yes", verb="share")

    cfg = _config()
    endpoint = cfg.get("endpoint")
    if not endpoint and not _fake():
        output.fail(output.EXIT_UNEXPECTED, "no share endpoint configured",
                    hint="run: ops share init  (or use --gist)", verb="share")
    res = _publish(endpoint or "https://fake.invalid", body, ttl)
    sid, token = res["id"], res.get("admin_token", "")
    base_url = f"{(endpoint or '').rstrip('/')}/{sid}"
    url = base_url
    if url_key:
        url += f"#{url_key}"

    entry = {"id": sid, "kind": kind, "key": key, "url": url, "admin_token": token,
             "plain": plain, "notes": [d["slug"] for d in docs],
             "note_paths": [str(p.relative_to(paths.OPS_HOME)) for _, p in sel],
             "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "created_ts": int(datetime.now(timezone.utc).timestamp()),
             "expires_ts": int(datetime.now(timezone.utc).timestamp()) + ttl}
    led = _ledger()
    led["shares"].append(entry)
    _write_ledger(led)
    for _, p in sel:
        _stamp_frontmatter(p, url)
    paths.append_journal(f"share {kind} {key} -> {sid}")

    agent = f"{base_url}.md"
    data = {"id": sid, "url": url, "kind": kind, "key": key, "expires_ts": entry["expires_ts"],
            "encrypted": not plain, "agent_md": agent}
    keynote = "" if plain else (
        f"\n  {YEL}send the FULL link — the #… after the id is the decryption key; "
        f"a truncated link cannot be opened{RESET}")
    if url_key:
        agent_hint = (
            f"\n  {DIM}agent md:{RESET} {agent}\n"
            f"  {DIM}  key: header X-Ops-Share-Key: {url_key}  (or ?k=… for fetch tools; may log){RESET}"
        )
    else:
        agent_hint = f"\n  {DIM}agent md:{RESET} {agent}"
    return output.emit(data, "share", human=lambda _:
                       f"{GREEN}shared{RESET} {kind} {key}\n  {url}{keynote}{agent_hint}\n"
                       f"  {DIM}revoke: ops share revoke {sid} --yes{RESET}")


def _gist(docs, yes):
    if not yes:
        output.fail(output.EXIT_CONFIRM, "creating a secret gist is a transmission",
                    hint="re-run with --gist --yes", verb="share")
    import shutil
    if not shutil.which("gh"):
        output.fail(output.EXIT_UNEXPECTED, "gh not installed", hint="brew install gh", verb="share")
    # pragma: no cover - confirm-gated, never in tests
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(sharelib.render_bundle(docs))
        tmp = f.name
    r = subprocess.run(["gh", "gist", "create", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        output.fail(output.EXIT_UNEXPECTED, "gh gist create failed", hint=r.stderr.strip(), verb="share")
    return output.emit({"url": r.stdout.strip(), "kind": "gist"}, "share",
                       human=lambda d: f"{GREEN}gist{RESET}: {d['url']}")


# --------------------------------------------------------------------------- list / revoke

def cmd_list():
    led = _ledger()
    now = int(datetime.now(timezone.utc).timestamp())
    rows = []
    for s in led["shares"]:
        if s.get("revoked"):
            state = "revoked"
        elif s.get("expires_ts", 0) < now:
            state = "expired"
        else:
            state = "active"
        rows.append({"id": s["id"], "kind": s.get("kind"), "key": s.get("key"),
                     "state": state, "expires_ts": s.get("expires_ts"), "url": s.get("url")})

    def render(rs):
        if not rs:
            return "no shares yet — `ops share <slug> --yes`"
        out = [f"{len(rs)} share(s):"]
        for r in rs:
            out.append(f"  {r['id']:<18} {r['state']:<8} {r['kind']}:{r['key']}")
        return "\n".join(out)

    return output.emit_rows(rows, "share", human=render, header={"count": len(rows)})


def cmd_revoke(argv):
    sid = next((a for a in argv if not a.startswith("-")), "")
    yes = ("--yes" in argv) or ("-y" in argv)
    if not sid:
        output.fail(output.EXIT_USAGE, "usage: ops share revoke <id> --yes", verb="share")
    led = _ledger()
    entry = next((s for s in led["shares"] if s["id"] == sid), None)
    if not entry:
        output.fail(output.EXIT_NOT_FOUND, f"no share '{sid}' in ledger", verb="share")
    if not yes:
        output.fail(output.EXIT_CONFIRM, f"revoking '{sid}' deletes the published blob",
                    hint=f"re-run: ops share revoke {sid} --yes", verb="share")
    cfg = _config()
    _revoke_remote(cfg.get("endpoint", "https://fake.invalid"), sid, entry.get("admin_token", ""))
    entry["revoked"] = True
    entry["revoked_ts"] = int(datetime.now(timezone.utc).timestamp())
    _write_ledger(led)
    paths.append_journal(f"share revoke {sid}")
    return output.emit({"id": sid, "revoked": True}, "share",
                       human=lambda _: f"{GREEN}revoked{RESET} {sid}")


# --------------------------------------------------------------------------- init

WORKER_DIR = Path(__file__).resolve().parent / "worker"


def cmd_init(argv):
    yes = ("--yes" in argv) or ("-y" in argv)
    endpoint = argv[argv.index("--endpoint") + 1] if "--endpoint" in argv else None
    if endpoint:
        SHARE_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({"endpoint": endpoint}, indent=2) + "\n", encoding="utf-8")
    steps = [
        f"cd {WORKER_DIR}",
        "wrangler kv namespace create OPS_SHARE",
        "# paste the namespace id into wrangler.toml, then:",
        "wrangler deploy",
        "ops share init --endpoint https://<your-worker>.workers.dev",
    ]
    if not yes:
        return output.emit({"deployed": False, "worker": str(WORKER_DIR), "steps": steps},
                           "share", human=lambda _:
                           "deploy the share worker once (confirm with --yes to run wrangler):\n  "
                           + "\n  ".join(steps))
    # pragma: no cover - confirm-gated wrangler deploy, never in tests
    import shutil, subprocess
    if not shutil.which("wrangler"):
        output.fail(output.EXIT_UNEXPECTED, "wrangler not installed",
                    hint="npm i -g wrangler", verb="share")
    r = subprocess.run(["wrangler", "deploy"], cwd=str(WORKER_DIR))
    return output.emit({"deployed": r.returncode == 0}, "share",
                       human=lambda d: f"wrangler deploy exit {r.returncode}")


def main(argv):
    _, argv = output.parse_argv(argv)
    action = argv[0] if argv else ""
    if action == "list":
        return cmd_list()
    if action == "revoke":
        return cmd_revoke(argv[1:])
    if action == "init":
        return cmd_init(argv[1:])
    if action == "collection":
        return cmd_share(argv)
    if not action or action.startswith("-"):
        output.fail(output.EXIT_USAGE,
                    "usage: ops share <slug> [--expires 7d] | collection <tag> | list | revoke <id> | init",
                    verb="share")
    return cmd_share(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
