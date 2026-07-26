# Architecture — why ops is shaped the way it is

This doc explains the reasoning behind ops: the problem it solves, the principles it commits to, how
those principles are enforced, and what each layer traded away. It is for anyone extending ops or
deciding whether its shape fits their own tools.

For *how to do things*, see the [operating manual](../skills/operate-ops/SKILL.md). For exact shapes,
see the [machine contract](machine-contract.md). For the history of each decision, see the
[ADR log](DECISIONS.md).

---

## The problem, and the bet

Personal knowledge tools die two deaths.

- **Lock-in.** Your notes live in someone's database, app, or sync service, and they leave when it
  does.
- **Entropy.** A folder of files with no system decays into a junk drawer.

ops bets that both are solved by the same move. Make **plaintext Markdown in one git repo** the only
source of truth. Then put **one command surface** in front of it that knows where everything goes.

Six principles fall out of that bet. Every later decision traces back to one of them.

1. **Plaintext is the truth.** Anything else is a disposable cache: SQLite, LanceDB, `ops.json`,
   extracts. All of it is rebuildable with `rm -rf .index && ops index`.
2. **Git is the spine.** Every change is a revertible diff. History is the undo button and the audit
   log. This holds at scale: 500k text notes is about 2.5 GB of well-compressed text (ADR-006).
3. **One door.** `ops <verb>` is the only way anything mutates the vault. The verb owns *where* and
   *how*; the caller supplies content and judgment. This is the "Iron Law".
4. **Agent-agnostic.** A model decides *what*; the system guarantees *where* and *how*. Any agent that
   can read a file and run a command can drive ops, through the same door, behind the same wall.
5. **Nothing transmits without a human.** Drafts, nags, and confirm-gates instead of sends.
6. **Reversible, zero-install, no server.** The stdlib-only path always works. Heavy deps are optional
   and auto-detected. There is no daemon, no HTTP server, and no resident state, ever.

## The shape: four roots, one repo of truth

```
~/ops        THE SYSTEM   knowledge (wiki/), tasks/, journal/, the verbs (bin/), plugins/   [git: your repo]
~/work       CODE         one git repo per project: products/ labs/ tools/ clients/         [git: each its own]
~/files      BINARIES     client docs, PDFs, datasets — referenced by wiki "shadow notes"   [restic, not git]
~/dotfiles   THE MACHINE  installs tools, puts ops on PATH                                  [git: separate]
```

Separation **by location** is what makes the rest enforceable.

The guardrail's path-wall is rooted in this layout. Writes outside the roots are refused, and
iCloud and family paths are walled off.

Git stays fast because binaries structurally never enter the knowledge repo. That was the failure
mode that killed comparable git-wiki systems: their repos bloated with embedded media, not with text.

## The single enforcement path

Every caller converges on one chokepoint: human, cron job, Raycast script, Obsidian URI, MCP host,
plugin, agent.

```
 terminal ─┐
 Raycast  ─┤
 launchd  ─┼──▶  ops <verb> [--json]  ──▶  guardrail.gate()  ──▶  bin|plugins/<verb>/run.py  ──▶  git diff
 ops mcp  ─┤         (dispatcher)           risk class,             writes only via verbs        (revertible)
 plugins  ─┘                                --yes, dry-run,
                                            path-wall, logs
```

Two rules keep the chokepoint honest. They are the two most load-bearing lines in the codebase.

- **Nothing imports around it.** Frontends and the MCP server never import verb code "to save a
  subprocess". Every call re-enters through `ops <verb>`, so the guardrail and `.logs/` see
  everything. The MCP server is a stateless stdio child spawned per session, precisely so there is no
  second, resident door.
- **Refusals teach.** The exit-code protocol tells a blocked caller its correct next call from the
  error itself: `3` needs `--yes` with the exact re-run, `4` is not-found with a did-you-mean, `5` is
  denied. For an agent, error messages *are* the feedback loop.

The risk classes are `read`, `safe_write`, `draft_only`, `confirm`, and `deny`. They encode one idea:
**the blast radius of a mistake, not the intent of the caller.**

- A `--dry-run` is a `read`, so anything is explorable.
- An undeclared verb is `confirm`, so forgetting to classify fails safe.
- An untrusted plugin is capped at `confirm` regardless of what it claims, so a manifest is a claim,
  not a grant.

## The machine contract: agents as first-class operators

This is v4's central addition. Instead of "the agent reads the manual and hopes," the surface is
self-describing.

Every verb speaks one frozen `--json` envelope. The generated `ops.json` v2 carries the whole surface:
args, output schemas, risk classes, usage hints, and detected capabilities.

The consequences compound.

- `ops mcp` is near-zero marginal surface. Its tool list is *generated* from `ops.json`, so every new
  verb and every installed plugin becomes an MCP tool automatically.
- A contract test round-trips every verb against its declared schema, so drift breaks CI, not
  consumers. That is the lesson of every ad-hoc `--json` flag that quietly changed shape.
- Discipline over features: the envelope changes only with a version bump. An unstable machine schema
  is worse than none.

## Extension without erosion

The extension mechanism was designed backwards from two failure modes: user code overwritten by
updates, and third-party code silently escalating.

- **Multi-root resolution** (`bin/` → `plugins/` → `$OPS_PATH`) with `bin/` reserved. Engine updates
  can never collide with user verbs, and user verbs can never shadow engine ones.
