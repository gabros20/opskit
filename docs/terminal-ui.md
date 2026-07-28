# The terminal UI (`plainkeep ui`)

How to install, use, and update the guided terminal UI. For the design rationale, see
[ADR-011 in `DECISIONS.md`](DECISIONS.md); for the source and contributor workflow, see
[`../ui/README.md`](../ui/README.md).

`plainkeep ui` is the human face of the system. It reads the machine contract (`plainkeep help
--json`) and generates itself: a verb palette grouped like `plainkeep help`, a form per action built
from its typed arguments, and result views that render tables instead of JSON. Every action it
takes re-enters `plainkeep <verb> --json` as a subprocess — the guardrail and `.logs/` see the UI
exactly as they see an agent.

## Install

```sh
plainkeep setup ui --yes
```

This downloads a self-contained compiled binary (no Node required) for your platform from the
template repo's GitHub release, verifies its sha256 against the release's `checksums.txt`, and
installs it to `$PLAINKEEP_HOME/.local/bin/plainkeep-ui` — where the `plainkeep ui` shim looks first.

Requirements:

- The **GitHub CLI (`gh`)**, authenticated. The template repo may be private, so the download uses
  your existing `gh` auth. Missing it, the layer reports `blocked` with the install hint
  (`brew install gh`).
- Supported platforms: macOS (Apple Silicon + Intel) and Linux (x64 + arm64).

The wizard (`plainkeep setup --wizard`) offers this layer with a default of **yes** — it is a small,
verified download into the vault's own `.local/bin/`, nothing system-wide.

## Use

```sh
plainkeep ui
```

- **Pick a verb** from the grouped palette (type to filter), or use the quick **Capture** entry at
  the top.
- **Compound verbs** (task, wiki, files, …) show an action picker; each action's form prompts only
  for its declared arguments — enums become selects, known values become pickers.
- **Confirm-class actions** run first *without* `--yes`. The verb refuses (exit 3), the UI shows
  the refusal and offers the confirmed re-run. The UI never pre-confirms anything.
- **Dry-run preview**: actions that support `--dry-run` offer a preview before the real run — a
  dry-run is a read, so it needs no confirmation.
- **Terminal hand-off**: tty verbs (`wiki edit` → `$EDITOR`, `backup init`) get the real terminal.

The UI is interactive-only. Piped or scripted invocation exits `2` and points at
`plainkeep <verb> --json` — that surface is for machines.

## Update

Updates ride the normal engine update — there is no separate update command:

```sh
./script/update      # engine update brings the new expected UI version
plainkeep setup            # dashboard shows:  ui  partial  "update available: installed X → Y"
plainkeep setup ui --yes   # downloads the exact release the engine expects
```

How it works: the engine ships the version it expects in `bin/ui/version.txt` (an engine file, so
`script/update` bumps it), and the installed binary reports its own via `plainkeep-ui --version`. The
setup status compares the two **offline** — no network in `plainkeep setup` or `plainkeep doctor` —
and a mismatch makes the layer attemptable again. The download is pinned to the matching release
tag, so a vault always gets the binary its engine was tested with.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `plainkeep ui` says "not installed" | `plainkeep setup ui --yes` (or set `PLAINKEEP_UI_BIN=/path/to/plainkeep-ui`) |
| Layer reports `blocked` | install the GitHub CLI: `brew install gh`, then `gh auth login` |
| Layer reports `not_applicable` | no prebuilt binary for this platform — build from source (below) |
| Update never appears | your engine predates versioned UI — run `./script/update` first |

**Resolution order** for the binary: `$PLAINKEEP_UI_BIN` (explicit override) →
`$PLAINKEEP_HOME/.local/bin/plainkeep-ui` (what setup installs) → `plainkeep-ui` on PATH.

**Build from source** (contributor checkout with `ui/` present, needs [Bun](https://bun.sh)):
`plainkeep setup ui --yes` compiles automatically when no release is reachable, or manually:

```sh
cd ui && bun install && bun run build:binary
```
