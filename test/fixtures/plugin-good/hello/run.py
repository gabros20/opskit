#!/usr/bin/env python3
"""A tiny fixture plugin verb: imports ONLY the frozen SDK (lib.api) and re-enters through the
dispatcher. Used by test/run_plugin.py to prove a plugin verb runs via api.emit."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["OPS_HOME"]) / "bin"))
from lib import api  # noqa: E402


def main(argv):
    argv = [a for a in argv if a != "--json"]
    name = argv[0] if argv else "world"
    return api.emit({"greeting": f"hello {name}"}, "hello",
                    human=lambda d: f"hello {name} (via api v{api.OPS_API_VERSION})")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
