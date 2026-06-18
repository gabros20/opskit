#!/usr/bin/env python3
"""ops search "<query>" — ranked file#heading hits (FTS5 + wikilink graph, §10.2 stage 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.indexlib import search  # noqa: E402

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print('usage: ops search "<query>"', file=sys.stderr)
        sys.exit(2)
    hits = search(query)
    if not hits:
        print("(no hits — try `ops index` first, or broaden the query)")
        sys.exit(0)
    for path, heading, score in hits:
        print(f"{score:6.4f}  {path}#{heading}")
