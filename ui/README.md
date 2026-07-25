# ui/ — the ops terminal UI (`ops ui`)

**The human face of [`opskit`](https://github.com/gabros20/opskit).** A guided, menu-driven UI over
the `ops.json/3` contract — you point-and-pick instead of memorizing flags. Agents keep using
`ops <verb> --json`; humans get this. **Two faces, one door.**

```
┌ ops  the guided terminal UI — humans point-and-pick, agents use ops <verb> --json
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
- In a vault, `ops setup ui --yes` downloads the matching asset with the **authenticated `gh` CLI**
  (the template repo may be private), verifies its sha256, and installs it to
  `$OPS_HOME/.local/bin/ops-ui` — exactly where the stdlib `bin/ui/` shim looks first.
- No Node, Bun, or `node_modules` ever enters a vault. The engine's zero-dependency floor holds.

## How it works

ops-ui **never hardcodes menus or flags**. It runs `ops help --json` to read the contract and
*generates* itself:

- the verb palette comes from the manifest's groups;
- each verb's form is built from its `actions[]` + typed `args` (enum → select, completion providers →
  pickers, everything else → text);
- `confirm`-class actions run first *without* `--yes`; the verb self-gates (exit 3) and ops-ui renders
  the refusal + offers the exact re-run — it never pre-appends `--yes`;
- `dry_run` actions offer a **Preview** (a dry-run is a read, no `--yes` needed);
- `tty` verbs (`wiki edit` → `$EDITOR`, `backup init`) hand off the real terminal.

Every action re-enters `ops <verb> --json` as a subprocess, so the guardrail and `.logs/` see it
exactly as they see an agent. ops-ui imports no `ops` internals.

## Develop (contributor checkout)

Requires Bun (or Node ≥ 20 with npm) and an `ops` vault (schema `ops.json/3`+).

```sh
cd ui
bun install
OPS_BIN=/path/to/ops/ops bun run dev      # run the TUI against a vault

bunx tsc --noEmit                          # typecheck
bun build --compile src/index.ts --outfile ../.local/bin/ops-ui   # local binary install
```

`OPS_BIN` (absolute path to the `ops` script) overrides lookup; otherwise ops-ui runs `ops` from
PATH. It's interactive-only — piped/non-TTY invocation exits 2 and points you at `ops <verb> --json`.

To cut a release: `git tag ui-vX.Y.Z && git push origin ui-vX.Y.Z`.

## Status — v1 (Clack-first)

Shipped: contract-generated palette + forms, dry-run preview, exit-3 confirm loop, tty hand-off,
capture quick-entry, `ops.json/3` schema guard, compiled-binary distribution via `ops setup ui`.
Deferred (v1.1): live arg-value completion via the right `ops complete` prior-words (today the form
falls through to free text for provider args); Ink screens for `search` live-preview and the
`triage`/`organize` review loops; a setup dashboard screen.
