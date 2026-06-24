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
| **Agent entry point** | ✅ files exist — `AGENTS.md`, `CLAUDE.md`, `skills/operate-ops/SKILL.md` |
| **Other verbs** | ⬜ designed, NOT built — `capture`, `task`, `triage`, `start`, `close`, `status`, `new`, `invoice`, `week`, … |
| **Guardrail enforcement** | ⬜ modeled & validated in `test/`, NOT yet wired into the dispatcher |
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
./ops help                          # the surface (today: help, index, search)
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
Build the daily-driver verbs (`capture`, `task`, `status`, `help`-from-manifest) and wire the
validated guardrail (`test/lib/guardrail.py`) into real dispatcher enforcement — see the build
order in the design §17.
