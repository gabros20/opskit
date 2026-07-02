# Architecture — why ops is shaped the way it is

**Explanation.** The reasoning behind the system: the problem, the principles, the enforcement path,
and the trade-offs each layer accepted. For *how to do things*, see the
[operating manual](../skills/operate-ops/SKILL.md); for exact shapes, the
[machine contract](machine-contract.md); for the history of each decision, the
[ADR log](DECISIONS.md).

---

## The problem, and the bet

Personal knowledge tools die two deaths: **lock-in** (your notes live in someone's database, app, or
sync service, and leave when it does) and **entropy** (a folder of files with no system decays into a
junk drawer). ops bets that both are solved by the same move: make **plaintext Markdown in one git
repo** the only source of truth, and put **one command surface** in front of it that knows where
everything goes.

Six principles fall out of that bet, and every later decision traces back to one of them:

1. **Plaintext is the truth.** Anything else — SQLite, LanceDB, `ops.json`, extracts — is a
   disposable cache, rebuildable with `rm -rf .index && ops index`.
2. **Git is the spine.** Every change is a revertible diff; history is the undo button and the audit
   log. (This holds at scale: 500k text notes ≈ 2.5 GB of well-compressed text — see ADR-006.)
3. **One door.** `ops <verb>` is the only way anything mutates the vault. The verb owns *where* and
   *how*; the caller supplies content and judgment (the "Iron Law").
4. **Agent-agnostic.** A model decides *what*; the system guarantees *where/how*. Any agent that can
   read a file and run a command can drive ops — through the same door, behind the same wall.
5. **Nothing transmits without a human.** Drafts, nags, and confirm-gates instead of sends.
6. **Reversible, zero-install, no server.** The stdlib-only path always works; heavy deps are
   optional and auto-detected; there is no daemon, no HTTP server, no resident state — ever.

## The shape: four roots, one repo of truth

```
~/ops        THE SYSTEM   knowledge (wiki/), tasks/, journal/, the verbs (bin/), plugins/   [git: your repo]
~/work       CODE         one git repo per project: products/ labs/ tools/ clients/         [git: each its own]
~/files      BINARIES     client docs, PDFs, datasets — referenced by wiki "shadow notes"   [restic, not git]
~/dotfiles   THE MACHINE  installs tools, puts ops on PATH                                  [git: separate]
```

Separation **by location** is what makes the rest enforceable: the guardrail's path-wall is rooted in
this layout (writes outside the roots are refused; iCloud/family paths are walled off), and git stays
fast because binaries structurally never enter the knowledge repo — the failure mode that killed
comparable git-wiki systems (their repos bloated with embedded media, not with text).

## The single enforcement path

Every caller — human, cron job, Raycast script, Obsidian URI, MCP host, plugin, agent — converges on
one chokepoint:

```
 terminal ─┐
 Raycast  ─┤
 launchd  ─┼──▶  ops <verb> [--json]  ──▶  guardrail.gate()  ──▶  bin|plugins/<verb>/run.py  ──▶  git diff
 ops mcp  ─┤         (dispatcher)           risk class,             writes only via verbs        (revertible)
 plugins  ─┘                                --yes, dry-run,
                                            path-wall, logs
```

Two rules keep the chokepoint honest, and they are the two most load-bearing lines in the codebase:

- **Nothing imports around it.** Frontends and the MCP server never import verb code "to save a
  subprocess" — every call re-enters through `ops <verb>`, so the guardrail and `.logs/` see
  everything. (The MCP server is a stateless stdio child spawned per session precisely so there is no
  second, resident door.)
- **Refusals teach.** The exit-code protocol (`3` = needs `--yes` with the exact re-run, `4` = not
  found with a did-you-mean, `5` = denied) means a blocked caller learns the correct next call from
  the error itself. For an agent, error messages *are* the feedback loop.

The classes themselves (`read` / `safe_write` / `draft_only` / `confirm` / `deny`) encode one idea:
**the blast radius of a mistake, not the intent of the caller**. A `--dry-run` is a read (so anything
is explorable); an undeclared verb is `confirm` (so forgetting to classify fails safe); an untrusted
plugin is capped at `confirm` regardless of what it claims (so a manifest is a claim, not a grant).

## The machine contract: agents as first-class operators

v4's central addition. Instead of "the agent reads the manual and hopes," the surface is
self-describing: every verb speaks one frozen `--json` envelope, and the generated `ops.json` v2
carries the whole surface — args, output schemas, risk classes, usage hints, detected capabilities.
The consequences compound:

- `ops mcp` is ~zero marginal surface: its tool list is *generated* from `ops.json`, so every new
  verb and every installed plugin becomes an MCP tool automatically.
