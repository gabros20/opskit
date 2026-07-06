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

# Self-contained reading stylesheet (Flexoki palette, kepano-minimal). Pure CSS — no JS, no external
# refs (the note renders inside a scriptless sandboxed iframe, and the bundle must stay portable).
# Light/dark auto via prefers-color-scheme; code blocks scroll instead of blowing out the layout.
_CSS = (
    ":root{color-scheme:light dark;"
    "--bg:#FFFCF0;--tx:#100F0F;--tx2:#6F6E69;--line:#DAD8CE;--code:#F2F0E5;--accent:#24837B;--sel:#DAD8CE}"
    "@media (prefers-color-scheme:dark){:root{"
    "--bg:#100F0F;--tx:#CECDC3;--tx2:#878580;--line:#282726;--code:#1C1B1A;--accent:#3AA99F;--sel:#282726}}"
    "*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}"
    "body{margin:0 auto;max-width:44rem;"
    "padding:calc(3.5rem + env(safe-area-inset-top)) max(1.25rem,env(safe-area-inset-right)) "
    "calc(6rem + env(safe-area-inset-bottom)) max(1.25rem,env(safe-area-inset-left));"
    "background:var(--bg);color:var(--tx);overflow-wrap:break-word;-webkit-font-smoothing:antialiased;"
    "font:1.0625rem/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}"
    "::selection{background:var(--sel)}"
    "h1,h2,h3,h4,h5,h6{line-height:1.25;font-weight:650;letter-spacing:-.01em;margin:2.4rem 0 .8rem}"
    "h1{font-size:1.9rem;font-weight:700;margin-top:0}h2{font-size:1.4rem}h3{font-size:1.17rem}"
    "h4,h5,h6{font-size:1.02rem}"
    "p{margin:0 0 1.05rem}strong{font-weight:650}em{font-style:italic}"
    "a{color:var(--tx);text-decoration:underline;text-underline-offset:2px;"
    "text-decoration-color:var(--line);text-decoration-thickness:1px}"
    "a:hover{color:var(--accent);text-decoration-color:var(--accent)}"
    "ul,ol{margin:0 0 1.05rem;padding-left:1.5rem}li{margin:.3rem 0}li::marker{color:var(--tx2)}"
    "blockquote{margin:1.5rem 0;padding:.15rem 0 .15rem 1rem;border-left:3px solid var(--line);color:var(--tx2)}"
    "blockquote p{margin:.45rem 0}"
    "hr{border:0;border-top:1px solid var(--line);margin:2.8rem 0}"
    "img{max-width:100%;height:auto;display:block;margin:1.6rem 0;border-radius:8px}"
    "code{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace;"
    "font-size:.88em;background:var(--code);padding:.15em .38em;border-radius:5px}"
    "pre{margin:1.5rem 0;padding:1rem 1.1rem;background:var(--code);border:1px solid var(--line);"
    "border-radius:10px;overflow-x:auto;-webkit-overflow-scrolling:touch}"
    "pre code{background:none;padding:0;border-radius:0;font-size:.86rem;line-height:1.55;"
    "display:block;white-space:pre}"
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
    list_type = None  # 'ul' | 'ol' | None — the currently open list
    in_quote = False

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def close_quote():
        nonlocal in_quote
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    def inl(s):
        return _md_inline(html.escape(s), resolvable)

    for raw in lines:
        if raw.strip().startswith("```"):
            close_list(); close_quote()
            out.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(raw))
            continue

        stripped = raw.strip()
        if stripped == "":
            close_list(); close_quote()
            out.append("")
            continue

        # images (whole-line) first — before escaping — so data URIs inline
        img = _IMG.match(stripped)
        if img:
            close_list(); close_quote()
            alt, path = img.group(1), img.group(2).strip()
            uri = image_resolver(path) if image_resolver else None
            out.append(f'<img alt="{html.escape(alt)}" src="{uri}">' if uri
                       else f"<p><em>{html.escape(alt or path)}</em></p>")
            continue

        hm = re.match(r"^(#{1,6})\s+(.*)$", raw)
        if hm:
            close_list(); close_quote()
            lvl = len(hm.group(1))
            out.append(f"<h{lvl}>{inl(hm.group(2))}</h{lvl}>")
            continue

        um = re.match(r"^\s*[-*+]\s+(.*)$", raw)
        if um:
            close_quote()
            if list_type != "ul":
                close_list(); out.append("<ul>"); list_type = "ul"
            out.append(f"<li>{inl(um.group(1))}</li>")
            continue

        om = re.match(r"^\s*\d+[.)]\s+(.*)$", raw)
        if om:
            close_quote()
            if list_type != "ol":
                close_list(); out.append("<ol>"); list_type = "ol"
            out.append(f"<li>{inl(om.group(1))}</li>")
            continue

        qm = re.match(r"^\s*>\s?(.*)$", raw)
        if qm:
            close_list()
            if not in_quote:
                out.append("<blockquote>"); in_quote = True
            out.append(f"<p>{inl(qm.group(1))}</p>")
            continue

        close_list(); close_quote()
        out.append(f"<p>{inl(raw)}</p>")

    close_list(); close_quote()
    if in_code:  # defensive: unterminated fence
        out.append("</code></pre>")
    return "\n".join(out)


def render_bundle(notes: list[dict], image_resolver=None) -> str:
    """`notes` = [{slug, title, md}] → ONE self-contained HTML document (inline CSS, intra-set
    wikilinks). A single note and a collection use the same path (collections coalesce to one blob)."""
    resolvable = {n["slug"] for n in notes}
    title = notes[0]["title"] if len(notes) == 1 else f"{len(notes)} notes"
    parts = [
        "<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
        '<meta name="color-scheme" content="light dark">',
        '<meta name="theme-color" media="(prefers-color-scheme:light)" content="#FFFCF0">',
        '<meta name="theme-color" media="(prefers-color-scheme:dark)" content="#100F0F">',
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
