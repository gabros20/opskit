#!/usr/bin/env python3
"""
plainkeep {{name}} — {{summary}}

SCAFFOLDED by `plainkeep new verb`. This is a stub — implement main(). Keep the contract:
  • Iron Law (§4): the model decides WHAT; this verb guarantees WHERE/HOW. The verb owns placement —
    never take a path from the caller and write it blindly.
  • Any path you write MUST be classifiable by the guardrail path-wall — inside ~/plainkeep, ~/files, or the
    current task's ONE ~/work repo. Nothing external is transmitted; verbs that could must draft only.
  • Declared risk is `{{risk}}` in cmd.json. New verbs default to `confirm`, so the guardrail makes a
    human re-run with --yes until you deliberately lower it. Read skills/operate-plainkeep/SKILL.md and an
    existing bin/<verb>/run.py before extending. Regenerate the surface with `plainkeep index --manifest`.

This is a PLUGIN verb (plugins/local/{{name}}/) — user-owned, survives `script/update`. It reaches
the engine's shared lib via PLAINKEEP_HOME (the dispatcher always exports it); it re-enters through
`plainkeep {{name}}`, so the guardrail + logs still gate it — never import lib to skip the dispatcher.
"""
import os
import sys
from pathlib import Path

# Plugin verbs live outside bin/, so locate the engine's lib via PLAINKEEP_HOME (dispatcher-exported);
# fall back to the plugins/<pack>/<verb>/ layout depth if run outside the dispatcher.
_BIN = Path(os.environ.get("PLAINKEEP_HOME") or Path(__file__).resolve().parents[3]) / "bin"
sys.path.insert(0, str(_BIN))
from lib import paths  # noqa: E402,F401  (most verbs need paths — keep or drop)


def main(argv):
    print("plainkeep {{name}}: not implemented yet — edit plugins/local/{{name}}/run.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
