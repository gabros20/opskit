# AGENTS.md — {{name}}

Operating contract for any agent working in this `~/work` repo. (The system-wide contract
lives in `~/plainkeep/AGENTS.md`; this file is repo-local and wins for repo-specific rules.)

## Ground rules
- This repo is one project under `~/work`. Operate only here and in its sanctioned
  worktrees (`~/work/.worktrees/{{slug}}-<task-id>`).
- Use `script/*` for everything repeatable — never hand-run ad-hoc build/test commands
  that a script should own. If a workflow isn't a script yet, add one.
- Never commit secrets. `.env` is gitignored; reference secrets by name only.
- Never push, deploy, or publish without an explicit human OK (drafts are fine).

## Commands
- `script/setup` — install deps / prepare the environment.
- `script/test` — the test suite (make this the single source of truth for "is it green?").

## Knowledge
- The durable "why" for this project lives in its wiki hub `[[{{slug}}]]` in `~/plainkeep`, not here.
  Keep this repo signal-only (code + the docs a contributor needs).
