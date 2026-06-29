#!/usr/bin/env python3
"""ops index [--manifest] — (re)build the search index from the content tree (§10.2, stage 1).
--manifest instead only regenerates ops.json from the cmd.json sidecars (after adding a verb)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    if "--manifest" in sys.argv[1:]:
        from lib.manifest import write_manifest
        p = write_manifest()
        print(f"manifest regenerated -> {p.name}")
    else:
        from lib.indexlib import index
        index()
