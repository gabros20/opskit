#!/usr/bin/env python3
"""ops index [--manifest] [--dry-run] [--json] — (re)build the search index from the content tree
(§10.2, stage 1). --manifest instead only regenerates ops.json from the cmd.json sidecars."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import output  # noqa: E402


def main(argv):
    _, argv = output.parse_argv(argv)
    dry = "--dry-run" in argv

    if "--manifest" in argv:
        from lib.manifest import write_manifest
        if dry:
            return output.emit({"dry_run": True, "target": "ops.json"}, "index",
                               human=lambda _: "would regenerate ops.json  (dry run — nothing written)")
        p = write_manifest()
        return output.emit({"manifest": p.name}, "index",
                           human=lambda _: f"manifest regenerated -> {p.name}")

    from lib import indexlib
    if dry:
        n = len(list(indexlib.CONTENT.rglob("*.md"))) if indexlib.CONTENT.exists() else 0
        return output.emit({"dry_run": True, "would_index": n}, "index",
                           human=lambda _: f"would index {n} note(s) under {indexlib.CONTENT}  (dry run — nothing written)")

    n = indexlib.index(verbose=not output.json_mode())
    if output.json_mode():
        return output.emit({"indexed": n}, "index")
    return output.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
