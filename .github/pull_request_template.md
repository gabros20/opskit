## What & why

Brief description of the change and the motivation.

## Checklist

- [ ] `python3 test/run_all.py` is green
- [ ] New/changed verbs ship a `cmd.json` with the correct `risk` class, and `ops help` renders them
- [ ] New behaviour has a `test/run_*.py` suite (added to `test/run_all.py`)
- [ ] `ops doctor` passes
- [ ] No secrets, no binaries committed into `wiki/`; writes stay inside the roots
- [ ] If it changes the spec, `docs/design/` and/or `docs/DECISIONS.md` updated
