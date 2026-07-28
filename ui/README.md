# ui/ — the plainkeep terminal UI (`plainkeep ui`)

**The human face of [`plainkeep`](https://github.com/gabros20/plainkeep).** A guided, menu-driven UI
over the `plainkeep.json/3` contract — you point-and-pick instead of memorizing flags. Agents keep
using `plainkeep <verb> --json`; humans get this. **Two faces, one door.**

```
┌ plainkeep  the guided terminal UI — humans point-and-pick, agents use plainkeep <verb> --json
│
◇  What do you want to do? (type to filter)
│  ＋ Capture a thought
│  ● orient    where was I — journal, tasks, inbox, health
│  ● capture   a thought → inbox
│  ● search    ranked note hits
│  ● task      list / add / done
│  …
```

## How it ships (ADR-011)

This directory is **template-only source** — it is *not* in `script/engine.txt`, so `script/update`
never copies it into a vault. What a vault installs is a **self-contained compiled binary**:

- `.github/workflows/release-ui.yml` cross-compiles this source with `bun build --compile` for
  darwin-arm64/x64 and linux-x64/arm64 and attaches the binaries + `checksums.txt` to a GitHub
  release (tag `ui-v*`).
- In a vault, `plainkeep setup ui --yes` downloads the matching asset with the **authenticated `gh`
  CLI** (the template repo may be private), verifies its sha256, and installs it to
  `$PLAINKEEP_HOME/.local/bin/plainkeep-ui` — exactly where the stdlib `bin/ui/` shim looks first.
- No Node, Bun, or `node_modules` ever enters a vault. The engine's zero-dependency floor holds.

## How it works

plainkeep-ui **never hardcodes menus or flags**. It runs `plainkeep help --json` to read the contract
and *generates* itself:

- the verb palette comes from the manifest's groups;
- each verb's form is built from its `actions[]` + typed `args` (enum → select, completion providers →
  pickers, everything else → text);
- `confirm`-class actions run first *without* `--yes`; the verb self-gates (exit 3) and plainkeep-ui
  renders the refusal + offers the exact re-run — it never pre-appends `--yes`;
- `dry_run` actions offer a **Preview** (a dry-run is a read, no `--yes` needed);
- `tty` verbs (`wiki edit` → `$EDITOR`, `backup init`) hand off the real terminal.

Every action re-enters `plainkeep <verb> --json` as a subprocess, so the guardrail and `.logs/` see
it exactly as they see an agent. plainkeep-ui imports no `plainkeep` internals.

## Develop (contributor checkout)

Requires Bun (or Node ≥ 20 with npm) and a `plainkeep` vault (schema `plainkeep.json/3`+).

```sh
cd ui
bun install
PLAINKEEP_BIN=/path/to/plainkeep/plainkeep bun run dev      # run the TUI against a vault

bunx tsc --noEmit                          # typecheck
bun build --compile src/index.ts --outfile ../.local/bin/plainkeep-ui   # local binary install
```

`PLAINKEEP_BIN` (absolute path to the `plainkeep` script) overrides lookup; otherwise plainkeep-ui
runs `plainkeep` from PATH. It's interactive-only — piped/non-TTY invocation exits 2 and points you
at `plainkeep <verb> --json`.

To cut a release: `git tag ui-vX.Y.Z && git push origin ui-vX.Y.Z`.

## Status — v1 (Clack-first)

Shipped: contract-generated palette + forms, dry-run preview, exit-3 confirm loop, tty hand-off,
capture quick-entry, `plainkeep.json/3` schema guard, compiled-binary distribution via
`plainkeep setup ui`. Deferred (v1.1): live arg-value completion via the right `plainkeep complete`
prior-words (today the form falls through to free text for provider args); Ink screens for `search`
live-preview and the `triage`/`organize` review loops; a setup dashboard screen.