- **A frozen SDK** (`lib/api.py`, `OPS_API_VERSION`) instead of "import whatever". The blessed subset
  includes `classify`, the seam that makes a plugin inherit the path-wall rather than skip it.
- **A trust ceiling** instead of install-time permissions. Declared risks activate only after an
  explicit `ops plugin trust`, updates re-pin explicitly, and there is no registry to compromise: the
  git repo is the plugin. See [plugins.md](plugins.md).

## Frontends: rent before build

The vault is plaintext, so the richest frontends are ones ops doesn't have to write.

**Obsidian is "Frontend Zero"**: read, edit, graph, and mobile for the cost of a config pack. It runs
under a strict treaty. URIs *open*, verbs *write*, and ops tolerates Obsidian's frontmatter
normalization on read rather than rewriting user files to fight it. Plaintext view formats such as
Bases and JSON Canvas let ops *generate* what Obsidian *renders*, with no server and no plugin API
dependency.

The first **built** tier is deliberately thin: Raycast script commands that shell to `ops`. It proves
the `--json` surface before anything heavier earns its keep. Mobile is documentation, not an app,
because git is the only sync transport.

The second built tier is **`ops ui`**, the human terminal UI (ADR-011). See
[terminal-ui.md](terminal-ui.md) for how to use it.

Its TypeScript source lives in this template's `ui/` directory, but a vault never sees that source.
`ui/` is not in `script/engine.txt`. What `ops setup ui --yes` installs is a **self-contained
compiled binary**: built with Bun, shipped on the template repo's GitHub releases, sha256-verified,
and placed in `$OPS_HOME/.local/bin/` where the tiny stdlib `bin/ui/` shim looks first.

`ops ui` is the human *face* of the same one door. It reads `ops.json` (the `actions[]` grammar) to
generate menus and forms, so nothing has to be memorized. Every action it takes re-enters
`ops <verb> --json` as a subprocess, so the guardrail and `.logs/` see it exactly as they see an
agent.

Two faces, one door: humans drive `ops ui`, agents drive `ops <verb> --flags`. The enriched
`ops.json/3` contract (grammar single-sourced, completion derived from it) is what makes the generated
human UI possible without a second copy of the surface.

The compiled-binary distribution keeps the engine's stdlib-only floor intact. No Node, Bun, or
`node_modules` ever enters a vault.

## The knowledge pipeline: provenance as the safety mechanism

Turning artifacts into knowledge involves models, and models hallucinate. The pipeline's design rule:
**a model may propose, rank, or label. It may never directly produce bytes that land in the vault.**

- `files extract` is deterministic tooling (tiered local extractors). Its output is a *derived* note
  carrying `derived_from`, `source_sha256`, and `tool`, so extraction never masquerades as source
  truth.
- `files distill` accepts only a typed JSON payload from the model. The verb validates and writes
  through templates, and the result stays `author: agent, status: draft` until a human promotes it.
- `organize` runs a closed op catalog: seven op types, and anything else is rejected at write *and*
  read time. It uses a propose → review → apply ledger, one git commit per applied op, edit budgets,
  and protected paths. The scan is schedulable; apply never is.

Three note planes (human, derived, agent) are a *checked* convention. `doctor` flags violations and
`ops search --author human` filters. This exists because the number-one reported failure mode of
agent-adjacent PKM is agent output being re-read as human truth.

## Retrieval: staged, local, disposable

Keyword and graph search (FTS5 plus wikilinks) is the always-on floor.

Local vectors (EmbeddingGemma plus LanceDB) and a cross-encoder reranker are opt-in stages that must
measurably earn their place. Per ADR-002, vectors recovered exactly the queries keyword search
structurally cannot.

Everything is embedded, file-based, and rebuildable. That is the retrieval add-on test: file-based
plus locally computed plus rebuilt from plaintext is allowed; a server or a second stale graph is
rejected (ADR-003 and ADR-006).

## Durability: the guardrail pushed into the storage layer

Backup precedes sharing because `~/files` is the one root where loss is irreversible.

The design's sharpest trick: the scheduled cloud push runs from launchd, invoking restic **directly
with an append-only key**, outside the verb surface entirely. The human consents once at `init`.
Thereafter even a fully compromised agent or laptop can only *add* to backup history, never erase it.

`ops share` keeps the same consent discipline for sharing. It publishes to your own worker under a
long, unguessable capability URL, where secrecy is the link plus a TTL. ADR-008 traded zero-knowledge
for a link any agent can fetch: HTML in a browser, raw markdown at `<url>.md`. The verb's output is a
*draft link* the human sends. See [backup-and-share.md](backup-and-share.md).

## What ops deliberately refuses to become

The refusals are as load-bearing as the features. The full list lives in the
[v4 proposal's anti-roadmap](design/proposals/2026-07-01-v4-platform-roadmap.md#the-anti-roadmap):

- No daemon or local HTTP server.
- No frontend importing lib to skip the dispatcher.
- No install-time plugin permissions or auto-updates.
- No second machine schema.
- No removed verb spellings.
- No model ever emitting file text in organization flows.
- No heavy hard deps.
- No truth in SQLite or restic.
- No `.git` over iCloud, Dropbox, or Syncthing.
- No public publishing bolted onto `share`.

Each "no" is a scar from a system that tried it: Taskwarrior 3's SQLite-as-truth regressions,
Dendron's host lock-in, gbrain's binary-bloated git wiki. The refusals are what keep the six
principles true as the surface grows.
