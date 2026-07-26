# Layered setup

This guide shows how to finish setting up your vault after bootstrap. It is for anyone running `ops setup` on a fresh clone, plus agents that need to advance layers safely.

## Before you start

The bootstrap scripts handle L0. Run `script/get` and `script/setup` first; they:

- Clone or wire `~/ops` and put `ops` on PATH.
- Install shell completion.
- Create `~/work` and `~/files`.
- Track the template as a fetch-only `upstream` remote.
- Run `ops doctor --init`.

GitHub remote and push work is left to you.

`ops setup` handles the remaining local layers. It is safe to rerun. Each layer checks its current state first and reports one status:

| Status | Meaning |
| --- | --- |
| `ready` | Layer is fully set up. |
| `partial` | Some pieces present, some missing. |
| `absent` | Not set up. |
| `blocked` | Needs a prerequisite or human input first. |
| `not_applicable` | This host can't run it (e.g. launchd off macOS). Advisory, never a failure. |

The full contract is in [the machine contract §7](machine-contract.md#7-ops-setup-layer-status-enum).

The six layers are: `skeleton`, `search`, `backups`, `models`, `automation`, `ui`.

## Guided first-run

The easiest way to finish setup:

```sh
ops setup --wizard
```

The wizard walks the layers in order with skippable prompts and safe defaults pre-selected:

- `skeleton` **on** — required and safe.
- `ui` **on** — a small sha256-verified binary download into the vault's own `.local/bin`.
- `search`, `models`, `automation` **off** — no vectors, no model pulls, no scheduled jobs.

Press Enter to accept a default. Type `y`/`n` to override.

Already-`ready` layers are noted and skipped. `blocked` and `not_applicable` layers show their reason and next step, and are never prompted to install.

Backups are never a yes/no here. The wizard prints the `ops backup init` handoff (it needs human secrets) and never runs it.

Each accepted layer runs through the same engine as every other path below. There is no second code path.

The wizard is interactive-only. With no tty (e.g. a piped `curl … | sh`), or combined with `--json` or `--dry-run`, it exits `2` and points you at the non-interactive forms:

- `ops setup --all --yes` to apply.
- `ops setup --json` to inspect.

Those forms and the per-layer controls are below.

## Run the dashboard

```sh
ops setup
```

Read the checklist top to bottom.

Required structure failures are fixed by the `skeleton` layer. Optional layers degrade gracefully: missing search, model, backup, or automation pieces become warnings with a one-line next step, not a broken vault.

## Advance layers

Run one layer at a time for a controlled setup:

```sh
ops setup skeleton --yes
ops setup search --yes
ops setup models --yes
ops setup automation --yes
ops setup ui --yes
```

Use `--yes` when the layer is allowed to install packages, pull models, or write generated local files.

To advance every non-ready layer setup can safely handle:

```sh
ops setup --all --yes
```

`--all` is best-effort:

- It advances every attemptable layer.
- A failure in one independent layer does not abort the rest.
- Layers that are already `ready`, `blocked` on a missing prerequisite, or `not_applicable` are skipped and never fail the run.
- Exit is `1` only if a layer it actually *attempted* failed.

### Preview first with `--dry-run`

Any advance can be previewed. `--dry-run` prints exactly what *would* run and installs or writes nothing.

A dry-run is a read, so it never needs `--yes` — even for the confirm-class `search`/`models` layers:

```sh
ops setup search --dry-run     # what the search layer would create/install/pull
ops setup --all --dry-run      # the whole plan, nothing touched
```

## The `.venv`: one home for all optional deps

Bare `python3` is the stdlib floor. Every core verb works on it with zero optional deps.

The optional `$OPS_HOME/.venv` holds **all** optional deps. The `ops` dispatcher prefers it whenever it exists and actually starts, falling back to bare `python3` otherwise. So `ops index`, `ops search`, `ops files`, and `ops doctor` all see those deps with no manual `PATH` surgery — including from an agent terminal.

Each layer installs its own dep subset into the same venv:

- `ops setup search --yes` creates `$OPS_HOME/.venv` (if missing), installs the search deps (`lancedb` + `fastembed`, from `requirements-search.txt`), pulls the embedding model, and builds the index.
- `ops setup models --yes` installs the file-processing deps (Pillow, trafilatura, and — on Apple Silicon — mlx-vlm) into the **same** venv, then pulls the local models.

The venv is just the shared, dispatcher-visible environment they land in. So `ops doctor`'s optional probes (Pillow / mlx_vlm / lancedb) run under the same interpreter and report consistently.

Re-running the relevant `ops setup <layer>` provisions or migrates that layer's deps.

The venv is disposable and rebuildable:

```sh
rm -rf .venv && ops setup search --yes && ops setup models --yes
```

A broken or half-built venv is repaired automatically on the next `ops setup search`/`models`.

This is the single install story. See [ADR-009](DECISIONS.md) and [the agent-terminal guide](agent-terminal-search.md).

## The terminal UI layer

```sh
ops setup ui --yes
```

This installs the compiled **`ops ui`** binary (ADR-011) — the guided human terminal UI — into `$OPS_HOME/.local/bin/ops-ui`, where the `bin/ui/` shim looks first.

Key facts:

- It downloads the matching platform asset from the template repo's GitHub release with the authenticated **`gh` CLI**. If the layer reports `blocked`, install gh with `brew install gh`.
- It verifies the asset's sha256 against the release's `checksums.txt` before installing.
- The binary is self-contained — no Node or Bun needed.
- **Updates ride `script/update`.** The engine ships the expected version in `bin/ui/version.txt`; the installed binary self-reports via `ops-ui --version`. When they disagree, the layer turns `partial` with "update available" and re-running `ops setup ui --yes` re-downloads the pinned release.

Full install, use, and update details are in the [terminal UI guide](terminal-ui.md).

## Blocked: backups

Blocked layers stay blocked and print the exact remediation in `next`.

Backups are blocked because encrypted off-machine backup setup needs human choices and secrets (and `restic` installed):

```sh
ops backup init
```

## Agent path

Agents should inspect state before acting:

```sh
ops setup --json
```

Use the returned rows to choose the smallest non-ready layer, then advance it explicitly:

```sh
ops setup <layer> --yes
```

Rules:

- Do not invent install commands from status text.
- If a row is `blocked`, report its handoff command to the human instead of working around it.

## Check health

`ops doctor` is the checker:

```sh
ops doctor
```

It reports the same setup layers and:

- Fails required non-ready layers.
- Treats optional `partial`, `absent`, or `blocked` layers as advisory warnings.
- Treats `not_applicable` layers as informational — never a failure, even were the layer required.
