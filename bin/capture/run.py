#!/usr/bin/env python3
"""ops capture "<text>" — zero-decision capture of a thought into inbox/ (also reads stdin)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]).strip()
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    if not text:
        print('usage: ops capture "<text>"   (or pipe text via stdin)', file=sys.stderr)
        sys.exit(2)
    paths.INBOX.mkdir(parents=True, exist_ok=True)
    f = paths.INBOX / f"cap-{paths.now_stamp()}.md"
    f.write_text(f"---\ntype: capture\ncreated: {paths.today()}\nsource: capture\n---\n{text}\n",
                 encoding="utf-8")
    paths.append_journal(f"captured: {text[:70]}{'…' if len(text) > 70 else ''}")
    print(f"captured -> {f.relative_to(paths.OPS_HOME)}  (triage it with `ops triage`)")
