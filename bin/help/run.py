#!/usr/bin/env python3
"""ops help [verb] — render the command surface from the cmd.json manifest (§4.3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import manifest  # noqa: E402

if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        manifest.write_manifest()  # keep ops.json fresh on every help
    except Exception:
        pass
    print(manifest.render(verb))
