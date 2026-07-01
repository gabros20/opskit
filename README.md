# Personal Operating System (`~/ops`)

**A local-first, agent-agnostic system for your knowledge, tasks, and work.**
Plaintext is the truth, git is the spine, and one `ops <verb>` command drives everything — by hand in
a terminal, on a schedule, or through any AI agent. No server, no cloud, no lock-in. Your notes are
Markdown files in your own git repo; you can read them, grep them, and walk away from this tool at any
time with nothing stranded.

[![License: MIT](https://img.shields.io/badge/License-MIT-C96442.svg)](LICENSE) · 21 verbs · 24 test suites · CI · macOS / Linux · Python 3 + git

> 🖱️ **Want the 2-minute tour first?** Open **[`docs/how-it-works.html`](docs/how-it-works.html)** —
> a single self-contained interactive walkthrough (no install, just open it in a browser). Click
> through the four roots, the 21 verbs, the guardrail, and a **Flows** tab with six animated `ops`
> flowcharts you can step through.

---

## What is this?

A "personal operating system" is the small set of habits and folders you use to run your life and
work — capturing thoughts, turning them into tasks, keeping durable notes, managing projects, and not
losing anything. This makes that explicit and durable:

- **Everything is a Markdown file** in `~/ops`, version-controlled with git. Indexes and embeddings
  are disposable caches rebuilt from the text — never the source of truth.
- **One command surface.** You never poke at files by hand. `ops <verb>` is the single door; each of
  the 21 verbs knows *where* things go and *how* to keep them safe.
- **Agent-agnostic.** A model (Claude, Codex, Grok, a local agent…) decides *what* to do; the system
  guarantees *where* and *how*. Any agent operates it through the same verbs and the same guardrail
  you do — so you can automate as much or as little as you like without giving up safety.

### A minute in the life

```sh
ops start                              # morning: open the journal, carry forward open tasks
ops capture "RRF beats naive hybrid"   # a thought → inbox/ (zero decisions)
ops triage                             # it proposes: file as a wiki note? a task? — you approve
ops task add "Fix the Acme webhook"    # → tasks/active/
ops search "ranking fusion"            # find anything, ranked
ops task done T-20260629-01            # folder = status
ops close                              # evening: summarize the day, flag loose ends
```

---

## The big idea, briefly

**Four roots, separated by location** (this is the key structural decision):

| Root | Holds | In git? |
|---|---|---|
| `~/ops` | **this repo** — knowledge (wiki), tasks, journal, the verbs | ✅ your own repo |
| `~/work` | code — every project is its *own* git repo (`products/ labs/ tools/ clients/`) | each project separately |
| `~/files` | binary assets — client docs, PDFs, datasets | ❌ (Time Machine / restic) |
| `~/dotfiles` | machine config — installs tools, puts `ops` on PATH | ✅ separately |

The siblings sit *next to* `~/ops`, never inside it. That keeps the knowledge repo small, plaintext,
and fast — and the safety wall (below) is rooted in this layout.

---

## Install — from template to your vault

This repo is a **template, not your data.** You make your own copy; one script wires the machine.

1. **Get your own copy.** On GitHub → **Use this template → Create a new repository** (your account,
   fresh history). Clone it to `~/ops` — the path matters, the safety wall is rooted there:
   ```sh
   git clone git@github.com:<you>/ops.git ~/ops && cd ~/ops
   ```
2. **Run setup** — puts `ops` on your PATH, installs zsh tab-completion, creates the sibling roots
   `~/work` + `~/files`, tracks the template as a fetch-only `upstream`, runs a health check, and makes
   the first commit. It never pushes.
   ```sh
   ./script/setup --lean
   ```
3. **Make it live:**
   ```sh
   git push -u origin main                                        # your repo, your GitHub
   pip install -r requirements.txt && ollama pull embeddinggemma  # optional: semantic search
   ops job apply                                                  # optional: schedule the nightly jobs
   ```

Now `ops` works from anywhere. Pull engine improvements later without touching your notes:
```sh
./script/update    # checks out ONLY engine files (bin/, skills/, docs…) from upstream; your content is never touched
```

**Requirements:** macOS or Linux, `git`, Python 3.10+. Everything below is optional and
auto-detected — nothing is required to run `ops`:
- Semantic search (stages 2–3): [Ollama](https://ollama.com) + `pip install -r requirements.txt`.
- Prettier note rendering: [`glow`](https://github.com/charmbracelet/glow) or `bat` (else a built-in renderer).
- Fuzzy note-picking: [`fzf`](https://github.com/junegunn/fzf) (else `ops wiki open` with no slug just lists notes).

---

## Using it #1 — in the terminal

The daily rhythm is five verbs: **`start` → `capture`/`triage`/`task` → `close`**, with **`week`** on
Fridays. Everything else is discoverable via `ops help`. The full surface:

| Group | Verbs |
|---|---|
| **System** | `help` · `status` · `doctor` (self-check) · `backup` (commit/push nag) · `index` · `consolidate` |
| **Flow** | `capture` · `triage` · `start` · `close` · `week` |
| **Knowledge** | `search` · `wiki` (open / edit / new / backlinks / stale / orphans) · `bookmark` (URL → note) |
| **Tasks** | `task` (list / add / show / move / done — folder = status) |
| **Work** | `new` (scaffold project/client) · `repo` (fleet health/clone/adopt) · `archive` · `files` (ingest binaries) · `sweep` (Desktop/Downloads decay) |
| **Business** | `invoice` (draft only — never sends) |
| **Jobs** | `job` (list / run / apply — schedule the nightly verbs via launchd) |

```sh
ops help                       # the whole surface, rendered from each verb's manifest
ops help triage                # usage for one verb
ops wiki new note "An idea"    # a structured note (frontmatter + slug, right folder)
ops wiki open rrf              # read a note, rendered in the terminal
ops wiki edit rrf              # open it in $EDITOR
ops wiki backlinks rrf         # what links here
ops bookmark https://… --archive   # save a URL as a note (title fetched); snapshot to ~/files
ops new project "Acme Webapp" --kind products   # scaffold a ~/work repo + wiki hub
ops doctor                     # is everything healthy?
```

You never have to remember file paths or formats — the verb owns placement; you provide the content.

### You don't have to memorize the verbs

Two conveniences make the terminal forgiving, both **zero-dependency** and both degrading gracefully:

- **Tab-completion (zsh).** `ops <Tab>` lists every verb *with its summary*; `ops wiki <Tab>`
  completes subcommands; `ops wiki open <Tab>` completes your **actual note slugs**; `ops task done
  <Tab>` completes your **live task IDs**. Candidates are pulled live from your content, so they never
  drift. `script/setup` installs it; to wire it by hand:
  ```sh
  mkdir -p ~/.zsh/completions && ln -sf ~/ops/script/completions/_ops ~/.zsh/completions/_ops
  # in ~/.zshrc, before `compinit`:   fpath=(~/.zsh/completions $fpath)
  ```
- **Readable notes.** `ops wiki open <slug>` renders Markdown in the terminal — headings, dimmed
  frontmatter, highlighted `[[links]]`. It auto-upgrades to [`glow`](https://github.com/charmbracelet/glow)
  or `bat` if either is installed, and prints raw Markdown when piped (`OPS_RENDER=raw` forces it).
- **Fuzzy-pick (optional).** Run `ops wiki open` (or `edit`) with **no slug** and, if
  [`fzf`](https://github.com/junegunn/fzf) is installed, you get a fuzzy picker with a live rendered
  preview — the "I don't remember the slug" escape hatch. Without `fzf` it just lists your notes.

---

## Using it #2 — with an AI agent

This is where it gets powerful. Point any capable agent at `~/ops` and it operates the *same* system,
behind the *same* guardrail. The mechanism is one contract, read by every agent:

- **`AGENTS.md`** — the operating contract (the open standard most agents read).
- **`skills/operate-ops/SKILL.md`** — the detailed manual the contract tells the agent to load.
- **`CLAUDE.md`** — a one-line bridge for Claude Code (which reads `CLAUDE.md`, not `AGENTS.md`).

The agent reads the contract, then drives the system through `ops <verb>` — it never hand-edits files
or invents commands, because the contract and the guardrail forbid it. **Whatever the agent does, the
guardrail still applies** (see below), so automating is safe by construction.

| Agent | Reads the contract as | How to point it at `~/ops` | Optional hardening |
|---|---|---|---|
| **Claude Code** (`claude`) | `CLAUDE.md` (bridge — already in the repo) | run `claude` from `~/ops` | `.claude/settings.json`: allow `Bash(ops:*)`, deny the rest |
| **Codex CLI** (`codex`) | `AGENTS.md` (native) | run from `~/ops` (or `--cd ~/ops`) | `.codex/config.toml` sandbox=`workspace-write`; symlink `.codex/skills → ../skills` |
| **Grok CLI / Grok Build** | `AGENTS.md` + `skills/` (both native) | run in `~/ops` | works out of the box — picks up `AGENTS.md`, skills, hooks |
| **Hermes** (Nous Research) | `AGENTS.md` (native) | set the gateway cwd to `~/ops`; add `~/ops/skills` as an external skill dir | config lives in `~/dotfiles` |
| **OpenClaw / nanoClaw** | `AGENTS.md` (native, workspace) | set the agent workspace to `~/ops` | tighten `exec-approvals` to allow only the `ops` binary |

**The universal rule:** any agent that can read a file and run a shell command can drive `~/ops` —
start it in the directory, and it reads `AGENTS.md` → loads `operate-ops` → runs `ops` verbs. Most
agents read `AGENTS.md` natively; only Claude needs the bridge (already shipped). For coding agents,
`ops` verbs can also call an agent *headlessly* as a scoped executor (e.g. `claude -p` with
`--allowedTools`) — the system stays in charge of *where/how*, the model supplies judgment.

> `ops doctor` checks the wiring: that `CLAUDE.md` bridges `AGENTS.md`, the skill exists, and any
> adapter symlinks/configs resolve. A broken adapter is how an agent silently starts improvising — so
> it's a first-class health check.

---

## How it stays safe

Before any verb runs, a guardrail classifies it. New verbs default to the safest class; nothing leaves
your machine without you. The same wall applies whether it's you or an agent at the keyboard.

| Class | Meaning |
|---|---|
| `read` | pure read — runs freely, even unattended |
| `safe_write` | writes inside the roots — every change is a revertible git diff |
| `draft_only` | produces a draft (e.g. `invoice`) — a human sends; the system never transmits |
| `confirm` | needs an explicit `--yes`; the default for new/undeclared verbs |
| `deny` | always refused: force-push, `rm -rf`, reading secrets, writing iCloud/family paths |

It's all git underneath, so even a mistaken `safe_write` is one `git revert` away.

---

## Finding anything — three local stages

All on your machine, no server. Keyword search works out of the box; the semantic stages are opt-in
and rebuildable from your Markdown.

1. **Keyword + graph** *(built in)* — SQLite FTS5 fused with the `[[wikilink]]` graph.
2. **Semantic vectors** *(opt-in, `OPS_VECTORS=1`)* — local EmbeddingGemma + LanceDB; multilingual, finds by meaning.
3. **Cross-encoder rerank** *(opt-in, `OPS_RERANK=1`)* — re-scores the top hits for precision.

```sh
ops index                                  # build/refresh the index from your notes
ops search "how do I stop a runaway agent" # ranked file#heading hits
```
The index lives in `.index/` and is disposable: `rm -rf .index && ops index` rebuilds it from the text.

---

## Keeping it safe & current

```sh
ops backup        # nags (exit 1) if ~/ops has uncommitted or unpushed work — never pushes for you
ops job apply     # render launchd jobs: index hourly, consolidate + close nightly, backup weekly
./script/update   # pull engine improvements from the template (your notes untouched)
```

---

## Project layout

```
ops                  # the dispatcher: ops <verb>  (symlinked onto your PATH by setup)
AGENTS.md  CLAUDE.md  # the agent contract (CLAUDE.md bridges to AGENTS.md)
bin/                 # the verbs — lib/ (shared: paths, guardrail, render…) + one folder per verb
skills/operate-ops/  # the operating manual any agent loads
wiki/                # KNOWLEDGE — your durable notes (see wiki/conventions.md)
tasks/               # folder = status: inbox/ active/ waiting/ done/
journal/  inbox/     # daily log · capture zone
templates/           # scaffolds: project-repo/, tax-formula.md
jobs/registry.json   # scheduled-job definitions (ops job apply → launchd)
script/              # setup · update · engine.txt (framework/content boundary) · completions/ (zsh)
docs/                # how-it-works.html · design/ (the spec) · DECISIONS.md (ADRs)
test/                # validation harness (dev-only; dropped from a lean vault)
```

The other roots (`~/work`, `~/files`, `~/dotfiles`) are created next to this one at setup.

---

## Status & tests

All **21 verbs of the design surface are built, guardrail-gated, and tested.** The retrieval engine,
the enforced guardrail, the installer (`script/setup`/`update`), and the jobs scheduler all work
end-to-end. **24 offline test suites** (run in CI) cover the verbs, the guardrail model, the agent indirection, retrieval, terminal ergonomics (completion + rendering), and the flows.

```sh
python3 test/run_all.py                          # every offline suite (stdlib only, no network)
python3 test/run_simulation.py --compare sonnet opus   # LLM-operator agnosticism check (needs a CLI)
```

**Agnosticism check (§18): passed.** The 18 adversarial operator scenarios were run through two
different operators (Claude Sonnet and Opus): **18/18 passed for both, with 0 divergences** — they
filed the same repo to the same root, refused the same actions, and traversed the wiki the same way.
Zero divergence means the contract (`AGENTS.md` + `operate-ops`) is unambiguous. (Cross-vendor agents
read the *same* contract; this harness measures it via Claude tiers because it asks the operator to
emit a JSON plan rather than act.) Everything else — seed notes, per-agent adapters (`.codex/`,
`.claude/`), the §6 agent indirection, and CI — is in place. The system is v1-complete; flipping
public is your call.

Design: [`docs/design/PERSONAL_OS_DESIGN.md`](docs/design/PERSONAL_OS_DESIGN.md) (v3.7) ·
decisions: [`docs/DECISIONS.md`](docs/DECISIONS.md).

## License

[MIT](LICENSE) © 2026 Tamás Gábor. Use it, fork it, make it yours.
