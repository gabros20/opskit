# The machine contract — `--json`, exit codes, `ops.json` v2, `cmd.json`

**Reference.** The exact shapes a program (or agent) can rely on when driving `ops`. Everything here
is frozen per version and covered by a contract test (`test/run_json.py`); the envelope only ever
changes with an explicit `ops_json` version bump.

---

## 1. The `--json` envelope

Every verb accepts a global `--json` flag (or `OPS_JSON=1` in the environment). Human rendering is
unchanged when it is absent. One implementation lives in `bin/lib/output.py`; verbs never hand-roll
JSON.

**Scalar verbs** — one envelope object on stdout:

```json
{"ops_json": 1, "ok": true, "verb": "status", "data": { "...": "..." }}
```

**Multi-row verbs** (`search`, `task` list, `week`, `files` list, `wiki` backlinks, …) — NDJSON: one
header object, then one plain JSON object per row:

```json
{"ops_json": 1, "ok": true, "verb": "search", "count": 5}
{"path": "notes/risk-classes.md", "heading": "(top)", "score": 0.0324, "snippet": "…"}
{"path": "notes/the-ops-loop.md",  "heading": "The ops loop", "score": 0.0321, "snippet": "…"}
```

The header may carry extra verb-specific fields (e.g. `queue`, `applied`, `dry_run` on
`organize apply`). The four reserved header keys are `ops_json`, `ok`, `verb`, `count`.

**Errors** — the envelope goes to stdout, the process exits with `error.code`:

```json
{"ops_json": 1, "ok": false, "verb": "wiki", "error": {"code": 4, "message": "no note 'xyz'", "hint": "…optional…"}}
```

Without `--json`, the same message (plus the hint) goes to stderr. Either way the exit code is the
same — the error surface is identical for humans and machines.

## 2. The exit-code protocol

| Code | Meaning | Emitted by |
|---|---|---|
| `0` | ok | the verb |
| `1` | unexpected failure (or a semantic "at-risk" status, e.g. `backup`/`repo health`) | the verb |
| `2` | usage error (message on stderr, or the error envelope under `--json`) | the verb |
| `3` | guardrail: confirm-class call without `--yes` — message contains the **exact re-run** | guardrail or the verb's self-gate |
| `4` | not found (unknown verb → includes a did-you-mean; missing note/task/asset) | guardrail / the verb |
| `5` | guardrail: deny-class — never runs | guardrail |

Constants: `output.EXIT_OK / EXIT_UNEXPECTED / EXIT_USAGE / EXIT_CONFIRM / EXIT_NOT_FOUND / EXIT_DENY`.
The dispatcher propagates guardrail codes verbatim (a refused call is `3`/`5`, never a flattened `1`).

## 3. The `--dry-run` contract

Every mutating verb declares `"dry_run": true` in its `cmd.json` and implements `--dry-run` as a true
preview: print what *would* happen, write nothing. The guardrail honours the declaration — a
confirm-class verb invoked with `--dry-run` is **downgraded to a read** and allowed without `--yes`
(a true dry-run *is* a read). This makes the entire surface explorable: `ops archive foo --dry-run`,
`ops organize apply --dry-run`, `ops share <slug> --dry-run` all run freely and mutate nothing.
(Untrusted plugin verbs are the one exception: the confirm ceiling holds even for `--dry-run`.)

## 4. `ops.json` v2 — the generated surface description

`ops.json` is **generated** by `bin/lib/manifest.py` (`ops index` and `ops help` refresh it). Nothing
in it is hand-maintained, and nothing is persisted that isn't re-detected at write time.

```json
{
  "schema": "ops.json/2",
  "ops_version": "4.0.0-dev",          // the VERSION file
  "api_version": "1.0",                // the plugin SDK version (bin/lib/api.py)
  "json_envelope": 1,                  // the envelope version above
  "capabilities": {
    "vectors": true,                   // importlib-detected: lancedb present?
    "rerank": true,                    // fastembed present?
    "agent": "none",                   // $OPS_AGENT
    "plugins": []                      // installed packs
  },
  "verbs": [ { "...": "per-verb entries, see below" } ]
}
```

