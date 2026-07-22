# Running ops from an agent terminal (venv, PATH, and semantic search)

**How-to.** Get stage-2/3 semantic search (`OPS_VECTORS=1`, `OPS_RERANK=1`) working when `ops` is
driven by an **agent terminal** (a Telegram/Hermes-style agent, a dispatched Claude Code session, a
cron job) rather than your interactive shell. If keyword search works but vectors don't — or
`ops index` warns that `lancedb` is missing even though you installed it — this is the page.

> [!NOTE]
> **Stage 1 (keyword + wikilink graph) needs nothing but Python 3.10+ stdlib** and always works. This
> page is only about the *optional* vector/rerank planes. Everything here is setup, not code.

## The one durable fact

**`ops` runs whichever `python3` is first on `PATH`.** The dispatcher (the `ops` script) shells to
bare `python3` for the guardrail, the resolver, and every verb (`bin/*/run.py`) — it does **not**
activate `$OPS_HOME/.venv` for you. So the optional packages (`lancedb`, `fastembed`) must be
importable by *that* interpreter.

Everything below is a consequence of this one fact. The trap is that your **interactive** shell and
an **agent's** shell often resolve `python3` to *different* interpreters, because an agent terminal
usually doesn't source `~/.zshrc`.

```
ops  ──►  python3 (first on PATH)  ──►  import lancedb ?
                                          ├─ yes → stage-2 vectors
                                          └─ no  → keyword-only (with a warning, never a crash)
```

## 1. Provision the interpreter

Put the optional deps in a venv that lives with the vault:

```bash
cd "$OPS_HOME"                       # e.g. ~/ops
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull embeddinggemma           # the local embedder (or your OPS_EMBED_MODEL)
```

> [!NOTE]
> On **macOS Intel (x86_64)** `pip` resolves `lancedb` to 0.25.x — that is expected and works;
> `requirements.txt` carries platform-aware markers so this installs cleanly. See the header of
> `requirements.txt` for the why.

## 2. Order PATH so the venv wins

The venv's `bin` must come **before** any other `python3` shim (`~/.local/bin`, Homebrew):

```bash
export OPS_HOME="$HOME/ops"
export PATH="$OPS_HOME/.venv/bin:$HOME/.local/bin:$PATH"
export OPS_VECTORS=1                  # optional: enable the vector plane
export OPS_RERANK=1                   # optional: enable the rerank plane
```

> [!WARNING]
> Putting `~/.local/bin` **before** `.venv/bin` is a real, silent failure: `ops` then runs a
> Homebrew/PEP-668 `python3` with no optional deps while your fully-provisioned venv sits unused.
> `ops doctor` will report `lancedb` missing even though you "installed" it — because it checks the
> interpreter on PATH, not the venv.

## 3. Make the agent terminal inherit the same environment

An interactive login shell sources `~/.zshrc`, so the exports above are present. **An agent terminal
frequently does not** — it builds its own environment per session and may source only bash profiles
(`~/.profile`, `~/.bash_profile`), which on a zsh-only Mac often don't exist. Result: the agent's
`python3` and `OPS_*` are wrong, and semantic search silently falls back to keyword-only.

The fix is generic: **point the agent's terminal at an init file that sets `OPS_HOME`, `PATH`, and
the `OPS_*` flags, and make that file bash-safe** (`export` statements only — no zsh-only syntax),
because agent terminals typically source init files with `bash`.

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
export PATH="$OPS_HOME/.venv/bin:$HOME/.local/bin:$PATH"
export OPS_VECTORS=1
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

## 4. Verify — from inside the agent's terminal

Run these *in the agent's terminal*, not your own — the whole point is that they can differ:

```bash
which python3                        # must be $OPS_HOME/.venv/bin/python3
python3 -c 'import lancedb; print(lancedb.__version__)'   # must import
ops doctor                           # expect: "optional: lancedb present (stage-2 vectors)"
OPS_VECTORS=1 ops index              # embeds notes → vectors.lance (no fallback warning)
ops search "some idea"               # semantic hits, not just keyword
```

If `ops doctor` prints **"OPS_VECTORS=1 but lancedb is NOT importable by this python3"**, the
interpreter on PATH is wrong — recheck steps 2 and 3. `ops index` will still succeed keyword-only; it
never crashes on a missing vector plane (that graceful fallback is by design — see the CHANGELOG /
issue #3).

## What this deliberately does not require

No change to how `ops` runs — it stays a bare-`python3`-on-PATH dispatcher, so any agent terminal
that can set environment variables works the same way (Hermes is just the worked example). No daemon,
no vault-side config, no second interpreter. Get the three layers to agree on one `python3` and
semantic search follows.
