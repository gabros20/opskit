#!/usr/bin/env python3
"""
plainkeep __complete [prior words...] — the brain behind zsh tab-completion (Tier-1 ergonomics).

The shell passes the words already typed after `plainkeep` (everything before the word being completed).
We print the candidates for the NEXT word, one per line, as `value:description` (the description is
optional and colon-free). The zsh function in script/completions/_ops feeds these to `_describe`.

Everything is derived live from `lib/completion.py` — verbs + each compound verb's `actions[]`
grammar (the cmd.json sidecars) and live content providers (note slugs, task ids, …). There are NO
hardcoded subaction tables here anymore (plainkeep.json/3): the grammar lives in cmd.json, so completion
can never drift from the real surface, and `plainkeep complete --json` shares this exact brain. Hidden from
`plainkeep help`/`plainkeep.json` (cmd.json "hidden": true); risk `read`, so it runs freely under the guardrail.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import completion  # noqa: E402


def _clean(s: str) -> str:
    return s.replace(":", " -").strip()


def main(prior: list[str]) -> int:
    for value, desc, _kind in completion.candidates(prior):
        print(f"{value}:{_clean(desc)}" if desc else value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
