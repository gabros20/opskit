# v4 proposal — ops as a platform (machine contract → plugins → frontends → pipeline → durability)

**Status: ACCEPTED & IMPLEMENTED (2026-07-02) — see ADR-007 in `docs/DECISIONS.md`.** Parts 0–5
implemented on branch `v4-platform`; 5.3 (`ops publish`) and 3.5 (TUI) remain deferred as proposed.

**Provenance.** Produced 2026-07-01 by a 15-agent research workflow: 10 web researchers (CLI-PKM
landscape, Obsidian ecosystem, plugin architectures, frontends, sharing infra, backup/sync, media
pipelines, LLM self-organization, X.com community discourse, install DX) and 5 independent design
panels (core architecture, terminal UX, interop/frontends, knowledge pipeline, share/sync/durability),
synthesized by the main agent. Where multiple panels converged independently, that is noted — it is
the strongest signal in this document.

---

## The verdict in one paragraph

The system's philosophy (plaintext truth, git spine, one verb surface, guardrail, agent-agnostic) is
**validated by the field** — Taskwarrior 3's SQLite-as-truth regression storm, Dendron's host-lock-in
death, and gbrain's binary-bloated git wiki are all cautionary tales this design already avoids. The
gap is not philosophy but **surface**: ops today is an excellent *closed* system. v4 should make it an
excellent *platform* — one machine-readable contract (`--json` + exit codes + ops.json v2), one
extension mechanism (`plugins/` + `ops plugin` + a frozen `lib/api.py`), one agent transport
(`ops mcp`, stateless stdio), one rented frontend (Obsidian as Frontend Zero), one built frontend tier
(Raycast script commands), one ingestion pipeline (`files extract`/`distill` with provenance), one
self-organization loop (`ops organize` typed-op proposal queue), and one durability floor (restic
family + share worker). Every piece below is buildable in this codebase's existing idioms
(one-folder-per-verb, cmd.json, auto-detected optional deps, deterministic fallback).

**Convergence highlights** (independent agreement across panels):
- 3/5 panels named the `--json` envelope the single keystone dependency. Ship it first.
- 2/5 panels independently found the same latent **data-loss bug**: `ops new verb` scaffolds into
  `bin/`, which is inside the `script/engine.txt` checkout boundary — a future upstream verb with the
  same name is silently checked out **over the user's code** by `script/update`.
- 3/5 panels independently reached the same daemon verdict: **no daemon, ever** (for now) — the only
  sanctioned resident-ish process is a client-spawned, stateless stdio MCP child.
- 2/5 panels converged on the same self-organization safety architecture: closed typed-op catalog
  (Mem0 lesson), propose-then-approve queue, one-git-commit-per-op, edit budgets, protected paths,
  scheduled scan / never-scheduled apply.

---

## Part 0 — Corrections & solidification (do these regardless of everything else)

These fix real defects in what already exists.

### 0.1 `script/update` → 3-way merge (stop silently destroying local engine edits)
Today `git checkout upstream/main -- <path>` per engine path **silently discards** any local fix a
user made to a verb. Adopt the copier/cruft pattern: record the last-synced upstream commit in a
tracked `.ops-engine-ref`; per engine path, if locally unmodified since that ref → fast-path checkout
as now; if modified → `git merge-file` (base=ref, theirs=upstream, ours=working tree), stage the
result, surface conflict markers in the summary. First run without the ref file falls back to current
behavior with a loud warning. ~60 lines of bash delta. **Effort: M.**

### 0.2 Retarget `ops new verb` out of `bin/`
User-authored verbs must scaffold into `plugins/local/<verb>/` (see Part 2) — never into `bin/`,
which upstream owns. Until the multi-root resolver lands, an interim guard: `ops new verb` warns that
the verb lives inside the update boundary. **Effort: S (after 2.1).**

### 0.3 Exit-code protocol + self-teaching errors
Standardize: `0` ok, `1` unexpected, `2` usage, `3` guardrail-confirm-needed, `4` not-found,
`5` guardrail-deny. Change the dispatcher's `|| exit 1` to propagate, and guardrail.py to exit 3 vs 5.
Unknown verb → `difflib.get_close_matches` did-you-mean. Guardrail CONFIRM refusal prints the exact
remediation (`re-run: ops archive foo --yes`), not just the class name. Normalize usage errors to
stderr + exit 2 (search does; capture/task/wiki are inconsistent). For an agent, error messages ARE
the feedback loop. **Effort: S.**