- A contract test round-trips every verb against its declared schema, so drift breaks CI, not
  consumers (the lesson of every ad-hoc `--json` flag that quietly changed shape).
- Discipline over features: the envelope changes only with a version bump. An unstable machine
  schema is worse than none.

## Extension without erosion

The extension mechanism was designed backwards from two failure modes: user code overwritten by
updates, and third-party code silently escalating. Hence:

- **Multi-root resolution** (`bin/` → `plugins/` → `$OPS_PATH`) with `bin/` reserved: engine updates
  can never collide with user verbs, and user verbs can never shadow engine ones.
- **A frozen SDK** (`lib/api.py`, `OPS_API_VERSION`) instead of "import whatever": the blessed subset
  includes `classify` — the seam that makes a plugin inherit the path-wall rather than skip it.
- **A trust ceiling** instead of install-time permissions: declared risks activate only after an
  explicit `ops plugin trust`, updates re-pin explicitly, and there is no registry to compromise —
  the git repo is the plugin. See [plugins.md](plugins.md).

## Frontends: rent before build

The vault is plaintext, so the richest frontends are ones ops doesn't have to write. **Obsidian is
"Frontend Zero"** — read/edit/graph/mobile for the cost of a config pack — under a strict treaty:
URIs *open*, verbs *write*, and ops tolerates Obsidian's frontmatter normalization on read rather
than rewriting user files to fight it. Plaintext view formats (Bases, JSON Canvas) let ops *generate*
what Obsidian *renders* — no server, no plugin API dependency. The first **built** tier is
deliberately thin (Raycast script commands that shell to `ops`), proving the `--json` surface before
anything heavier earns its keep. Mobile is documentation, not an app: git is the only sync transport.

## The knowledge pipeline: provenance as the safety mechanism

Turning artifacts into knowledge involves models, and models hallucinate. The pipeline's design rule:
**a model may propose, rank, or label — it may never directly produce bytes that land in the vault.**

- `files extract` is deterministic tooling (tiered local extractors); its output is a *derived* note
  carrying `derived_from` + `source_sha256` + `tool` — extraction never masquerades as source truth.
- `files distill` accepts only a typed JSON payload from the model; the verb validates and writes
  through templates, and the result is `author: agent, status: draft` until a human promotes it.
- `organize` runs a closed op catalog (seven op types; anything else is rejected at write *and* read
  time), a propose → review → apply ledger, one git commit per applied op, edit budgets, and
  protected paths. The scan is schedulable; apply never is.

Three note planes — human, derived, agent — are a *checked* convention (`doctor` flags violations;
`ops search --author human` filters), because the #1 reported failure mode of agent-adjacent PKM is
agent output being re-read as human truth.

## Retrieval: staged, local, disposable

Keyword+graph (FTS5 + wikilinks) is the always-on floor; local vectors (EmbeddingGemma + LanceDB) and
a cross-encoder reranker are opt-in stages that measurably earn their place (ADR-002: vectors
recovered exactly the queries keyword structurally cannot). Everything is embedded, file-based, and
rebuildable — the retrieval add-on test: *file-based + locally computed + rebuilt from plaintext =
allowed; a server or a second stale graph = rejected* (ADR-003/006).

## Durability: the guardrail pushed into the storage layer

Backup precedes sharing because `~/files` is the one root where loss is irreversible. The design's
sharpest trick: the scheduled cloud push runs from launchd invoking restic **directly with an
append-only key** — outside the verb surface entirely. The human consents once at `init`; thereafter
even a fully compromised agent (or laptop) can only *add* to backup history, never erase it.
`ops share` applies the same zero-trust posture to sharing: encrypt locally, publish ciphertext to
your own worker, key in the URL fragment — the provider can never read the note, and the verb's
output is a *draft link* the human sends. See [backup-and-share.md](backup-and-share.md).

## What ops deliberately refuses to become

As load-bearing as the features (the full list lives in the
[v4 proposal's anti-roadmap](design/proposals/2026-07-01-v4-platform-roadmap.md#the-anti-roadmap)):

no daemon or local HTTP server · no frontend importing lib to skip the dispatcher · no install-time
plugin permissions or auto-updates · no second machine schema · no removed verb spellings · no model
ever emitting file text in organization flows · no heavy hard deps · no truth in SQLite/restic ·
no `.git` over iCloud/Dropbox/Syncthing · no public publishing bolted onto `share`.

Each "no" is a scar from a system that tried it — Taskwarrior 3's SQLite-as-truth regressions,
Dendron's host lock-in, gbrain's binary-bloated git wiki. The refusals are what keep the six
principles true as the surface grows.
