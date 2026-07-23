# Running ops from an agent terminal (venv, PATH, and semantic search)

**How-to.** Get stage-2/3 semantic search (`OPS_VECTORS=1`, `OPS_RERANK=1`) working when `ops` is
driven by an **agent terminal** (a Telegram/Hermes-style agent, a dispatched Claude Code session, a
cron job) rather than your interactive shell. If keyword search works but vectors don't — or
`ops index` warns that `lancedb` is missing even though you installed it — this is the page.

> [!NOTE]
> **Stage 1 (keyword + wikilink graph) needs nothing but Python 3.10+ stdlib** and always works. This
> page is only about the *optional* vector/rerank planes. Everything here is setup, not code.

## The one install story

**`ops setup search --yes` provisions everything, and the dispatcher finds it automatically.** That
one command creates `$OPS_HOME/.venv`, installs *only* the search deps (`lancedb` + `fastembed`, from
`requirements-search.txt`) into it, pulls the embedding model, and builds the index. The `ops`
dispatcher then **prefers `$OPS_HOME/.venv/bin/python3` whenever it exists and starts** — for the
guardrail, the resolver, and every verb — so `ops index` / `ops search` import the vector plane with
no manual `PATH` surgery. If there is no venv (or the venv python is broken — a stale symlink after a
system-python upgrade), the dispatcher falls back to bare `python3` (the stdlib keyword floor) rather
than failing every verb.

> [!NOTE]
> The `.venv` is the single home for **all** optional deps, not just search: `ops setup models --yes`
> installs the file-processing deps (Pillow, trafilatura, mlx-vlm) into the same venv, so `ops files`
> / `ops enrich` / `ops doctor` see them under the same dispatcher-preferred interpreter. This page
> focuses on the search planes, but the interpreter contract below covers both.

```bash
cd "$OPS_HOME"          # e.g. ~/ops
ops setup search --yes  # .venv + lancedb/fastembed + embed model + index — one command
```

```
ops  ──►  $OPS_HOME/.venv/bin/python3   (if it exists — created by `ops setup search`)
          └─ else bare python3 on PATH  ──►  import lancedb ?
                                               ├─ yes → stage-2 vectors
                                               └─ no  → keyword-only (a warning, never a crash)
```

This is the whole contract (ADR-009): bare `python3` is the stdlib floor; the optional `.venv` holds
all optional deps (search + models); the dispatcher prefers it when present and startable; **agent
terminals inherit that for free** —
they run the same `ops` script, so they get the same interpreter without any per-agent PATH ordering.
Preview it first with `ops setup search --dry-run` (writes nothing, needs no `--yes`).

> [!NOTE]
> On **macOS Intel (x86_64)** `pip` resolves `lancedb` to 0.25.x — that is expected and works;
> `requirements-search.txt` carries platform-aware markers so this installs cleanly on every host.

## What the agent terminal still needs: `OPS_HOME` and the `OPS_*` flags

The interpreter is now handled for you, but two things still must reach the agent's shell:

- **`OPS_HOME`** — so `ops` (and its venv) resolve to *your* vault, not a default.
- **`OPS_VECTORS=1` / `OPS_RERANK=1`** — the opt-in flags that turn the vector/rerank arms *on* at
  query time (the venv makes them importable; these env flags make search *use* them).

An interactive login shell sources `~/.zshrc`, so these are present. **An agent terminal frequently
is not** — it builds its own environment per session and may source only bash profiles
(`~/.profile`, `~/.bash_profile`), which on a zsh-only Mac often don't exist. The fix is generic:
**point the agent's terminal at a bash-safe init file that exports `OPS_HOME` and the `OPS_*` flags**
(`export` statements only — no zsh-only syntax), because agent terminals typically source init files
with `bash`. You no longer need to prepend `.venv/bin` to `PATH` — the dispatcher does that job.

### Worked example — Hermes (`~/.hermes/config.yaml`)

*Accurate as of Hermes mid-2026; a third-party tool, so verify against its current docs.*

```yaml
terminal:
  backend: local
  cwd: ~/ops
  shell_init_files:
    - /Users/<you>/.zshrc          # or a dedicated bash shim, see below
```

> [!IMPORTANT]
> **`shell_init_files` must be a YAML *list*, not a scalar string.** Hermes discards a non-list value
> silently (its loader does `if not isinstance(files, list): files = []`) and falls back to bash
> profiles — with **no error**. `hermes config set terminal.shell_init_files /path/to/.zshrc` can
> write a bare string; confirm the file actually contains a `- ` list item. This silent no-op is the
> single most common cause of "it works in my shell but not for the agent".

If your `~/.zshrc` has zsh-only constructs, don't source it with bash — use a dedicated shim instead:

```bash
# ~/.hermes/ops-shell-init.sh   (bash-safe: export only)
export OPS_HOME="$HOME/ops"
export OPS_VECTORS=1     # the dispatcher already prefers $OPS_HOME/.venv/bin/python3 — no PATH surgery
export OPS_RERANK=1
```

```yaml
terminal:
  shell_init_files:
    - /Users/<you>/.hermes/ops-shell-init.sh
```

**Session/reload behavior (Hermes):** a config change may be picked up by file mtime, but **existing
sessions keep their old environment snapshot** — start a **new** session (`/new`) to get the new env.
The gateway can't restart itself from inside a running session; restart it from a separate terminal
if a full reload is needed.

## Verify — from inside the agent's terminal

Run these *in the agent's terminal*, not your own — the whole point is that its environment can
differ from yours:

```bash
ops setup search           # expect: search "ready" (deps-importable ✓ · model-pulled ✓ · index-built ✓)
ops doctor                 # expect: "optional: lancedb present (stage-2 vectors)"
ops index                  # embeds notes → vectors.lance (no fallback warning)
ops search "some idea"     # semantic hits, not just keyword
```

If `ops setup search` reports `blocked`, its `next` field is the exact command to run (e.g. install
ollama). If `ops doctor` prints **"OPS_VECTORS=1 but lancedb is NOT importable by this python3"**, the
venv wasn't created or is missing the deps — re-run `ops setup search --yes` (or preview with
`--dry-run`). `ops index` still succeeds keyword-only; it never crashes on a missing vector plane
(that graceful fallback is by design — see the CHANGELOG / issue #3).

## What this deliberately does not require

No manual venv, no `PATH` ordering, no vault-side daemon. `ops setup search` creates the one venv and
the dispatcher prefers it; the stdlib keyword floor still runs on bare `python3` when there is no
venv. An agent terminal only needs `OPS_HOME` and the `OPS_*` flags in its environment — it runs the
same `ops` script, so it inherits the same interpreter. One install story, everywhere.