Per verb (copied from its `cmd.json` sidecar, plus injected fields):

| Field | Meaning |
|---|---|
| `verb`, `summary`, `usage`, `args` | what `ops help` renders |
| `risk` | guardrail class: `read` / `safe_write` / `draft_only` / `confirm` / `deny` |
| `reads`, `writes` | declared filesystem footprint |
| `source` | `engine` or `plugin:<name>` (injected by the manifest) |
| `output` | `{mode: "scalar"|"rows", fields: {name: type}}` — the `--json` shape of the verb's default action |
| `hints` | when-to-use + the common mistake (also shown by `ops help <verb>`; becomes the MCP tool description) |
| `dry_run` | `true` if the verb supports the dry-run contract |

A third party can drive the whole system from `ops.json` alone — that is what `ops mcp` does: its MCP
tool list is generated from this file, and every tool call shells back through `ops <verb> --json`.

## 5. `cmd.json` — the per-verb sidecar (what a verb author writes)

Example (`bin/search/cmd.json`, abbreviated):

```json
{
  "verb": "search",
  "summary": "ranked file#heading hits (keyword + graph [+ vectors/rerank])",
  "usage": "ops search \"<query>\"",
  "risk": "read",
  "args": [{ "name": "query", "required": true }],
  "reads": [".index/", "wiki/"],
  "writes": [".logs/queries.jsonl"],
  "hints": "…",
  "output": { "mode": "rows", "fields": { "path": "string", "heading": "string", "score": "number", "snippet": "string" } }
}
```

Notes for authors:
- `"hidden": true` keeps a plumbing verb (`__complete`, `mcp`) out of `ops help`/`ops.json` while the
  guardrail still gates it.
- For subcommand verbs, `output` describes the **default** action's rows (`task`→list, `wiki`→list,
  `files`→list…); other subactions still emit valid envelopes, with their own row shapes.
- Undeclared `risk` defaults to `confirm` — the safe class.

## 6. Stability policy

- The envelope changes only with an `ops_json` bump; `ops.json` structure only with a `schema` bump.
- `test/run_json.py` round-trips every read-class verb against its declared `output` block and fails
  the build on drift; `test/run_plugin.py` snapshots every SDK signature.
- Consumers should key on `schema` / `ops_json` / `api_version`, not on `ops_version`.

## 7. `ops setup` layer `status` enum

Each row `ops setup` emits (`ops setup --json`, and the same rows `ops doctor` folds in) carries a
`status` field from a **closed enum** — a program keys on this, never on the human `detail` string:

| `status` | Meaning | `ops doctor` severity |
|---|---|---|
| `ready` | the layer is operational | `ok` |
| `partial` | some prerequisites present, some missing | `warn` (optional) / `FAIL` (required) |
| `absent` | no prerequisites present yet | `warn` (optional) / `FAIL` (required) |
| `blocked` | a hard prerequisite is missing (an external binary, or a human handoff); `next` carries the **exact** remediation command | `warn` (advisory) |
| `not_applicable` | the layer cannot apply on **this host** (e.g. launchd scheduling off macOS); advisory only | `ok` (never a FAIL, even for a required layer) |

`blocked` and `not_applicable` are the two the machine must special-case: neither is a defect, and
`ops setup --all` **skips** both (and `ready`) rather than attempting them — so they never contribute
to its exit code. `--all` is otherwise best-effort: it advances every attemptable layer and exits `1`
iff some *attempted* layer failed (a semantic at-risk exit per §2, not a crash; the envelope `ok`
stays `true` and the per-layer `results` carry each failure). Reading `next` is how an agent learns
the remediation for a `blocked` layer — it must never invent an install command from `detail`.
