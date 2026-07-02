"""
sharelib.py — pure, dependency-light helpers for `ops share` (proposal Part 5.2). Kept free of any
`from lib import …` so a test can load it by file path (the bin/lib-namespace-vs-test/lib gotcha),
and free of network I/O so encryption / HTML rendering are unit-testable offline.

The zero-knowledge model (PrivateBin pattern): the note renders to ONE self-contained HTML blob
LOCALLY, that blob is encrypted with a locally-generated AES-256-GCM key, only the CIPHERTEXT is
published, and the key travels in the URL fragment (never reaches the worker). `cryptography` is an
AUTO-DETECTED optional dep — without it only `--plain` works and E2E prints the install hint.
"""
from __future__ import annotations
import base64
import html
import os
import re

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    HAVE_CRYPTO = True
except Exception:  # pragma: no cover - exercised only on the zero-install path
    AESGCM = None  # type: ignore
    HAVE_CRYPTO = False

CRYPTO_HINT = "install the AES layer: pip install cryptography  (or use --plain)"

_LINK = re.compile(r"\[\[([^\]]+)\]\]")
_IMG = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ICODE = re.compile(r"`([^`]+)`")
_MDLINK = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")

_CSS = (
    "body{max-width:44rem;margin:2rem auto;padding:0 1rem;"
    "font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a1a}"
    "h1,h2,h3{line-height:1.25}code{background:#f4f4f4;padding:.1em .3em;border-radius:3px}"
    "img{max-width:100%}a{color:#b5651d}hr{border:none;border-top:1px solid #ddd;margin:2rem 0}"
    ".ops-note{margin-bottom:2rem}"
)


# --------------------------------------------------------------------------- encryption (E2E)

def have_crypto() -> bool:
    return HAVE_CRYPTO


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64u_dec(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def encrypt(plaintext: bytes) -> tuple[str, str]:
    """AES-256-GCM. Returns (ciphertext_b64url, key_b64url). The blob is nonce||ct so decrypt is
    self-contained; the key is what travels in the URL fragment `#<key>`."""
    if not HAVE_CRYPTO:
        raise RuntimeError(CRYPTO_HINT)
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return _b64u(nonce + ct), _b64u(key)


def decrypt(blob_b64: str, key_b64: str) -> bytes:
    """Inverse of encrypt() — used by the round-trip test (the browser does this in JS in production)."""
    if not HAVE_CRYPTO:
        raise RuntimeError(CRYPTO_HINT)
    raw = _b64u_dec(blob_b64)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM(_b64u_dec(key_b64)).decrypt(nonce, ct, None)


# --------------------------------------------------------------------------- expiry

def parse_expires(spec: str) -> int:
    """'7d' / '12h' / '30m' / '3600' → seconds. Raises ValueError on garbage. Feeds KV expirationTtl."""
    spec = (spec or "").strip().lower()
    m = re.fullmatch(r"(\d+)\s*([smhdw]?)", spec)
    if not m:
        raise ValueError(f"bad --expires {spec!r} (use e.g. 7d, 12h, 30m)")
    n = int(m.group(1))
    return n * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[m.group(2)]


# --------------------------------------------------------------------------- markdown → self-contained HTML

def _md_inline(text: str, resolvable: set[str]) -> str:
    """Inline markdown → HTML on already-escaped text. Wikilinks resolve WITHIN the shared set to an
    intra-doc anchor; targets outside the set degrade to plain text (proposal Part 5.2)."""
    def link(m):
        tgt = m.group(1).split("#", 1)[0].split("|", 1)[0].strip()
        label = m.group(1).split("|", 1)[1].strip() if "|" in m.group(1) else tgt
        if tgt in resolvable:
            return f'<a href="#note-{html.escape(tgt)}">{html.escape(label)}</a>'
        return html.escape(label)
    text = _LINK.sub(link, text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ICODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _MDLINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', text)
    return text


def _strip_frontmatter(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return md


def render_note_html(md: str, resolvable: set[str], image_resolver=None) -> str:
    """Render ONE note body (frontmatter stripped) to an HTML fragment. `image_resolver(path)` returns
    a data: URI (or None to drop the image — over the size cap or outside the files root)."""
    out, lines = [], _strip_frontmatter(md).splitlines()
    in_code = False
    for raw in lines:
        if raw.strip().startswith("```"):
            out.append("</pre>" if in_code else "<pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(raw))
            continue
        # images first (before escaping) so we can inline data URIs
        img = _IMG.match(raw.strip())
        if img:
            alt, path = img.group(1), img.group(2).strip()
            uri = image_resolver(path) if image_resolver else None
            if uri:
                out.append(f'<img alt="{html.escape(alt)}" src="{uri}">')
            else:
                out.append(f"<p><em>{html.escape(alt or path)}</em></p>")
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", raw)
        if hm:
            lvl = len(hm.group(1))
            out.append(f"<h{lvl}>{_md_inline(html.escape(hm.group(2)), resolvable)}</h{lvl}>")
        elif raw.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{_md_inline(html.escape(raw), resolvable)}</p>")
    return "\n".join(out)


def render_bundle(notes: list[dict], image_resolver=None) -> str:
    """`notes` = [{slug, title, md}] → ONE self-contained HTML document (inline CSS, intra-set
    wikilinks). A single note and a collection use the same path (collections coalesce to one blob)."""
    resolvable = {n["slug"] for n in notes}
    title = notes[0]["title"] if len(notes) == 1 else f"{len(notes)} notes"
    parts = [
        "<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head><body>",
    ]
    for i, n in enumerate(notes):
        if i:
            parts.append("<hr>")
        parts.append(f'<section class="ops-note" id="note-{html.escape(n["slug"])}">')
        parts.append(render_note_html(n["md"], resolvable, image_resolver))
        parts.append("</section>")
    parts.append("</body></html>")
    return "\n".join(parts)


def data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
