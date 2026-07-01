#!/usr/bin/env python3
"""
ops {{name}} — {{summary}}

SCAFFOLDED by `ops new verb`. This is a stub — implement main(). Keep the contract:
  • Iron Law (§4): the model decides WHAT; this verb guarantees WHERE/HOW. The verb owns placement —
    never take a path from the caller and write it blindly.
  • Any path you write MUST be classifiable by the guardrail path-wall — inside ~/ops, ~/files, or the
    current task's ONE ~/work repo. Nothing external is transmitted; verbs that could must draft only.
  • Declared risk is `{{risk}}` in cmd.json. New verbs default to `confirm`, so the guardrail makes a
    human re-run with --yes until you deliberately lower it. Read skills/operate-ops/SKILL.md and an
    existing bin/<verb>/run.py before extending. Regenerate the surface with `ops index --manifest`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths  # noqa: E402,F401  (most verbs need paths — keep or drop)


def main(argv):
    print("ops {{name}}: not implemented yet — edit bin/{{name}}/run.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
