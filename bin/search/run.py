#!/usr/bin/env python3
"""ops search "<query>" [--json] — ranked file#heading hits (FTS5 + wikilink graph, §10.2 stage 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output  # noqa: E402
from lib.indexlib import search  # noqa: E402


def main(argv):
    _, argv = output.parse_argv(argv)
    query = " ".join(argv).strip()
    if not query:
        output.fail(output.EXIT_USAGE, 'usage: ops search "<query>"', verb="search")
    hits = search(query, log=True)  # every real search is logged to .logs/queries.jsonl (ADR-002)
    rows = [{"path": p, "heading": h, "score": round(s, 6)} for p, h, s in hits]

    def render(rs):
        if not rs:
            return "(no hits — try `ops index` first, or broaden the query)"
        return "\n".join(f"{r['score']:6.4f}  {r['path']}#{r['heading']}" for r in rs)

    return output.emit_rows(rows, "search", human=render)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
