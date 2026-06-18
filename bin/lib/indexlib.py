"""
indexlib.py — stage-1 search engine for the Personal OS (§10.2).

Implements exactly what the validated spec calls stage 1:
  - SQLite FTS5 over the content tree (wiki/tasks/journal), chunked by markdown heading,
    incremental by file content hash,
  - the wikilink graph (one-hop expansion) fused with keyword via reciprocal-rank fusion,
  - one rebuildable file at .index/ops.sqlite (the rebuild rule: rm -rf .index && ops index).

No vectors here — that's stage 2 (sqlite-vec + local Ollama), added only when a real query log
shows FTS5+graph missing (ADR-002). Pure stdlib (sqlite3); FTS5 ships with SQLite.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

OPS_HOME = Path(os.environ.get("OPS_HOME", Path(__file__).resolve().parents[2]))
CONTENT = Path(os.environ.get("OPS_CONTENT", OPS_HOME / "content"))
INDEX_DIR = OPS_HOME / ".index"
DB = INDEX_DIR / "ops.sqlite"

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def connect() -> sqlite3.Connection:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, hash TEXT);
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(path, heading, body, slug UNINDEXED);
        CREATE TABLE IF NOT EXISTS links(src TEXT, dst TEXT);
        """
    )
    return con


def _chunks(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) sections; preamble under '(top)'."""
    out, head, buf = [], "(top)", []
    for ln in text.splitlines():
        m = HEADING_RE.match(ln)
        if m:
            if "".join(buf).strip():
                out.append((head, "\n".join(buf)))
            head, buf = m.group(2).strip(), []
        else:
            buf.append(ln)
    if "".join(buf).strip():
        out.append((head, "\n".join(buf)))
    return out or [("(top)", text)]


def _norm_link(target: str) -> str:
    return target.split("#", 1)[0].split("|", 1)[0].strip()


def index(root: Path | str = CONTENT, verbose: bool = True) -> int:
    root = Path(root)
    con = connect()
    seen, changed = set(), 0
    for p in sorted(root.rglob("*.md")):
        rel = str(p.relative_to(root))
        seen.add(rel)
        content = p.read_text(encoding="utf-8")
        h = hashlib.sha1(content.encode()).hexdigest()
        row = con.execute("SELECT hash FROM files WHERE path=?", (rel,)).fetchone()
        if row and row[0] == h:
            continue  # unchanged — incremental skip
        con.execute("DELETE FROM chunks WHERE path=?", (rel,))
        con.execute("DELETE FROM links WHERE src=?", (rel,))
        slug = Path(rel).stem
        for head, body in _chunks(content):
            con.execute("INSERT INTO chunks(path, heading, body, slug) VALUES(?,?,?,?)",
                        (rel, head, body, slug))
        for tgt in {_norm_link(t) for t in LINK_RE.findall(content)}:
            con.execute("INSERT INTO links(src, dst) VALUES(?,?)", (rel, tgt))
        con.execute("INSERT OR REPLACE INTO files(path, hash) VALUES(?,?)", (rel, h))
        changed += 1
    for (rel,) in con.execute("SELECT path FROM files").fetchall():  # prune deleted
        if rel not in seen:
            con.execute("DELETE FROM chunks WHERE path=?", (rel,))
            con.execute("DELETE FROM links WHERE src=?", (rel,))
            con.execute("DELETE FROM files WHERE path=?", (rel,))
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    con.close()
    if verbose:
        print(f"indexed {n} files ({changed} (re)indexed) -> {DB}")
    return n


def _fts_query(q: str) -> str:
    toks = [t for t in re.findall(r"[A-Za-z0-9]+", q.lower()) if len(t) > 1]
    return " OR ".join(f'"{t}"' for t in toks) or '""'


LOG_DIR = OPS_HOME / ".logs"
QUERY_LOG = LOG_DIR / "queries.jsonl"


def log_query(query: str, hits: list[tuple[str, str, float]]) -> None:
    """Append a search to .logs/queries.jsonl — the real query log that settles the vector
    question over time (ADR-002). Add the slug that actually answered as `relevant` later to
    turn a logged query into a labeled benchmark case (`ops search --mark`, future)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "q": query,
        "hits": [p for p, _h, _s in hits[:5]],
        "relevant": None,
    }
    with open(QUERY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def search(query: str, k: int = 10, graph: bool = True, log: bool = False) -> list[tuple[str, str, float]]:
    """Return [(path, heading, score)] — FTS5 keyword + one-hop wikilink-graph, fused by RRF."""
    con = connect()
    try:
        rows = con.execute(
            "SELECT path, heading, bm25(chunks) AS r FROM chunks WHERE chunks MATCH ? ORDER BY r LIMIT ?",
            (_fts_query(query), k * 4),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    best, order = {}, []
    for path, head, _r in rows:
        if path not in best:
            best[path] = head
            order.append(path)
    scores = {p: 1.0 / (60 + i) for i, p in enumerate(order, 1)}  # RRF: keyword arm
    if graph and order:
        slug_to_file = {Path(p).stem: p for (p,) in con.execute("SELECT path FROM files")}
        for i, p in enumerate(order[:k], 1):
            for (dst,) in con.execute("SELECT dst FROM links WHERE src=?", (p,)):
                fp = slug_to_file.get(dst)
                if fp:
                    scores[fp] = scores.get(fp, 0.0) + 0.5 / (60 + i)  # RRF: graph arm (discounted)
    con.close()
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
    hits = [(p, best.get(p, "(top)"), sc) for p, sc in ranked]
    if log:
        log_query(query, hits)
    return hits
