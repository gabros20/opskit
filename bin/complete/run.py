#!/usr/bin/env python3
"""
plainkeep complete [<typed word>...] [--json] — the structured completion contract (plainkeep.json/3).

Given the words already typed after `plainkeep` (everything BEFORE the word being completed), emit the
candidates for the next word as structured rows `{value, description, kind}`. This is the clean,
documented sibling of the zsh helper `plainkeep __complete` (which emits the same candidates as lossy
`value:description` text): both share one brain, `lib/completion.py`, derived live from each compound
verb's cmd.json `actions[]`/args — no hardcoded tables, so a future TUI or an agent negotiates the
grammar from the contract instead of re-parsing usage strings. Risk `read`.

  plainkeep complete                 -> the verb list
  plainkeep complete task            -> task's subcommands (list/add/show/move/done)
  plainkeep complete task move T-42  -> the status enum (active/waiting/…)
  plainkeep complete wiki open       -> live note slugs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import completion, output  # noqa: E402


def main(argv):
    _, argv = output.parse_argv(argv)
    rows = [{"value": v, "description": d, "kind": k}
            for v, d, k in completion.candidates(list(argv))]

    def render(rs):
        if not rs:
            return "(no candidates)"
        return "\n".join(f"{r['value']}\t{r['description']}" if r["description"] else r["value"]
                         for r in rs)

    return output.emit_rows(rows, "complete", human=render)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
