# Layered setup

Use this after the bootstrap script has put the vault in place. `script/get` and `script/setup`
handle L0: clone or wire `~/ops`, put `ops` on PATH, install shell completion, create `~/work` and
`~/files`, track the template as fetch-only `upstream`, run `ops doctor --init`, and leave GitHub
remote/push work to the human.

`ops setup` handles the remaining local layers. It is safe to rerun; each layer checks current state
first and reports `ready`, `partial`, `absent`, `blocked`, or `not_applicable` (a layer this host
can't run — e.g. launchd scheduling off macOS; advisory, never a failure). The full status contract
is in [the machine contract §7](machine-contract.md#7-ops-setup-layer-status-enum).

## Guided first-run (`ops setup --wizard`)

The easiest way to finish setup interactively. `ops setup --wizard` walks the layers in order with
**skippable prompts** and safe defaults pre-selected — skeleton **on** (required, safe), the
terminal UI **on** (a small sha256-verified binary download into the vault's own `.local/bin`), and
search / models / automation **off** (no vectors, no model pulls, no scheduled jobs). Press Enter to
accept each default; type `y`/`n` to override. Already-`ready` layers are noted and skipped;
`blocked` / `not_applicable` layers show their reason and next step and are never prompted to install.
Backups are never a yes/no here — the wizard prints the `ops backup init` handoff (it needs human
secrets), never runs it. Each accepted layer advances through the *same* engine as everything below —
there is no second code path.

```sh
ops setup --wizard
```

The wizard is **interactive-only**: with no tty (e.g. a piped `curl … | sh`), or combined with
`--json` / `--dry-run`, it exits `2` and points you at the non-interactive forms
(`ops setup --all --yes` to apply, `ops setup --json` to inspect). Those forms — and the granular
per-layer controls — are below.

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
ops setup ui --yes
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

### The `.venv` is the single home for all optional deps

Bare `python3` is the stdlib floor — every core verb works on it with zero optional deps. The
OPTIONAL `$OPS_HOME/.venv` holds **all** optional deps, and the `ops` dispatcher prefers it whenever
it exists and actually starts (falling back to bare `python3` otherwise), so `ops index` / `ops
search` / `ops files` / `ops doctor` all see those deps with no manual `PATH` surgery — including from
an agent terminal.

- `ops setup search --yes` creates `$OPS_HOME/.venv` (if missing), installs the search deps
  (`lancedb` + `fastembed`, from `requirements-search.txt`) into it, pulls the embedding model, and
  builds the index.
- `ops setup models --yes` installs the file-processing deps (Pillow, trafilatura, and — on Apple
  Silicon — mlx-vlm) into the **same** venv, and pulls the local models.

Each layer owns its own dep subset; the venv is just the shared, dispatcher-visible environment they
land in — so `ops doctor`'s optional probes (Pillow / mlx_vlm / lancedb) run under the same
interpreter and report consistently. Re-running the relevant `ops setup <layer>` provisions or
migrates that layer's deps into the venv. The venv is disposable and rebuildable
(`rm -rf .venv && ops setup search --yes && ops setup models --yes`); a broken or half-built venv is
repaired automatically on the next `ops setup search`/`models`. This is the single install story; see
[ADR-009](DECISIONS.md) and [the agent-terminal guide](agent-terminal-search.md).

### The terminal UI layer (`ops setup ui`)

`ops setup ui --yes` installs the compiled **`ops ui`** binary (ADR-011) — the guided human terminal
UI — into `$OPS_HOME/.local/bin/ops-ui`, where the `bin/ui/` shim looks first. It downloads the
matching platform asset from the template repo's GitHub release with the **authenticated `gh` CLI**
(the template may be private; install gh with `brew install gh` if the layer reports `blocked`) and
verifies its sha256 against the release's `checksums.txt` before installing. The binary is fully
self-contained — no Node or Bun is needed on this machine. In a full contributor checkout (with
`ui/` source present) plus `bun` on PATH, the layer compiles from source instead.

**Updates ride `script/update`.** The engine ships the ui version it expects in
`bin/ui/version.txt` (engine-owned), and the installed binary self-reports via `ops-ui --version`.
When they disagree — e.g. after a `script/update` pulled a newer engine — the layer's status turns
`partial` with "update available", `ops doctor` nudges you, and the same `ops setup ui --yes`
re-downloads the exact release the engine expects (the download is pinned to that tag). No separate
update command; the dashboard tells you when, the layer does the rest.

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