### 0.4 Doctor: sync-wall + second-remote checks
Fail if `~/ops` or any `~/work/**/.git` resolves under iCloud/Dropbox/Syncthing paths (extend the
existing walled-off markers — Syncthing's own maintainers say never sync `.git`). Warn if `~/ops` has
fewer than two push remotes. Add a frontmatter YAML round-trip check (flags notes Obsidian's
Properties normalizer would churn). **Effort: S.**

### 0.5 `--dry-run` as a system-wide contract
Standardize `--dry-run` on every mutating verb; declare it in cmd.json (`"dry_run": true`); teach
`guardrail.gate()` one rule: a confirm-class verb invoked with `--dry-run` is allowed without `--yes`,
downgraded to read (a true dry-run IS a read). Makes confirm-class verbs explorable for humans and
agents alike. **Effort: M (rolled out verb-by-verb).**

---

## Part 1 — The keystone: one machine contract

> Everything else in this proposal consumes this. Ship it before anything in Parts 2–4.

### 1.1 `--json` envelope, implemented once in `bin/lib/output.py`
A global `--json` flag on every verb. Frozen, versioned envelope:
`{"ops_json": 1, "ok": true|false, "verb": "...", "data": {...}, "error": {"code", "message", "hint"}}`.
NDJSON rows after a header object for multi-row verbs (`search`, `task list`, `week`, `files list`);
single object for scalar verbs. Human text renders when `--json` absent (or to stderr under it).
Three helpers: `emit(data)`, `emit_rows(iter)`, `fail(code, msg, hint)`. Conversion per verb is
mechanical — the verbs already compute structured dicts internally.

**Discipline is the real work** (the `jc` lesson: an unstable machine schema is worse than none):
- each `cmd.json` gains an `output` block (field names/types); `manifest.py` copies it into `ops.json`
  so **ops.json becomes the complete I/O contract** — a third party reads it and never imports lib;
- one `test/run_json.py` contract test round-trips every read-class verb against its `output` block;
- envelope changes only with an explicit `ops_json` version bump.

**Effort: M.**

### 1.2 `ops.json` v2 — capability negotiation + agent hints
Top level gains `{"schema": "ops.json/2", "ops_version", "api_version", "json_envelope": 1,
"capabilities": {"vectors": <detected>, "rerank": <detected>, "agent": $OPS_AGENT, "plugins": [...]}}`;
per verb: `source` (engine|plugin:<name>), the `output` block, and a short `hints` string
(when-to-use, common mistakes — basic-memory's tool-annotation pattern, shown in `ops help <verb>`
too). All detection via `importlib.util.find_spec` in `write_manifest()`; nothing persisted that
isn't re-detected. Turns "read the manual and hope" into a deterministic handshake for any agent.
**Effort: S.**

---

## Part 2 — Extensibility: plugins, SDK, MCP

### 2.1 Multi-root verb resolution
Resolve verbs in strict precedence: `bin/` (engine, RESERVED — always wins; a plugin can never shadow
a core or future-core verb) → `plugins/<pack>/<verb>/` → colon-separated `$OPS_PATH`. A plugin verb is
the exact same shape as an engine verb (`run.py` + `cmd.json`) — zero new runtime. `plugins/` is NOT
in `engine.txt`, so it is user-owned, survives updates, and version-controls inside the user's vault.
Touch points: a `resolve_verb()` in lib, one dispatcher line, `guardrail._known_verbs()`/`risk_of()`
use the resolver, `manifest.load_cmds()` globs plugin cmd.jsons and tags `_source`, renders a PLUGINS
group — so **every agent discovers plugins through ops.json with no other change**. **Effort: M.**

### 2.2 `ops plugin` — gh-extensions distribution, krew integrity, guardrail trust ceiling
`ops plugin add owner/repo[@tag]` (confirm-class) shallow-clones into `plugins/<name>/`, validates
`plugin.json` against a schema (name, semver, `min_ops_version`, declared verbs each with
risk/reads/writes), prints the declared surface, records resolved commit sha + accepted risks in a
committed `plugins/plugins.lock.json`. Subcommands: `add / list / update / remove / trust`.

**The trust model (non-negotiable):** a plugin's self-declared risk NEVER takes effect at install.
The guardrail caps every verb from an untrusted pack at `confirm`; `ops plugin trust <name> --yes`
records the accepted ceiling in the lockfile; even trusted plugins keep the transmit-block and
path-wall. `update` re-resolves the pin explicitly, refuses to cross `min_ops_version`, never
auto-updates (the gh cli/cli#13551 pin-bypass bug is the named anti-pattern). Document krew's stance:
installed ≠ audited; trust is per-owner. No central registry — the git repo IS the plugin; a curated
`ops-plugins-index` (git repo of pointers, krew-index model) can come later without any hosted
service. **Effort: L.**

### 2.3 `bin/lib/api.py` — the frozen public SDK
One module re-exporting the blessed subset plugins may import (~15 names): `paths` essentials
(+`append_journal`), `guardrail.classify` (so plugin verbs inherit the path-wall instead of skipping
it — the Iron Law seam), notetype loaders, `agent.run_agent`, `output.emit/emit_rows/fail`.
`OPS_API_VERSION = "1.0"`, explicit `__all__`, a contract test that snapshots signatures and fails CI
on removal. `plugin.json` declares `api: ">=1,<2"`. Everything else in lib is private. **Effort: S.**

### 2.4 `ops mcp` — the agent transport (and the daemon verdict)
**Verdict: no daemon.** Fork/exec is fast enough at human/agent interaction rates; a resident process
accumulates state plaintext can't rebuild. The only future exception: an opt-in warm-embedding cache,
only after *measured* cold-start pain.

Instead: `ops mcp` (hidden/read-class, like `__complete`) — a **stateless stdio MCP server**, spawned
by the agent host per session, dies with it. Tool list is *generated from ops.json v2* (summaries +
hints → descriptions, args → input schema); tool call = `subprocess ops <verb> --json` — execution
**re-enters through the dispatcher**, so the guardrail and `.logs/` remain the single enforcement
path. Confirm-class calls return a structured needs-`--yes` result (exit 3), never auto-pass.
Plugins appear as MCP tools automatically. Setup prints the `claude mcp add ops -- ops mcp` line.
This is how basic-memory and gbrain operationalize agent-agnosticism in 2026. **Effort: M.**

---

## Part 3 — Interop & frontends

### 3.1 Obsidian as Frontend Zero (rent, don't build)
The ruthless "which frontend first" answer: **adopt Obsidian** — read, edit, graph, backlinks, AND
mobile, for the cost of a config pack.
- Ship `templates/obsidian/` (app.json: `newLinkFormat=shortest`, `useMarkdownLinks=false`,
  attachment path routed OUT of wiki/; appearance/core-plugins/hotkeys). `ops doctor --init` offers a
  one-time copy to `.obsidian/` (user-owned; engine.txt must NOT own it). Gitignore
  `workspace*.json`, `.obsidian/cache`, `.trash/`, `.smart-env/`.
- `ops wiki open <slug> --obsidian` (or `OPS_OPEN=obsidian`): `open obsidian://open?vault=…&file=…` —
  plugin-free native URI, local IPC not network. **URIs are for OPENING only; all writes go through
  verbs** (Advanced URI write mode bypasses the guardrail — forbidden).
- External-edit tolerance: `ops index --changed` (incremental reindex by mtime vs a stored build
  timestamp; ignore `.obsidian/`, `.trash/`); frontmatter reader tolerates Obsidian Properties
  normalization (key reorder, flow-vs-block lists) — tolerate on read, re-normalize only at index
  time, **never rewrite user files to fight the normalizer**.
- Doctor lints for what Obsidian silently mangles: lowercase-hyphenated tags, wikilinks in body only,
  the YAML round-trip check (0.4).
- Vendor kepano/obsidian-skills' OFM spec into `docs/` as the *normative* compatibility reference so
  "Obsidian-compatible" is checkable, not implicit.
**Effort: S–M.**

### 3.2 Bases + JSON Canvas — plaintext views ops generates, Obsidian renders
Starter `.base` files (Obsidian Bases YAML — active-projects, open-tasks, stale-notes,
recent-decisions) as saved queries over the same frontmatter; both open specs, both git-versioned.
`ops wiki canvas <hub|tag>` emits a deterministic `.canvas` (JSON Canvas, MIT) from the wikilink
graph — a visual layer with no server and no Obsidian required to produce it. Optionally mirror Bases
filter semantics later in an `ops query` verb (kills the Dataview gap). **Effort: M.**

### 3.3 Raycast Script Commands — the first BUILT frontend
`frontends/raycast/` (in engine.txt so improvements flow): 4–6 zero-build script commands —
quick-capture, search (`--json`, Enter opens via Obsidian), task add/list, status inline. Plus one
Apple Shortcut (Receive Text / share sheet → `ops capture`) for global-hotkey capture. Every
invocation shells to `ops` on PATH → guardrail + logs apply; the frontend has zero privileged access.
Graduate to a React extension only after this tier proves the `--json` surface. **Effort: S
(capture can ship today; the rest gated on 1.1).**

### 3.4 Terminal ergonomics
- **`ops open <target>`** — one read-class resolver for every addressable thing (task id → wiki slug
  → files asset → search query), flags `--edit / --reveal / --obsidian`; bare `ops open` = fzf picker
  with preview. Keep `wiki open`/`files open`/`task show` as thin delegates — **never remove existing
  spellings** (muscle memory + deployed vaults).
- **`ops orient`** — one-call session bootstrap replacing SKILL.md §3's multi-step ritual: journal
  tail, tasks, inbox count, pending proposals, index/backup age, git dirtiness, recent notes. Three
  renders: human dashboard, `--json` (agent orientation in one call), `--line` (≤60-char cached
  string for starship/tmux). Read-only, safe to call from a prompt hook.
- **Search as a session**: FTS5 `snippet()` in results (agents judge relevance without opening
  files); bare `ops search` in a tty → fzf live-reload session with preview; `--open` jumps to top
  hit.
- **Mobile-lite** = documentation, not an app: Obsidian mobile or GitJournal (native
  wikilinks+frontmatter) over the private remote via Working Copy; an iOS Shortcut appending into
  `inbox/`; git push/pull as the ONLY sync transport. **Effort: S each.**

### 3.5 TUI — deliberately last
Optional Textual (auto-detected like trafilatura), scoped to `ops triage --tui` (full-screen inbox
review, single-key routing) — interactivity pays only in batch-review verbs. Python so it imports lib
in-process. Do NOT TUI-ify one-shot verbs. **Effort: L; tier 3.**

---

## Part 4 — Knowledge pipeline: extract → distill → organize

### 4.1 `ops files extract` — tiered local extraction into derived notes
`ops files ingest <path> [--extract]` / `ops files extract <slug> [--reextract]`. Original stays
byte-for-byte in `~/files`; shadow note stays the pointer; extraction emits a SIBLING derived note
`wiki/files/<slug>.extract.md` with `type: extract|transcript`, `derived_from: "[[<slug>]]"`,
`source_sha256`, `tool: <name> <version>` — **extraction never masquerades as source truth**, and
same-bytes+same-tool re-runs are idempotent no-ops.

Tier tables per media type, each an auto-detected optional dep (the established trafilatura pattern —
try/except import, deterministic degrade, one-line install hint):
| Media | Tier 1 | Fallbacks |
|---|---|---|
| PDF | `pymupdf4llm` | `docling` (heavy, opt-in) |
| Audio/voice | `parakeet-mlx` (Apple Silicon, ~3000× realtime) | `mlx-whisper`/`faster-whisper` (99-lang, `--lang hu`) → `whisper.cpp` |
| Image OCR | `ocrmac` (Apple Vision, no model download) | `tesseract` |
| Video/URL | `yt-dlp` captions-first (`--write-subs` → auto-subs, VTT→md) | audio download + ASR only when no captions |

`--diarize` (pyannote, gated HF token) and `--describe` (Ollama VLM) are explicit opt-in flags that
no-op with a clear message when absent. Gate audio tiers on `which ffmpeg`. **Effort: L.**

### 4.2 `ops files distill` — agent-compiled concept notes (Iron Law shape)
Reads a derived transcript/extract and produces 1–N interlinked concept notes in `wiki/notes/`. The
model returns a **typed JSON payload** ({title, summary, wikilinks[]}) — never file text; the verb
validates (unique slugs, resolvable links) and writes deterministically via notetype templates with
provenance frontmatter `author: agent`, `source: "[[…]]"`, `status: draft`. `ops triage` pages
agent-drafted notes as a promotion queue (accept → active, reject → delete, one commit each). With
`OPS_AGENT=none`: a deterministic heading-outline note. **Effort: M.**

### 4.3 Provenance as a checked convention (the poisoned-memory antidote)
Document three note planes in `wiki/conventions.md` — human note; derived note
(`derived_from`/`source_sha256`/`tool`); agent concept note (`author: agent` + draft gate) — and
teach doctor to flag violations. Index `author`/`derived_from` as filterable fields so
`ops search --author human` can exclude agent material. This is the #1 community-reported failure
mode (agent artifacts re-read as truth) closed deterministically, and it keeps the Obsidian graph a
representation of the user's own thoughts (kepano's clean-vs-messy separation). **Effort: S.**

### 4.4 `ops organize` — the self-organization loop (proposal queue, never direct edits)
The piece that turns `consolidate`'s nightly report into a compounding system, and the safety
architecture every future autonomous capability reuses.

- **Scan** (`draft_only`): zero-LLM candidate generation (lift consolidate's orphan/stale logic; FTS5
  title/alias overlap + LanceDB cosine for near-duplicates and link candidates; tag-case variants)
  → a typed proposal queue `inbox/organize/<date>.jsonl`, one op per line:
  `{id, op, target, payload, confidence, rationale, status}`. **Closed op catalog** (Mem0 lesson):
  `add_link · refresh_hub · normalize_tag · fix_frontmatter · retitle · flag_duplicate ·
  propose_merge`. The LLM (via `agent.py`, scope=read) only RANKS/LABELS; with `OPS_AGENT=none` the
  queue still emits with heuristic confidences. A hallucinating model can only mis-rank, never mutate.
- **Review** (`ops organize review`): triage-style paging showing the exact diff each op would
  produce; accept/reject/defer appended to the queue (never rewritten in place — audit-grade ledger).
- **Apply** (`confirm`): deterministic replay of APPROVED ops only — the model is not in the loop at
  apply time. Hard rails: **one git commit per op** (rationale in the message; any change is one
  `git revert`), per-run edit budget (~20 ops / ~300 lines), protected paths
  (conventions/index/hubs/pinned) review-only regardless of confidence; retitle/merge/deletion never
  auto-applies. Danger-split means safe primitives (add_link, additive hub refresh, tag/frontmatter
  repair) can eventually earn `--safe-only` auto-apply above a 0.8 threshold.
- **Schedule** the scan weekly via `jobs/registry.json` (next to the 02:30 consolidate); **apply is
  never schedulable** — enforced mechanically by its confirm class, plus a doctor check that warns if
  any confirm-class verb appears in the registry. Harden `agent.py` for headless runs: absolute
  binary path via `shutil.which`, `--max-turns` + timeout, failures surfaced to `.logs/jobs/`.
**Effort: M+M.**

---

## Part 5 — Durability & sharing

> The durability panel's ordering argument is right: **backup before share**. Sharing makes the
> system delightful; backup makes it trustworthy. `~/files` is the one root where loss is physically
> irreversible, and today its protection is a README paragraph.

### 5.1 The backup family (restic)
Keep bare `ops backup` as today's read-only nag (the agent-facing verb). Add:
- `ops backup init` — interactive, human-run once: local external-SSD restic repo + B2 bucket
  (Object Lock), keys as `op://` references, renders the launchd plist.
- `ops backup run [--target local|cloud]` — restic backup of `~/files`, `~/dotfiles`, and
  working-tree mirrors of `~/ops`/`~/work`, then `restic check`. Cloud target is confirm-class.
- **The scheduled cloud push runs from launchd invoking restic DIRECTLY with a dedicated
  append-only (no-delete/no-prune) B2 key — outside the agent/verb surface.** This resolves the
  never-transmit tension honestly: the human consents once (`init --yes`); thereafter it's machine
  infrastructure like Time Machine, and even a fully compromised laptop/agent can only ADD to
  history, never erase it — the guardrail concept pushed into the storage layer. Prune only manual,
  with a separate privileged key.
- `ops backup status` — snapshot age per target, exit 1 if stale >48h (feeds the nag).
- `ops backup drill` — monthly: restore latest snapshot (or random subset) to tmp, diff against
  source, fail loud. Quarterly: `restic check --read-data`. A backup that has never been restored is
  a hypothesis.
- `ops backup bundle` — rotated `git bundle --all` of `~/ops` + every `~/work` repo (including
  remote-less ones) into `~/files/backups/bundles/`, captured by restic — closes the
  "work repo with no upstream has exactly one copy in the world" hole.
Cost: ~$0.30–1.50/mo B2. Nightly run+check; weekly `--read-data-subset 10%` + forget/prune policy
(7d/4w/12m). **Effort: L (init UX is the meat), drill/bundle S.**

### 5.2 `ops share` — one Cloudflare Worker + KV, zero-knowledge, confirm-gated
`ops share <slug> [--expires 7d]` / `share collection <tag>` / `share list` / `share revoke <id>`.
Flow: render the note (or collection bundle) to ONE self-contained HTML blob **locally** (inline CSS,
wikilinks resolved only within the shared set, images inlined under a size cap) → encrypt with a
locally generated AES-256-GCM key → PUT **ciphertext only** to a vendored Cloudflare Worker + KV →
key travels in the URL fragment `#key` (PrivateBin pattern — the provider can never read the note) →
Worker returns `{id, admin_token}`. Expiry = KV `expirationTtl`, 1:1 from `--expires` (no cleanup
code); revoke = DELETE with the admin token. `--plain` mode (unguessable slug, no E2E) for
convenience.

Governance: risk `confirm` — publishing ciphertext off-machine IS a transmission; the guardrail's
transmit patterns catch the outbound PUT anyway, so the class is structurally enforced. The verb's
output is the link (a draft) — the human sends it. A committed `.share/ledger.json` + a `share:`
frontmatter block make every share auditable, and `ops sweep` warns on expired shares or notes edited
since sharing. Worker source vendored in `bin/share/worker/` (engine boundary → fixes distribute);
`ops share init` runs `wrangler deploy` once. Free tier: 100k req/day, 1k KV writes/day — collections
coalesce into ONE KV entry. Modeled on SharzyL/pastebin-worker, which proves the whole feature set.
Fallback for the unprovisioned: `--gist` (secret gist, unguessable-not-private, no TTL — throwaway
links only). **Effort: L.**

### 5.3 `ops publish` — a SEPARATE future verb (do not overload share)
Public evergreen digital-garden pages = Quartz 4 → Cloudflare/GitHub Pages, gated by
`publish: true` frontmatter. Share = private/expiring/revocable artifacts; publish = persistent
public site. Merging them forces the wrong defaults on both. **Effort: M; later.**

### 5.4 Install funnel
- `script/get` — one hardened, inspectable curl|sh bootstrap (rustup pattern: pinned TLS flags,
  published .sha256, `--dry-run`, refuse-don't-overwrite, no sudo). It only checks prereqs, clones to
  `~/ops`, and calls the existing idempotent `script/setup` — one setup code path.
- `--demo` — clone into a throwaway tmp dir seeded with example notes (reuse `OPS_ROOTS_HOME`) so
  capture/search/week work in 60 seconds; delete one directory to walk away. Optionally a committed
  `.devcontainer` + Codespaces quickstart badge for browser try-out.
- Homebrew: **only ever a tiny bootstrapper** (chezmoi model). Never a formula that clones vault
  content into a brew-owned prefix — the exact opposite of a user-owned repo.
- First-run wizard stays ≤5 skippable prompts with safe defaults (vectors OFF, jobs OFF); defer
  optional capabilities to just-in-time nudges.
- Windows = WSL2, documented, no native PowerShell attempt.
**Effort: M.**

---

## The anti-roadmap (consolidated warnings — as load-bearing as the roadmap)

1. **No resident daemon / local HTTP server.** Fork/exec suffices; a daemon accumulates
   unrebuildable state. Only ever an opt-in warm-embedding cache after measured pain.
2. **No frontend or MCP layer may import verb/lib code to "save a subprocess."** Everything re-enters
   through `ops <verb>` or the guardrail stops being the single enforcement path.
3. **Plugin manifests are claims, not permissions.** Guardrail stays authoritative; confirm-ceiling
   until explicit human trust; no auto-update across pins; no central registry/store.
4. **One JSON envelope, one version, one contract test.** Per-verb schema drift silently breaks every
   consumer (the jc lesson).
5. **Never remove/rename existing verb spellings** — add unified verbs and delegate.
6. **No model ever emits file text or diffs directly** in organization flows — closed typed-op
   catalog only; scheduled = propose, interactive = apply; never schedule a write-scoped agent call.
7. **Heavy models never become hard deps or defaults** — the stdlib-only zero-install path is the
   core promise.
8. **Derived/extracted markdown never lands in `~/files`; extracted text never folds into the shadow
   note** — planes stay separate so derivation can't masquerade as source.
9. **Never sync any `.git` via iCloud/Dropbox/Syncthing** (Syncthing's own maintainers' warning);
   don't soften the doctor check.
10. **Don't overload `ops share` with public publishing**; don't let backup auto-push or auto-commit
    "while it's at it" — the read-only nag is a feature.
11. **No git-lfs/git-annex for `~/files`; no truth ever moves into restic/SQLite** (Taskwarrior 3's
    regression storm is the cautionary tale).
12. **Obsidian URIs open, never write; never own `.obsidian/` in engine.txt; never auto-rewrite notes
    to fight Obsidian's normalizer** — tolerate on read, normalize at index time.

---

## Suggested build order

| Wave | Items | Rationale |
|---|---|---|
| 1 — Trust | 0.1 update-merge · 0.3 exit codes · 0.4 doctor walls · 5.1 backup family | Fixes silent data loss; makes the system trustworthy before delightful |
| 2 — Contract | 1.1 `--json` · 1.2 ops.json v2 · 0.5 dry-run | The keystone everything else consumes |
| 3 — Platform | 2.1 multi-root resolver (+0.2 retarget) · 2.3 api.py · 2.2 `ops plugin` · 2.4 `ops mcp` | ops becomes extendable + natively agent-drivable |
| 4 — Surfaces | 3.1 Obsidian zero · 3.3 Raycast pack · 3.4 open/orient/search-session · 3.2 Bases/Canvas | Rent Obsidian, build Raycast, polish terminal |
| 5 — Pipeline | 4.1 extract · 4.3 provenance · 4.2 distill · 4.4 organize | Artifacts → linked knowledge; the compounding loop |
| 6 — Reach | 5.2 share · 5.4 install funnel · 3.4 mobile doc · 5.3 publish (later) · 3.5 TUI (later) | Sharing, onboarding, everything-else |

---

## Key sources (verified by the research fleet)

nb (xwmx/nb) · zk (zk-org/zk) · Denote · basic-memory (basicmachines-co) · khoj · Quartz 4 ·
SwarmVault · Karpathy's llm-wiki gist · gbrain · kepano/obsidian-skills · JSON Canvas
(jsoncanvas.org) · Obsidian Bases · Advanced URI · Smart Connections · krew · gh extensions ·
Obsidian plugin manifest model · antidote · Raycast extensions · clig.dev · jc · Tailscale/Syncthing
daemon patterns · Textual · glow · SharzyL/pastebin-worker · PrivateBin · Cloudflare Workers KV ·
restic · Kopia · GitJournal · Working Copy · rclone-vs-backup distinction · parakeet-mlx ·
mlx-whisper/faster-whisper/whisper.cpp · pymupdf4llm · docling · ocrmac · WhisperX · yt-dlp ·
Mem0 · Letta sleep-time agents · Reor · Obsidian AutoMOC · Khoj Automations · chezmoi · copier ·
cruft · rustup · uv (PEP 723) · Taskwarrior 3 (#3329, cautionary) · Dendron postmortem (cautionary).
