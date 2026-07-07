# Layered setup

Use this after the bootstrap script has put the vault in place. `script/get` and `script/setup`
handle L0: clone or wire `~/ops`, put `ops` on PATH, install shell completion, create `~/work` and
`~/files`, track the template as fetch-only `upstream`, run `ops doctor --init`, and leave GitHub
remote/push work to the human.

`ops setup` handles the remaining local layers. It is safe to rerun; each layer checks current state
first and reports `ready`, `partial`, `absent`, or `blocked`.

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

Blocked layers stay blocked and print a handoff command. Backups are blocked because encrypted
off-machine backup setup needs human choices and secrets:

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
treats optional partial, absent, or blocked layers as advisory warnings.

```sh
ops doctor
```
