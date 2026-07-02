# Plugins — add your own verbs without forking the engine

**How-to + reference.** For anyone who wants a verb `ops` doesn't ship — from a private one-off to a
distributable pack. Engine contributors adding *core* verbs should read [`CONTRIBUTING.md`](../CONTRIBUTING.md)
instead.

The one-paragraph model: a plugin verb is **the exact same shape as an engine verb** — a folder with
`run.py` + `cmd.json` — resolved from `plugins/` instead of `bin/`. `bin/` is reserved (engine always
wins; a plugin can never shadow a core verb); `plugins/` is yours (never touched by `script/update`,
version-controlled inside your vault). Resolution order: `bin/` → `plugins/<pack>/<verb>/` →
colon-separated `$OPS_PATH`. Because plugins land in the same manifest, they appear in `ops help`,
`ops.json`, tab-completion, and the MCP tool list with zero extra wiring — and the guardrail gates
them exactly like core verbs.

---

## Write a local verb (2 minutes)

```sh
ops new verb standup          # scaffolds plugins/local/standup/{run.py,cmd.json}
$EDITOR plugins/local/standup/run.py
ops standup                   # it's live — help/completion/ops.json pick it up automatically
```

The scaffold gives you the argument parsing, `--json` emission, and a `cmd.json` that defaults to
the safest risk class. Fill in `summary`, `usage`, `risk`, `reads`/`writes`, `output`, `hints` —
see the [machine contract](machine-contract.md) for what each field means.

## Import only the SDK

A plugin imports **one** module: `lib.api` (frozen, `OPS_API_VERSION = "1.0"`). Everything else in
`bin/lib/` is private and may change without notice.

| Export | What it's for |
|---|---|
| `OPS_HOME`, `WIKI`, `INBOX` | the filesystem roots |
| `append_journal(line)` | the shared activity record — call it after any meaningful action |
| `slugify`, `today`, `fm_field`, `link_targets` | slugs, dates, frontmatter reads, wikilink extraction |
| `classify(action, path…)` | **the Iron Law seam** — gives your verb the same path-wall + transmit-block a core verb has; call it before any write you compute yourself |
| `load_types`, `type_dir`, `is_type`, `render_note` | the data-driven note types (so your notes match the vault's conventions) |
| `run_agent(prompt, scope=…)` | borrow the configured model with a deterministic fallback when `OPS_AGENT=none` |
| `emit`, `emit_rows`, `fail` | the `--json` envelope + exit-code protocol |

`test/run_plugin.py` snapshots every exported signature — the API cannot drift silently under you.

## Package a pack (distributable)

A pack is a git repo (or directory) of verb folders plus a manifest:

```
ops-greeter/
├── plugin.json
└── hello/
    ├── run.py
    └── cmd.json
```

`plugin.json` schema:

```json
{
  "name": "greeter",
  "version": "0.1.0",
  "min_ops_version": "4.0.0",
  "api": ">=1,<2",
  "verbs": [
    { "verb": "hello", "risk": "safe_write", "reads": ["wiki"], "writes": ["wiki/notes"],
      "summary": "write a greeting note" }
  ]
}
```

`ops plugin add` validates this against the schema, refuses a pack whose `api` range doesn't cover
the installed `OPS_API_VERSION`, and refuses any verb name that collides with an engine verb.

## Install, trust, update, remove

```sh
ops plugin add you/ops-greeter@v0.1.0 --yes   # shallow-clone into plugins/greeter/ (a local path works too)
ops plugin list                               # name · version · pinned commit · trust state · verbs
ops plugin trust greeter --yes                # lift the ceiling to the pack's declared risks
ops plugin update greeter --yes               # explicit re-pin; refuses to cross min_ops_version
ops plugin remove greeter --yes               # delete dir + lock entry
```

Every install/trust decision is recorded in the committed `plugins/plugins.lock.json` (resolved
commit sha + accepted risk ceiling), so your vault's plugin state is reproducible and auditable.

## The trust model (read this before installing anything)

- **A manifest is a claim, not a permission.** A pack's self-declared risk classes never take effect
  at install. Until you run `ops plugin trust`, the guardrail caps *every* verb from that pack at
  `confirm` — including `--dry-run` calls (the one place dry-run does **not** downgrade, so an
  untrusted pack can't use it as a probe).
- **Trust lifts the ceiling to the declared classes — not above them.** Even a trusted plugin keeps
  the transmit-block and the path-wall; `deny`-class actions stay denied for everyone.
- **Nothing auto-updates.** `update` is explicit and re-pins; there is no central registry — the git
  repo *is* the plugin, and trust is per-owner (audit before you trust, like any code you run).

## Gotchas

- Don't put a verb in `bin/` — `script/update` owns that path and will merge upstream over it. That
  is exactly what `plugins/local/` exists for (`ops new verb` refuses to scaffold into `bin/`).
- Re-enter, never import: if your verb needs another verb, shell out to `ops <verb> --json` — do not
  import its code (the guardrail must see every call).
- Declare `output` and `hints` — they're what agents (and the MCP tool list) see; a verb without them
  is invisible to half the ecosystem.
- One pack name = one directory under `plugins/`; the resolver reads `plugins/<pack>/<verb>/`, so
  nesting deeper won't resolve.
