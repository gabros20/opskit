# Raycast Script Commands — the first built frontend (Part 3.3)

Zero-build [Raycast Script Commands](https://github.com/raycast/script-commands): plain bash, no
extension to compile. Every command shells to `plainkeep` on `PATH` (fallback `$PLAINKEEP_HOME/plainkeep`), so the
guardrail and `.logs/` apply exactly as on the terminal — the frontend has **zero privileged
access** and re-enters through the dispatcher, never importing `bin/lib`.

## Install

1. Make sure `plainkeep` is on your `PATH` (or export `PLAINKEEP_HOME=~/plainkeep`).
2. Raycast → *Extensions* → *Script Commands* → *Add Directories* → point it at this folder
   (`~/plainkeep/frontends/raycast`).
3. The commands appear in Raycast root search: **Plainkeep Capture**, **Plainkeep Search**, **Plainkeep Task Add**,
   **Plainkeep Task List**, **Plainkeep Status**.

Because this folder lives inside the engine boundary (`script/engine.txt`), improvements flow to you
on `script/update` — but you can freely add your own `*.sh` alongside them (Raycast picks up every
script in the directory).

## Commands

| Script | Runs | Mode |
|---|---|---|
| `quick-capture.sh` | `plainkeep capture <text>` | compact |
| `search.sh` | `plainkeep search <q> --json` → top hit paths | fullOutput |
| `task-add.sh` | `plainkeep task add <title>` | compact |
| `task-list.sh` | `plainkeep task list` | fullOutput |
| `status-inline.sh` | `plainkeep orient --line` | inline (30s refresh) |

Graduate to a full React extension only after this tier proves the `--json` surface — see the
roadmap. For global-hotkey and mobile capture, see [`docs/mobile-and-capture.md`](../../docs/mobile-and-capture.md).
