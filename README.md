# ops-ui

**The human terminal UI for [`ops`](https://github.com/gabros20/personal-operating-system).** A guided,
menu-driven face over the `ops.json/3` contract — so you point-and-pick instead of memorizing flags.
Agents keep using `ops <verb> --json`; humans get this. **Two faces, one door.**

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

## Run it

Requires Node ≥ 20 and an `ops` vault (schema `ops.json/3`+).

```sh
npm install
npm run build

# point at your ops dispatcher (or have `ops` on PATH):
OPS_BIN=/path/to/ops/ops node dist/index.js

# or install globally so the `ops ui` shim finds it:
npm link            # puts `ops-ui` on PATH
ops ui              # the dispatcher execs ops-ui
```

`OPS_BIN` (absolute path to the `ops` script) overrides PATH lookup; otherwise ops-ui runs `ops` from
PATH. It's interactive-only — piped/non-TTY invocation exits 2 and points you at `ops <verb> --json`.

## Status — v1 (Clack-first)

Shipped: contract-generated palette + forms, dry-run preview, exit-3 confirm loop, tty hand-off,
capture quick-entry, `ops.json/3` schema guard. Deferred (v1.1): live arg-value completion via the
right `ops complete` prior-words (today the form falls through to free text for provider args); Ink
screens for `search` live-preview and the `triage`/`organize` review loops; a setup dashboard screen.
