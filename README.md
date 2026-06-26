# Personal Operating System (`~/ops`)

A local-first, agent-agnostic personal operating system: **plaintext is truth, git is the spine,
one `ops <verb>` command surface drives everything** — for you, for cron, and for any AI agent.
This repo is the **canonical starter** for that system.

> 🖱️ **New here? Open [`docs/how-it-works.html`](docs/how-it-works.html)** — a single self-contained
> interactive walkthrough of the whole system. No install, no dependencies: just open it in a browser
> and click through the four roots, the 21 verbs, the daily loop, the guardrail, and the setup flow.
>
> Full design: [`docs/design/PERSONAL_OS_DESIGN.md`](docs/design/PERSONAL_OS_DESIGN.md) (v3.7).
> Why decisions were made: [`docs/DECISIONS.md`](docs/DECISIONS.md) (ADR log).

## State of the build (honest map)

This is an **early canonical repo**: the design is complete and validated, and the *retrieval
engine* is implemented; most other verbs are still designed-but-not-built.

| Area | Status |
|---|---|
| **Design + decisions** | ✅ complete — `docs/design/` (v3.6 baseline + v3.7 active), `docs/DECISIONS.md` (ADR-001…006) |
| **Retrieval engine** | ✅ built & tested — `ops index` / `ops search` (stage 1 FTS5+graph → stage 2 LanceDB vectors → stage 3 rerank) |
| **Verbs built (21/21 — all of §4.1)** | ✅ system: `help` `status` `doctor` `backup` `index` `consolidate` · flow: `capture` `triage` `start` `close` `week` · knowledge: `search` `wiki` · tasks: `task` · work: `new` `repo` `archive` `files` `sweep` · business: `invoice` · jobs: `job`. All guardrail-gated, self-describing, and tested. **The full design surface works end-to-end.** |
| **Agent entry point** | ✅ files exist — `AGENTS.md`, `CLAUDE.md`, `skills/operate-ops/SKILL.md` |
| **Remaining for v1 release** | ⬜ template polish — LICENSE, `.github/` (issue templates + "Use this template"), seed example notes, the two-agent agnosticism check actually run |
| **Guardrail enforcement** | ✅ wired — `bin/lib/guardrail.py` gates every verb by risk class (deny refused, confirm needs `--yes`, new verbs default confirm) + logs to `.logs/ops.log`; mirrors the validated §5 model (parity-tested) |
| **Validation harness** | ✅ `test/` — design simulation + retrieval tests (see `test/README.md`) |
| **Install / setup flow** | ✅ `script/setup` (template → your vault: PATH, sibling roots, upstream, lean, doctor, first commit) + `script/update` (pull engine only) |

## How it works (in brief)

*(The interactive version of this is [`docs/how-it-works.html`](docs/how-it-works.html).)*

**Three commitments.** Plaintext is truth (every note/task/journal entry is a Markdown file; indexes
are disposable caches). Git is the spine (one repo, every change a revertible diff). One command
surface (`ops <verb>` — you never edit the plumbing by hand). A model decides *what*; the system
guarantees *where* and *how* — so any AI agent operates it through the same verbs and guardrail you do.

**Four roots, separated by location.** `~/ops` (this repo: knowledge, tasks, journal, verbs) and three
siblings that sit *next to* it, never inside: `~/work` (code — each project its own git repo),
`~/files` (binaries, not in git), `~/dotfiles` (machine config). The separation keeps the knowledge
repo small, plaintext, and fast.

**The daily loop.** `capture` a thought into `inbox/` (zero decisions) → `triage` proposes a home and
you approve → it lands as a `task` (folder = status) or a `wiki` note (auto-linked) → `start`/`close`
bookend the day in the `journal`, and `week` reviews it. `search` finds anything.

**Safety is enforced.** Before any verb runs, the guardrail classifies it: `read` (free) ·
`safe_write` (a revertible diff inside the roots) · `draft_only` (you send, never the system) ·
`confirm` (needs `--yes`; the default for new verbs) · `deny` (force-push, `rm -rf`, reading secrets,
writing iCloud — never). The same wall applies to you and to any agent.

**Finding things — three local stages.** Keyword + wikilink-graph (FTS5, built in) → semantic vectors
(local EmbeddingGemma + LanceDB, opt-in) → cross-encoder rerank (opt-in). No server, no cloud,
rebuildable from your Markdown.

## Install — from template to your vault

This repo is a **GitHub template, not your data.** You make your own copy; one script wires the machine.

1. **Get your own copy.** On GitHub → **Use this template → Create a new repository** (fresh history, your account). Then clone it to `~/ops` (the path matters — the safety path-wall is rooted there):
   ```sh
   git clone git@github.com:<you>/ops.git ~/ops && cd ~/ops
   ```
2. **Run setup** — puts `ops` on your PATH, creates the sibling roots `~/work` + `~/files`, tracks this
   template as `upstream`, drops the dev-only test harness (lean), runs `ops doctor`, makes the first
   commit. It never pushes — that's your call.
   ```sh
   ./script/setup --lean
   ```
3. **Make it live:**
   ```sh
   git push -u origin main                                       # your repo, your GitHub
   pip install -r requirements.txt && ollama pull embeddinggemma # optional: semantic search
   ops job apply                                                 # optional: schedule the nightly jobs
   ```

Now `ops` works from anywhere. **`~/ops` is yours** (your git repo); `~/work`, `~/files`, `~/dotfiles`
are **siblings, never inside it.** Pull engine improvements later without touching your notes:
```sh
./script/update   # checks out ONLY engine paths (bin/, skills/, docs/design…) from upstream; stages for review
```

## Layout (the four roots + this repo)

```
ops                  # the dispatcher (ops <verb>); on PATH via dotfiles
AGENTS.md  CLAUDE.md  # the agent contract (CLAUDE.md bridges to AGENTS.md)
bin/                 # the verbs — lib/ (shared) + one folder per verb (index/, search/ built)
skills/operate-ops/  # the operating manual any agent reads
wiki/                # KNOWLEDGE — your durable notes (starts ~empty; see wiki/conventions.md)
tasks/               # folder = status: inbox/ active/ waiting/ done/
journal/  inbox/  templates/         # daily log · capture zone · scaffolds
jobs/registry.json                   # §15 scheduled-job definitions (ops job apply → launchd plists)
script/              # setup (new-machine install) · update (pull engine from upstream) · engine.txt
docs/                # design/ (the spec) + DECISIONS.md (ADRs)
test/                # validation harness + fixtures/ (dev-only; dropped from a lean vault)
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
./ops job list  /  ./ops job run consolidate  /  ./ops job apply   # §15 scheduler (renders launchd plists)
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
The verb surface is complete (all 21 of §4.1). What remains is **template finalization for a public
v1 release**: a LICENSE, `.github/` (issue templates + "Use this template" guidance), a couple of
seed example notes so `search`/`wiki` demo out of the box, and running the two-agent agnosticism
check (`run_simulation.py`) on two different agents per the §18 definition of done.
