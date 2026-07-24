#!/usr/bin/env python3
"""ops help [verb] [--json] — render the command surface from the cmd.json manifest (§4.3).
--json returns the ops.json/3 document (list) or one verb's contract (single verb)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import manifest, output  # noqa: E402


def main(argv):
    _, argv = output.parse_argv(argv)
    verb = argv[0] if argv else None
    try:
        p = manifest.write_manifest()  # keep ops.json fresh on every help
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        doc = {"schema": manifest.SCHEMA, "verbs": []}

    if verb:
        one = next((c for c in doc.get("verbs", []) if c.get("verb") == verb), None)
        data = one or {"verb": verb, "error": "unknown"}
        return output.emit(data, "help", human=lambda _: manifest.render(verb))
    return output.emit(doc, "help", human=lambda _: manifest.render(None))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
