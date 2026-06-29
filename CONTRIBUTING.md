# Contributing

This repo is the **template/engine** for the `~/ops` system. A user's own vault is a copy of it; the
framework files (`bin/`, `skills/`, `ops`, the adapters, `docs/`, `script/`) travel and update, while
their content (`wiki/ tasks/ journal/ jobs/registry.json`) is theirs. The boundary is
[`script/engine.txt`](script/engine.txt).

## Run the tests

```sh
python3 test/run_all.py          # every offline suite (stdlib only, no network, no LLM)
python3 test/run_<suite>.py      # one suite
```

All suites must stay green. CI (`.github/workflows/ci.yml`) runs `run_all.py` on every push/PR.

## Add a verb — one folder

A new verb costs exactly one directory. Nothing else to wire — `ops help`, the manifest, the
guardrail, and every agent learn it from the same place.

1. **`bin/<verb>/run.py`** — the implementation. Import shared helpers from `lib`:
   ```python
   import sys; from pathlib import Path
   sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   from lib import paths, filing   # paths/filing/guardrail/agent/manifest as needed
   ```
   The verb owns *where/how* (compute paths from `paths.*`, create tasks/notes via `filing.*`). Borrow
   model judgment, if any, through `agent.run_agent(prompt, scope)` — always with a deterministic
   fallback (§6).
2. **`bin/<verb>/cmd.json`** — the manifest sidecar. Set `verb`, `summary`, `usage`, and the **`risk`**
   class (`read` / `safe_write` / `draft_only` / `confirm` / `deny`). New/undeclared verbs default to
   `confirm`.
3. **Register the group** in `bin/lib/manifest.py` `GROUPS` (optional but tidy).
4. **`ops help`** — regenerates `ops.json`. Confirm the verb appears.
5. **`test/run_<verb>.py`** — cover it against a temp `OPS_HOME` (and `OPS_ROOTS_HOME` for the sibling
   roots). Add it to `test/run_all.py`.
6. **`ops doctor`** — should stay all-green.

### Conventions

- **Flat verbs, shallow subactions.** `ops task add …` is fine; never nest deeper.
- **Plaintext is truth.** No binaries in `wiki/`; indexes are disposable caches.
- **The guardrail is the system's, not the verb's.** Don't re-implement safety per verb — declare the
  right `risk` and (for verbs that handle caller-supplied paths) call `guardrail.classify()`.
- **The roots are walls.** Write only inside `~/ops`, `~/files`, and the task's `~/work` repo. Never
  iCloud/family paths; never transmit (drafts only).

The full rationale lives in [`docs/design/PERSONAL_OS_DESIGN.md`](docs/design/PERSONAL_OS_DESIGN.md)
and the decision log [`docs/DECISIONS.md`](docs/DECISIONS.md).
