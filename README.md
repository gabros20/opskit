# Personal Operating System (`~/ops`)

A local-first, agent-agnostic personal operating system: **plaintext is truth, git is the spine,
one `ops <verb>` command surface drives everything** — for you, for cron, and for any AI agent.
This repo is the **canonical starter** for that system.

> Full design: [`docs/design/PERSONAL_OS_DESIGN_v2.md`](docs/design/PERSONAL_OS_DESIGN_v2.md) (v3.7).
> Why decisions were made: [`docs/DECISIONS.md`](docs/DECISIONS.md) (ADR log).

## State of the build (honest map)

This is an **early canonical repo**: the design is complete and validated, and the *retrieval
engine* is implemented; most other verbs are still designed-but-not-built.

| Area | Status |
|---|---|
| **Design + decisions** | ✅ complete — `docs/design/` (v3.6 baseline + v3.7 active), `docs/DECISIONS.md` (ADR-001…006) |
| **Retrieval engine** | ✅ built & tested — `ops index` / `ops search` (stage 1 FTS5+graph → stage 2 LanceDB vectors → stage 3 rerank) |
| **Verbs built (14)** | ✅ `help` `status` `capture` `triage` `task` `index` `search` `start` `close` `week` `doctor` `wiki` `backup` `consolidate` — all guardrail-gated, self-describing. **The capture → triage → task → done spine, the daily/weekly loop, search, self-check, wiki navigation, backup-nag, and nightly consolidation all work end-to-end.** |
| **Agent entry point** | ✅ files exist — `AGENTS.md`, `CLAUDE.md`, `skills/operate-ops/SKILL.md` |
| **Other verbs** | ⬜ designed, NOT built — `new`, `invoice`, `repo`, `files`, `sweep`, and the jobs scheduler (cron wiring for `consolidate`/`close`) |
| **Guardrail enforcement** | ✅ wired — `bin/lib/guardrail.py` gates every verb by risk class (deny refused, confirm needs `--yes`, new verbs default confirm) + logs to `.logs/ops.log`; mirrors the validated §5 model (parity-tested) |
| **Validation harness** | ✅ `test/` — design simulation + retrieval tests (see `test/README.md`) |

## Layout (the four roots + this repo)

```
ops                  # the dispatcher (ops <verb>); on PATH via dotfiles
AGENTS.md  CLAUDE.md  # the agent contract (CLAUDE.md bridges to AGENTS.md)
bin/                 # the verbs — lib/ (shared) + one folder per verb (index/, search/ built)
skills/operate-ops/  # the operating manual any agent reads
wiki/                # KNOWLEDGE — your durable notes (starts ~empty; see wiki/conventions.md)
tasks/               # folder = status: inbox/ active/ waiting/ done/
journal/  inbox/  templates/  jobs/   # daily log · capture zone · scaffolds · scheduled jobs
docs/                # design/ (the spec) + DECISIONS.md (ADRs)
test/                # validation harness + fixtures/ (the KB-derived test vault lives here)
requirements.txt     # optional deps (lancedb, fastembed) for stage-2/3 search
```
The other roots (`~/work` code, `~/files` binaries, `~/dotfiles` machine) are described in the
design §2; this repo is `~/ops`.

## Quick start

```sh
./ops help                          # the command surface (rendered from cmd.json)
./ops capture "a passing thought"   # → inbox/
./ops triage                        # propose filing each inbox item → task or wiki note (you approve)
./ops task add "Fix the webhook"    # → tasks/active/ ;  ops task list | move <id> waiting | done <id>
./ops status                        # tasks, inbox, last index, repo state
./ops start  /  ./ops close  /  ./ops week   # daily start · daily close · weekly review (§16)
./ops wiki new note "An idea"  /  ./ops wiki backlinks <slug>  /  ./ops wiki orphans
./ops doctor                        # self-check: folders, manifest, adapters, secrets, index
./ops backup                        # nag if ~/ops has uncommitted/unpushed work (never pushes for you)
./ops consolidate                   # nightly: wiki orphans/stale + day digest → journal
./ops index                         # build the search index over wiki/  (stage 1: keyword + graph)
./ops search "your query"           # ranked file#heading hits

# stage 2 (semantic) + stage 3 (rerank) — opt-in, local, no server:
pip install -r requirements.txt && ollama pull embeddinggemma
OPS_VECTORS=1 ./ops index
OPS_VECTORS=1 OPS_RERANK=1 ./ops search "how do I stop an agent looping forever"
```
Rebuild rule: the index is a disposable cache — `rm -rf .index && ops index` rebuilds it from the
markdown. Nothing in `.index/`, `.logs/`, or `ref/` is tracked.

## Tests
```sh
python3 test/run_all.py             # all offline suites (stdlib only) — design model + search engine
python3 test/run_simulation.py --model sonnet   # LLM-operator agnosticism/drift sim (needs claude CLI)
```

## What's next
`new` (scaffold a project/client: wiki hub + `~/work` repo from template), and the **jobs scheduler**
(§15) that runs `consolidate` / `close` / `backup` on a cron so the maintenance verbs fire unattended.
Then the work-facing verbs (`repo`, `files`, `invoice`). Each is a `bin/<verb>/{run.py,cmd.json}`,
guardrail-gated and in `ops help`. See §15–17.
