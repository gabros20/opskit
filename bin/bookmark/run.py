#!/usr/bin/env python3
"""
ops bookmark <url> [--note "<text>"] [--no-fetch] [--archive] — save a link as a wiki note (issue #1
gap F). Local-first: the note is created from the URL immediately and always works offline. Title +
readable text are a BEST-EFFORT external GET (an external *read*, which the §5 wall allows — it never
transmits); --no-fetch skips the network, degrading to the URL as the title. --archive additionally
snapshots the fetched HTML into ~/files/bookmarks/ (via the same shadow-asset idea as `ops files`),
so the bookmark survives link-rot. The note is a data-driven `type: bookmark` (see lib/notetype).

Testability: OPS_BOOKMARK_FIXTURE=<file> feeds local HTML instead of the network, so the fetch/parse/
archive paths are exercised offline and deterministically.
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import notetype, paths  # noqa: E402

GREEN, DIM, YEL, RESET = "\033[32m", "\033[2m", "\033[33m", "\033[0m"
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META = re.compile(r'<meta[^>]+(?:name|property)=["\'](?:og:)?description["\'][^>]+content=["\'](.*?)["\']',
                   re.IGNORECASE | re.DOTALL)
_TAGS = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>")
_ANGLE = re.compile(r"(?s)<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")


def _unescape(s: str) -> str:
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&apos;", "'"), ("&nbsp;", " ")):
        s = s.replace(a, b)
    return s.strip()


def _fetch(url: str):
    """Return the page HTML, or None on any failure/offline. Honors OPS_BOOKMARK_FIXTURE for tests."""
    fixture = os.environ.get("OPS_BOOKMARK_FIXTURE")
    if fixture:
        try:
            return Path(fixture).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "ops-bookmark/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:  # noqa: S310 (http/https validated below)
            return r.read(600_000).decode("utf-8", "replace")
    except Exception:
        return None


def _readable(html: str, limit: int = 1200) -> str:
    text = _ANGLE.sub(" ", _TAGS.sub(" ", html))
    text = _WS.sub(" ", _unescape(text))
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    joined = " ".join(lines)
    return (joined[:limit] + "…") if len(joined) > limit else joined


def _title_from_url(url: str) -> str:
    p = urlparse(url)
    tail = (p.path.rstrip("/").rsplit("/", 1)[-1] or p.netloc)
    return _unescape(tail.replace("-", " ").replace("_", " ")) or p.netloc or url


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("-")]
    no_fetch = "--no-fetch" in argv
    archive = "--archive" in argv
    note_extra = ""
    if "--note" in argv:
        i = argv.index("--note")
        note_extra = argv[i + 1] if i + 1 < len(argv) else ""

    if not args:
        print("usage: ops bookmark <url> [--note \"<text>\"] [--no-fetch] [--archive]", file=sys.stderr)
        return 2
    url = args[0]
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        print(f"not a http(s) url: {url}", file=sys.stderr); return 2

    title, desc, html = "", "", None
    if not no_fetch:
        html = _fetch(url)
        if html:
            m = _TITLE.search(html)
            if m:
                title = _unescape(m.group(1))
            md = _META.search(html)
            if md:
                desc = _unescape(md.group(1))
    if not title:
        title = _title_from_url(url)
        if not no_fetch and html is None:
            print(f"{YEL}note{RESET}  fetch failed/offline — titled from the URL (edit later)", file=sys.stderr)

    slug = paths.slugify(title) or paths.slugify(parsed.netloc)
    existing = {p.stem for p in paths.WIKI.rglob("*.md")} if paths.WIKI.exists() else set()
    base, i = slug, 2
    while slug in existing:
        slug, i = f"{base}-{i}", i + 1

    body_parts = []
    if desc:
        body_parts.append(f"> {desc}")
    if note_extra:
        body_parts.append(note_extra)
    if html and not no_fetch:
        body_parts.append("## Extract\n" + _readable(html))
    body = "\n\n".join(body_parts)

    d = paths.WIKI / notetype.type_dir("bookmark")
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.md"
    f.write_text(notetype.render("bookmark", title=title, url=url, body=body, slug=slug), encoding="utf-8")

    archived = None
    if archive:
        if html:
            ad = paths.FILES_ROOT / "bookmarks"
            ad.mkdir(parents=True, exist_ok=True)
            archived = ad / f"{slug}.html"
            archived.write_text(html, encoding="utf-8")
        else:
            print(f"{YEL}note{RESET}  --archive skipped (no fetched HTML)", file=sys.stderr)

    paths.append_journal(f"bookmark: {slug} <- {url}")
    print(f"{GREEN}saved{RESET} -> {f.relative_to(paths.OPS_HOME)}  {DIM}({title}){RESET}")
    if archived:
        print(f"{GREEN}archived{RESET} -> {archived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
