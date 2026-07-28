# Plugins — add your own verbs without forking the engine

This doc shows how to add a verb `plainkeep` doesn't ship, from a private one-off to a distributable pack. It's for anyone writing their own verbs or installing packs.

Adding a *core* verb to the engine instead? Read [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## How it works, in one paragraph

A plugin verb has the exact same shape as an engine verb: a folder with `run.py` + `cmd.json`.

The only difference is where it lives. Core verbs resolve from `bin/`; plugin verbs resolve from `plugins/`.

- `bin/` is reserved. The engine always wins, so a plugin can never shadow a core verb.
- `plugins/` is yours. `script/update` never touches it, and it's version-controlled inside your vault.

Resolution order:

```
bin/  →  plugins/<pack>/<verb>/  →  $PLAINKEEP_PATH  (colon-separated)
```

Plugins land in the same manifest as core verbs. So they show up in `plainkeep help`, `plainkeep.json`, tab-completion, the `plainkeep ui` terminal UI, and the MCP tool list with zero extra wiring. The guardrail gates them exactly like core verbs.

---

## How-to

### Write a local verb (2 minutes)

```sh
plainkeep new verb standup          # scaffolds plugins/local/standup/{run.py,cmd.json}
$EDITOR plugins/local/standup/run.py
plainkeep standup                   # it's live — help/completion/plainkeep.json pick it up automatically
```

The scaffold gives you argument parsing, `--json` emission, and a `cmd.json` that defaults to the safest risk class.

Fill in `summary`, `usage`, `risk`, `reads`/`writes`, `output`, and `hints`. See the [machine contract](machine-contract.md) for what each field means.

### Import only the SDK

A plugin imports **one** module: `lib.api`. It's frozen at `PLAINKEEP_API_VERSION = "1.0"`.

Everything else in `bin/lib/` is private and may change without notice.

`test/run_plugin.py` snapshots every exported signature, so the API can't drift silently under you.

The [reference tables](#reference) below list every export and every command.

### Package a pack (distributable)

A pack is a git repo (or directory) of verb folders plus a manifest:

```
plainkeep-greeter/
├── plugin.json
└── hello/
    ├── run.py
    └── cmd.json
```

Its `plugin.json`:

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

`plainkeep plugin add` validates this against the schema. It refuses a pack whose `api` range doesn't cover the installed `PLAINKEEP_API_VERSION`, and it refuses any verb name that collides with an engine verb.

### Install, trust, update, remove

```sh
plainkeep plugin add you/plainkeep-greeter@v0.1.0 --yes   # shallow-clone into plugins/greeter/ (a local path works too)
plainkeep plugin list                               # name · version · pinned commit · trust state · verbs
plainkeep plugin trust greeter --yes                # lift the ceiling to the pack's declared risks
plainkeep plugin update greeter --yes               # explicit re-pin; refuses to cross min_ops_version
plainkeep plugin remove greeter --yes               # delete dir + lock entry
```

Every install and trust decision is recorded in the committed `plugins/plugins.lock.json` (resolved commit sha + accepted risk ceiling). Your vault's plugin state stays reproducible and auditable.

---

## The trust model

Read this before installing anything.

- **A manifest is a claim, not a permission.** A pack's self-declared risk classes never take effect at install. Until you run `plainkeep plugin trust`, the guardrail caps *every* verb from that pack at `confirm`. That includes `--dry-run` calls: this is the one place dry-run does **not** downgrade, so an untrusted pack can't use it as a probe.
- **Trust lifts the ceiling to the declared classes, not above them.** A trusted plugin still keeps the transmit-block and the path-wall. `deny`-class actions stay denied for everyone.
- **Nothing auto-updates.** `update` is explicit and re-pins. There's no central registry: the git repo *is* the plugin, and trust is per-owner. Audit before you trust, like any code you run.

---

## Reference

### SDK exports (`lib.api`)

| Export | What it's for |
|---|---|
| `PLAINKEEP_HOME`, `WIKI`, `INBOX` | the filesystem roots |
| `append_journal(line)` | the shared activity record — call it after any meaningful action |
| `slugify`, `today`, `fm_field`, `link_targets` | slugs, dates, frontmatter reads, wikilink extraction |
| `classify(action, path…)` | the Iron Law seam — gives your verb the same path-wall + transmit-block a core verb has; call it before any write you compute yourself |
| `load_types`, `type_dir`, `is_type`, `render_note` | the data-driven note types, so your notes match the vault's conventions |
| `run_agent(prompt, scope=…)` | borrow the configured model, with a deterministic fallback when `PLAINKEEP_AGENT=none` |
| `emit`, `emit_rows`, `fail` | the `--json` envelope + exit-code protocol |

### Plugin commands

| Command | What it does |
|---|---|
| `plainkeep new verb <name>` | scaffold `plugins/local/<name>/{run.py,cmd.json}` |
| `plainkeep plugin add <owner/repo>[@tag] --yes` | shallow-clone into `plugins/<pack>/` (a local path works too) |
| `plainkeep plugin list` | show name · version · pinned commit · trust state · verbs |
| `plainkeep plugin trust <name> --yes` | lift the ceiling to the pack's declared risks |
| `plainkeep plugin update <name> --yes` | explicit re-pin; refuses to cross `min_ops_version` |
| `plainkeep plugin remove <name> --yes` | delete the dir + lock entry |

---

## Gotchas

- **Don't put a verb in `bin/`.** `script/update` owns that path and will merge upstream over it. That's exactly what `plugins/local/` is for, and `plainkeep new verb` refuses to scaffold into `bin/`.
- **Re-enter, never import.** If your verb needs another verb, shell out to `plainkeep <verb> --json`. Don't import its code — the guardrail must see every call.
- **Declare `output` and `hints`.** They're what agents and the MCP tool list see. A verb without them is invisible to half the ecosystem.
- **One pack name = one directory** under `plugins/`. The resolver reads `plugins/<pack>/<verb>/`, so nesting deeper won't resolve.
