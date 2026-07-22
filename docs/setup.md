# Layered setup

Use this after the bootstrap script has put the vault in place. `script/get` and `script/setup`
handle L0: clone or wire `~/ops`, put `ops` on PATH, install shell completion, create `~/work` and
`~/files`, track the template as fetch-only `upstream`, run `ops doctor --init`, and leave GitHub
remote/push work to the human.

`ops setup` handles the remaining local layers. It is safe to rerun; each layer checks current state
first and reports `ready`, `partial`, `absent`, `blocked`, or `not_applicable` (a layer this host
can't run — e.g. launchd scheduling off macOS; advisory, never a failure). The full status contract
is in [the machine contract §7](machine-contract.md#7-ops-setup-layer-status-enum).

## Run the dashboard

```sh
ops setup
```

Read the checklist top to bottom. Required structure failures are fixed by the skeleton layer.
Optional layers degrade: missing search, model, backup, or automation pieces become warnings and
one-line next steps rather than a broken vault.

## Advance layers

Run one layer at a time when you want a controlled setup:

```sh
ops setup skeleton --yes
ops setup search --yes
ops setup models --yes
ops setup automation --yes
```

Use `--yes` when the layer is allowed to install packages, pull models, or write generated local
files. To ask setup to advance every non-ready layer it can safely handle:

```sh
ops setup --all --yes
```

`--all` is **best-effort**: it advances every attemptable layer, and a failure in one independent
layer does not abort the rest. Layers that are already `ready`, `blocked` on a missing prerequisite,
or `not_applicable` to this host are skipped (not attempted) and never fail the run; the exit is `1`
only if a layer it *attempted* failed.

### Preview first with `--dry-run`

Any advance can be previewed. `--dry-run` prints exactly what *would* run and installs/writes
**nothing** — and, because a dry-run is a read, it never needs `--yes` (even for the confirm-class
search/models layers):

```sh
ops setup search --dry-run     # what the search layer would create/install/pull
ops setup --all --dry-run      # the whole plan, nothing touched
```

### The search layer provisions its own venv

`ops setup search --yes` creates an isolated `$OPS_HOME/.venv`, installs **only** the search deps
(`lancedb` + `fastembed`, from `requirements-search.txt`) into it, pulls the embedding model, and
builds the index. The `ops` dispatcher then prefers `$OPS_HOME/.venv/bin/python3` automatically, so
`ops index` / `ops search` see the vector plane with no manual `PATH` surgery — including from an
agent terminal. This is the single install story; see [ADR-008](DECISIONS.md) and
[the agent-terminal guide](agent-terminal-search.md). (The file-processing deps — Pillow, trafilatura,
mlx-vlm — belong to the `models` layer, not the search venv.)

Blocked layers stay blocked and print the exact remediation in `next`. Backups are blocked because
encrypted off-machine backup setup needs human choices and secrets (and `restic` installed):

```sh
ops backup init
```

## Agent path

Agents should inspect state before acting:

```sh
ops setup --json
```

Use the returned rows to choose the smallest non-ready layer, then advance explicitly:

```sh
ops setup <layer> --yes
```

Do not invent install commands from status text. If a row is blocked, report its handoff command to
the human instead of working around it.

## Check health

`ops doctor` is the checker. It reports the same setup layers, fails required non-ready layers, and
treats optional partial, absent, or blocked layers as advisory warnings. `not_applicable` layers are
informational (never a failure, even were the layer required).

```sh
ops doctor
```
