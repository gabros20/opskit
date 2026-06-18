#!/usr/bin/env python3
"""ops index — (re)build the search index from the content tree (§10.2, stage 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.indexlib import index  # noqa: E402

if __name__ == "__main__":
    index()
