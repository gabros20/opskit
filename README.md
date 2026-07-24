# Personal Operating System (`~/ops`)

**A local-first, agent-agnostic platform for your knowledge, tasks, and work.**
Plaintext is the truth, git is the spine, and one `ops <verb>` command drives everything — by hand in
a terminal, on a schedule, through Obsidian or Raycast, or through any AI agent. No server, no cloud,
no lock-in. Your notes are Markdown files in your own git repo; you can read them, grep them, and walk
away from this tool at any time with nothing stranded.

[![License: MIT](https://img.shields.io/badge/License-MIT-C96442.svg)](LICENSE) · verbs generated (see `ops.json`) · offline test suites in CI · macOS / Linux · Python 3.10+ + git · zero required deps

> 🖱️ **Want the 2-minute tour first?** Open **[`docs/how-it-works.html`](docs/how-it-works.html)** —
> a single self-contained interactive walkthrough (no install, just open it in a browser). Click
> through the four roots, the verbs, the guardrail, and a **Flows** tab with animated `ops`
> flowcharts you can step through.

---

## What is this?

A "personal operating system" is the small set of habits and folders you use to run your life and
work — capturing thoughts, turning them into tasks, keeping durable notes, managing projects, and not
losing anything. This makes that explicit, durable, and **drivable by machines**:

- **Everything is a Markdown file** in `~/ops`, version-controlled with git. Indexes, embeddings, and
  every derived artifact are disposable caches rebuilt from the text — never the source of truth.
- **One command surface.** You never poke at files by hand. `ops <verb>` is the single door; each verb
  knows *where* things go and *how* to keep them safe. A guardrail classifies every invocation before
  it runs — the same wall whether it's you, a cron job, or an agent at the keyboard.
- **One machine contract.** Every verb speaks `--json` (one frozen, versioned envelope) and a fixed
  exit-code protocol; the generated [`ops.json`](ops.json) describes the whole surface — capabilities,
  per-verb schemas, usage hints. An agent doesn't read the manual and hope; it does a handshake.
- **Extensible without forking.** Your own verbs live in `plugins/` (never overwritten by updates),
  import a frozen SDK, and inherit the guardrail. Third-party packs install with an explicit trust
  ceiling — a plugin's self-declared permissions never take effect until *you* trust it.

### A minute in the life

```sh
ops orient                             # where was I? journal tail, tasks, inbox, health — one call
ops capture "RRF beats naive hybrid"   # a thought → inbox/ (zero decisions)
ops triage                             # it proposes: file as a wiki note? a task? — you approve
ops task add "Fix the Acme webhook"    # → tasks/active/
ops search "ranking fusion"            # ranked hits with snippets; add --json for machines
ops open rrf                           # one resolver: task id → note slug → file asset → search
ops close                              # evening: summarize the day, flag loose ends
```

---

## The big idea, briefly

**Four roots, separated by location** (this is the key structural decision):

| Root | Holds | In git? |
|---|---|---|
| `~/ops` | **this repo** — knowledge (wiki), tasks, journal, the verbs, your plugins | ✅ your own repo |
| `~/work` | code — every project is its *own* git repo (`products/ labs/ tools/ clients/`) | each project separately |
| `~/files` | binary assets — client docs, PDFs, datasets | ❌ (restic — see [durability](#durability--backup-and-share)) |
| `~/dotfiles` | machine config — installs tools, puts `ops` on PATH | ✅ separately |

The siblings sit *next to* `~/ops`, never inside it. That keeps the knowledge repo small, plaintext,
and fast — and the safety wall (below) is rooted in this layout.

---

## Install — from template to your vault

This repo is a **template, not your data.** You make your own copy; one script wires the machine.

**One-liner (the bootstrap funnel).** `script/get` checks prereqs (`git`, `python3`), clones the
vault to `~/ops`, and hands off to the same idempotent `script/setup` below — no sudo, and it refuses
to overwrite an existing install. Read it before you pipe it (that's the point of publishing it):
```sh
# inspect first — pin TLS, verify the published hash, read it, THEN run it
curl --proto '=https' --tlsv1.2 -fsSL \
  https://raw.githubusercontent.com/gabros20/personal-operating-system/main/script/get -o get.sh
shasum -a 256 get.sh   # compare against get.sh.sha256 published beside it
sh get.sh              # installs a LEAN vault, non-interactively (add --full to keep the dev test/ tree)
```
Then finish setup with the guided first-run — **`ops setup --wizard`** (≤5 skippable prompts, safe
defaults: skeleton on, search/models/automation off) — or **`ops setup --all --yes`** to advance
every safe layer non-interactively.

**Kick the tyres first (`--demo`).** Clone into a throwaway tmp dir seeded with example notes — the
roots, the `ops` symlink, and completion all land *inside* that one dir, so `capture`/`search`/`week`
work immediately and a single `rm -rf` walks away, touching nothing else:
```sh
sh get.sh --demo        # prints the vault path and the one directory to delete
```

**Prefer to do it by hand?** The template flow below is exactly what `script/get` automates:

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
   ops setup --wizard                                             # guided first-run (or: ops setup --all --yes)
   ```
   `ops setup --wizard` walks the optional layers interactively; `ops setup` (no args) is the
   read-only dashboard, `ops setup --all --yes` advances every safe layer, and `ops setup <layer>
   --dry-run` previews one without installing. Full reference — semantic search, local models,
   backups, and scheduled jobs: [`docs/setup.md`](docs/setup.md).

Now `ops` works from anywhere. Pull engine improvements later without touching your notes:
```sh
./script/update    # 3-way merge of ONLY the engine files — your content AND your local engine fixes survive
```

> [!NOTE]
> `script/update` does a per-file **3-way merge** keyed on the last-synced upstream commit
> (`.ops-engine-ref`): unmodified engine files fast-forward, locally patched ones merge, conflicts are
> surfaced with markers — an update never silently discards a fix you made.

**Requirements:** macOS or Linux, `git`, Python 3.10+. Everything below is optional and
auto-detected — nothing is required to run `ops`:
- Semantic search (stages 2–3): [Ollama](https://ollama.com) + `pip install -r requirements.txt`.
- Media extraction tiers (`ops files extract`): `pymupdf4llm` (PDF), `mlx-whisper` /
  `faster-whisper` (audio), `yt-dlp` (video captions) — each tier degrades gracefully with a
  one-line install hint.
- Image reading (`ops files extract` on images, `--describe` for a VLM caption): quality OCR via
  GLM-OCR/DeepSeek-OCR and VLM description via Qwen3-VL/moondream, both through `mlx-vlm` on Apple
  Silicon or Ollama on any host, falling back to `ocrmac` / `tesseract` with neither installed. See
  [`docs/image-reading.md`](docs/image-reading.md) for per-host setup.
- Search enrichment (`ops enrich`, auto-wired into `files extract`/`bookmark`): generates a
  `description` + `keywords` per source via a local Ollama model (`gemma4:e4b` default, EN+HU),
  falling back to a deterministic stdlib keyword floor with none installed. `ops models` manages the
  model behind this and every other stage (list/pull/stop/test). See
  [`docs/search-enrichment.md`](docs/search-enrichment.md).
- Off-machine backup: [`restic`](https://restic.net).
- Terminal niceties: [`glow`](https://github.com/charmbracelet/glow) or `bat` (rendering),
  [`fzf`](https://github.com/junegunn/fzf) (fuzzy pickers, live search sessions),
  [`trafilatura`](https://github.com/adbar/trafilatura) (better bookmark extraction).

**Platform notes.** *Homebrew:* if a tap ever ships, it is **only ever a tiny bootstrapper** that runs
`script/get` (the chezmoi model) — never a formula that clones your notes into a brew-owned prefix, the
opposite of a user-owned vault. *Windows:* use **WSL2** (a normal Linux install inside it); there is no
native PowerShell path.

---

## Using it #1 — in the terminal

The daily rhythm is five verbs: **`start` → `capture`/`triage`/`task` → `close`**, with **`week`** on
Fridays and **`orient`** whenever you (or an agent) sit down mid-stream. Everything else is
discoverable via `ops help`. The full surface:

| Group | Verbs |
|---|---|
| **System** | `help` · `status` · `orient` (one-call session bootstrap) · `doctor` (self-check) · `setup` (layered installer — doctor's fixer twin) · `backup` (nag + restic family) · `index` · `consolidate` · `models` (local-model stack: list/pull/stop/test) · `plugin` |
| **Flow** | `capture` · `triage` · `start` · `close` · `week` |
| **Knowledge** | `search` · `open` (one resolver for anything) · `wiki` (open / edit / new / backlinks / stale / orphans / canvas) · `bookmark` (URL → note) · `enrich` (description/keywords for search) · `organize` (scan → review → apply) |
| **Tasks** | `task` (list / add / show / move / done — folder = status) |
| **Work** | `new` (scaffold project/client/**verb**) · `repo` (fleet health/clone/adopt) · `archive` · `files` (ingest/extract/distill/link binaries) · `sweep` (Desktop/Downloads decay) |
| **Business** | `invoice` (draft only — never sends) · `share` (expiring capability links, agent-readable `.md` — never auto-sends) |
| **Jobs** | `job` (list / run / apply — schedule the nightly verbs via launchd) |

(Plus two hidden plumbing verbs: `ops mcp`, the agent transport, and `__complete`, which powers
tab-completion.)

```sh
ops help                       # the whole surface, rendered from each verb's manifest
ops help triage                # usage + hints for one verb
ops orient                     # dashboard; --line gives a ≤60-char string for your shell prompt
ops open T-20260702-01         # resolves task ids, note slugs, file assets — --edit/--reveal/--obsidian
ops search                     # bare, in a tty with fzf: a live-reload search session with preview
ops wiki new note "An idea"    # a structured note (frontmatter + slug, right folder)
ops wiki canvas acme           # a JSON Canvas map of the wikilink graph around a hub
ops bookmark https://… --archive   # save a URL as a note (title fetched); snapshot to ~/files
ops new project "Acme Webapp" --kind products   # scaffold a ~/work repo + wiki hub
ops files ingest brief.pdf --client acme --extract  # file it + extract text into a derived note
ops doctor                     # is everything healthy?
```

You never have to remember file paths or formats — the verb owns placement; you provide the content.

### You don't have to memorize the verbs

- **Tab-completion (zsh).** `ops <Tab>` lists every verb *with its summary*; `ops wiki open <Tab>`
  completes your **actual note slugs**; `ops task done <Tab>` completes your **live task IDs**.
  Installed by `script/setup`; candidates are pulled live from your content, so they never drift.
- **Readable notes.** `ops wiki open <slug>` renders Markdown in the terminal (auto-upgrades to
  `glow`/`bat`; raw when piped).
- **Fuzzy everything (optional).** With `fzf` installed: `ops wiki open` with no slug is a picker
  with live preview, `ops open` with no target is a picker over *everything*, and bare `ops search`
  is a type-to-requery session.
- **`--dry-run` everywhere.** Every mutating verb accepts `--dry-run` and prints what *would* happen —
  and the guardrail treats a dry-run as a read, so even confirm-class verbs are explorable without
  `--yes`.

---

## Using it #2 — with an AI agent

This is where it gets powerful. Point any capable agent at `~/ops` and it operates the *same* system,
behind the *same* guardrail. Three layers make that reliable:

**1. The contract (what the agent reads).**
- **`AGENTS.md`** — the operating contract (the open standard most agents read).
- **`skills/operate-ops/SKILL.md`** — the detailed manual the contract tells the agent to load.
- **`CLAUDE.md`** — a one-line bridge for Claude Code (which reads `CLAUDE.md`, not `AGENTS.md`).

**2. The machine contract (what the agent parses).** Every verb takes `--json` and emits one frozen
envelope (`{"ops_json": 1, "ok": …, "data"|"error": …}`; NDJSON rows for list verbs). Exit codes are a
protocol, not an accident: `0` ok · `2` usage · `3` needs `--yes` · `4` not found · `5` denied — and
error messages carry the exact remediation, so a refusal teaches the caller the correct next call.
[`ops.json`](ops.json) (`ops.json/3`) is the complete I/O contract: every verb's args, output schema,
risk class, display group, source (engine or plugin), a usage hint, and — for compound verbs — an
`actions[]` array describing each subcommand's typed args + completion providers, plus a
`capabilities` block (vectors? reranker? which agent?) re-detected on every regeneration. `ops complete
--json` returns completion candidates from the same contract. Details:
[`docs/machine-contract.md`](docs/machine-contract.md).

**3. The transport (how a host connects).** For hosts that speak [MCP](https://modelcontextprotocol.io),
`ops mcp` is a **stateless stdio server** — spawned per session, dies with it (no daemon, no HTTP, no
resident state). Its tool list is *generated from ops.json*, so every verb and every installed plugin
shows up automatically with schemas and hints; each tool call shells back through `ops <verb> --json`,
so the guardrail and `.logs/` stay the single enforcement path. A confirm-class call without `--yes`
returns a structured "needs `--yes`" result — the server never auto-confirms.
```sh
ops mcp --setup    # prints:  claude mcp add ops -- /abs/path/to/ops mcp
```

| Agent | Reads the contract as | How to point it at `~/ops` |
|---|---|---|
| **Claude Code** (`claude`) | `CLAUDE.md` bridge, or `ops mcp` | run `claude` from `~/ops`, or `claude mcp add ops -- ~/ops/ops mcp` |
| **Codex CLI** (`codex`) | `AGENTS.md` (native) | run from `~/ops` (or `--cd ~/ops`) |
| **Grok CLI / Grok Build** | `AGENTS.md` + `skills/` (native) | run in `~/ops` |
| **Any MCP host** | tool list from `ops.json` | register `ops mcp` as a stdio server |
| **Anything else** | `AGENTS.md` | if it can read a file and run a shell command, it can drive `ops` |

> `ops doctor` checks the wiring: that `CLAUDE.md` bridges `AGENTS.md`, the skill exists, and adapter
> symlinks/configs resolve. A broken adapter is how an agent silently starts improvising — so it's a
> first-class health check.

---

## Extending it — plugins, not forks

Your own verbs never touch `bin/` (the engine owns it; updates would overwrite you). Instead:

```sh
ops new verb standup                  # scaffolds plugins/local/standup/ — run.py + cmd.json
ops plugin add you/ops-pomodoro --yes # install a pack from a repo (or a local path)
ops plugin list                       # what's installed, pinned to which commit, trusted or not
ops plugin trust ops-pomodoro --yes   # lift the trust ceiling to the pack's declared risks
```

- **Same shape, same rules.** A plugin verb is exactly an engine verb (`run.py` + `cmd.json`) resolved
  from `plugins/` — it appears in `ops help`, `ops.json`, tab-completion, and MCP automatically, and
  the guardrail gates it identically. Engine names are reserved; a plugin can never shadow a core verb.
- **Trust is explicit.** A pack's self-declared risk classes **never take effect at install** — every
  verb from an untrusted pack is capped at `confirm` until you run `ops plugin trust`. Even trusted
  plugins keep the transmit-block and the path-wall. Updates re-pin explicitly; nothing auto-updates.
- **A frozen SDK.** Plugins import [`bin/lib/api.py`](bin/lib/api.py) only (`OPS_API_VERSION = "1.0"`):
  paths + journal, `classify` (the guardrail seam), note-type loaders, `run_agent`, and the `--json`
  emitters. A contract test snapshots every signature — the API can't drift silently.

How to write one: [`docs/plugins.md`](docs/plugins.md).

---

## Frontends — rent Obsidian, ship Raycast, polish the terminal

The vault is plaintext, so the best "app" is one you already have:

- **Obsidian (Frontend Zero).** `ops doctor --init` offers a one-time config pack
  (`templates/obsidian/`) tuned for this vault: wikilinks kept native, attachments routed out of
  `wiki/`, plus four starter **Bases** (active projects, open tasks, stale notes, recent decisions)
  as saved queries over the same frontmatter. `ops wiki canvas <hub>` renders the wikilink graph as a
  [JSON Canvas](https://jsoncanvas.org) file Obsidian opens natively. Obsidian **opens** notes
  (`ops open <slug> --obsidian`); all *writes* still go through verbs. `ops index --changed` picks up
  external edits incrementally, and the frontmatter reader tolerates Obsidian's Properties normalizer
  without ever rewriting your files to fight it. Compatibility spec: [`docs/obsidian-compat.md`](docs/obsidian-compat.md).
- **Raycast.** [`frontends/raycast/`](frontends/raycast/) ships five zero-build script commands —
  quick-capture, search, task add/list, inline status. Every one shells to `ops` on your PATH: zero
  privileged access, guardrail applies.
- **Mobile = git, documented.** No app. Obsidian mobile or GitJournal over your private remote, an
  iOS share-sheet Shortcut into `inbox/`, git push/pull as the only sync transport:
  [`docs/mobile-and-capture.md`](docs/mobile-and-capture.md).

---

## The knowledge pipeline — artifacts in, linked knowledge out

Binary artifacts (PDFs, recordings, screenshots, URLs) become searchable, linked, *honestly labeled*
knowledge in three deterministic steps:

```sh
ops files ingest talk.pdf --research --extract   # 1. file it + extract text → a DERIVED note
ops files distill talk                           # 2. compile concept notes (drafts) from the extract
ops organize                                     # 3. scan the vault for links/dupes/fixes → proposals
ops organize review                              # page through each proposed op with its exact diff
ops organize apply --yes                         # replay ONLY what you approved — one git commit per op
```

- **Extraction is tiered and local** — PDF/audio/image/video each try the best locally available tool
  and degrade gracefully (Apple-Silicon ASR at ~3000× realtime when available; captions before
  transcription for video). Originals stay byte-for-byte in `~/files`.
- **Provenance is a checked convention.** Three note planes — *human*, *derived* (`derived_from` +
  `source_sha256` + `tool`), *agent* (`author: agent`, gated as `status: draft` until you promote it
  in `ops triage`). `doctor` flags violations; `ops search --author human` excludes machine material.
  An agent artifact can never quietly become "truth".
- **Self-organization can't hallucinate an edit.** `organize scan` generates proposals with zero LLM
  involvement (a model, if configured, only *ranks* them); the op catalog is closed (add link, refresh
  hub, normalize tag, fix frontmatter, retitle, flag duplicate, propose merge — nothing else parses);
  apply is deterministic replay of approved ops with an edit budget, protected paths, and one revert-
  able git commit per op. The scan is schedulable; **apply never is**.

---

## How it stays safe

Before any verb runs, the guardrail classifies it. New verbs default to the safest class; nothing
leaves your machine without you. The same wall applies whether it's you, a job, a plugin, or an agent.

| Class | Meaning |
|---|---|
| `read` | pure read — runs freely, even unattended |
| `safe_write` | writes inside the roots — every change is a revertible git diff |
| `draft_only` | produces a draft (e.g. `invoice`) — a human sends; the system never transmits |
| `confirm` | needs an explicit `--yes` (exit `3` + the exact re-run when missing); the default for new/undeclared verbs — and the ceiling for untrusted plugins |
| `deny` | always refused (exit `5`): force-push, `rm -rf`, reading secrets, writing iCloud/family paths |

`--dry-run` on a mutating verb is treated as a read — preview anything, even confirm-class verbs,
without `--yes`. And it's all git underneath, so even a mistaken `safe_write` is one `git revert` away.

---

## Finding anything — three local stages

All on your machine, no server. Keyword search works out of the box; the semantic stages are opt-in
and rebuildable from your Markdown.

1. **Keyword + graph** *(built in)* — SQLite FTS5 fused with the `[[wikilink]]` graph, with snippets
   in the results so you (or an agent) judge relevance without opening files.
2. **Semantic vectors** *(opt-in, `OPS_VECTORS=1`)* — local EmbeddingGemma + LanceDB; multilingual, finds by meaning.
3. **Cross-encoder rerank** *(opt-in, `OPS_RERANK=1`)* — re-scores the top hits for precision.

```sh
ops index                                  # build/refresh the index from your notes
ops search "how do I stop a runaway agent" # ranked file#heading hits with snippets
ops search "acme pricing" --author human   # exclude derived/agent material
```
The index lives in `.index/` and is disposable: `rm -rf .index && ops index` rebuilds it from the text.

---

## Durability — backup and share

**Backup before share: `~/files` is the one root where loss is irreversible.**

```sh
ops backup            # the read-only nag: exit 1 if ~/ops is uncommitted/unpushed — never pushes for you
ops backup init --yes # once: local SSD + B2 restic repos, keys as op:// references, launchd plist rendered
ops backup status     # snapshot age per target; exit 1 if stale >48h
ops backup drill --yes# restore to tmp and diff — a backup that's never been restored is a hypothesis
ops backup bundle     # git-bundle ~/ops + every ~/work repo into ~/files (catches remote-less repos)
```

The scheduled cloud push runs from launchd invoking restic **directly with an append-only key** —
outside the agent/verb surface entirely, so even a fully compromised agent can only *add* to backup
history, never erase it.

**`ops share`** publishes a note (or a collection) to your own Cloudflare Worker under a single
**capability URL** — a 24-char unguessable token. The bare link renders HTML in a browser; append
`.md` and the same link returns the raw wiki markdown, so any chat or coding agent can read it with
a plain fetch (ADR-008 deliberately trades zero-knowledge for one-link agent ergonomics). Expiring,
revocable, ledgered in git, and confirm-gated: the verb's
output is a link, and *you* send it. `ops publish` (a public digital garden) is deliberately a
separate future verb. Details: [`docs/backup-and-share.md`](docs/backup-and-share.md).

---

## Project layout

```
ops                  # the dispatcher: ops <verb>  (symlinked onto your PATH by setup)
ops.json             # GENERATED — the machine contract (surface + schemas + capabilities)
AGENTS.md  CLAUDE.md # the agent contract (CLAUDE.md bridges to AGENTS.md)
bin/                 # the ENGINE verbs — lib/ (shared + api.py SDK) + one folder per verb
plugins/             # YOUR verbs + installed packs — never touched by updates
frontends/raycast/   # zero-build Raycast script commands
skills/operate-ops/  # the operating manual any agent loads
wiki/                # KNOWLEDGE — your durable notes (see wiki/conventions.md)
tasks/               # folder = status: inbox/ active/ waiting/ done/
journal/  inbox/     # daily log · capture zone (inbox/organize/ holds proposal queues)
templates/           # scaffolds: project-repo/, obsidian/ (config pack + Bases), tax-formula.md
jobs/registry.json   # scheduled-job definitions (ops job apply → launchd)
script/              # get (installer) · setup · update (3-way merge) · engine.txt · completions/
docs/                # the docs set — see docs/README.md
test/                # 42 offline suites (dev-only; dropped from a lean vault)
```

The other roots (`~/work`, `~/files`, `~/dotfiles`) are created next to this one at setup.

---

## Status & tests

**v4-complete.** Every verb (the full set is generated — see `ops.json`) plus the hidden MCP transport is built, guardrail-gated, documented in
the machine contract, and tested: the **offline suites** run in CI, covering the guardrail model, the
exit-code protocol, the `--json` contract (round-tripped against every verb's declared schema), the
plugin resolver + trust ceiling, the MCP handshake, the extraction/organize pipeline, and backup/share
— all stdlib-only, no network.

```sh
python3 test/run_all.py                          # every offline suite (stdlib only, no network)
python3 test/run_simulation.py --compare sonnet opus   # LLM-operator agnosticism check (needs a CLI)
```

**Agnosticism check: passed.** 18 adversarial operator scenarios, two different operators, 18/18 for
both with **0 divergences** — same filing, same refusals, same traversal. Zero divergence means the
contract (`AGENTS.md` + `operate-ops`) is unambiguous.

Docs: [`docs/README.md`](docs/README.md) (the map) · architecture:
[`docs/architecture.md`](docs/architecture.md) · design spec:
[`docs/design/PERSONAL_OS_DESIGN.md`](docs/design/PERSONAL_OS_DESIGN.md) · decisions (ADRs):
[`docs/DECISIONS.md`](docs/DECISIONS.md) · contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 Tamás Gábor. Use it, fork it, make it yours.
