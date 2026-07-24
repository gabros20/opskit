# The machine contract — `--json`, exit codes, `ops.json/3`, `cmd.json`

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

## 4. `ops.json/3` — the generated surface description

`ops.json` is **generated** by `bin/lib/manifest.py` (`ops index` and `ops help` refresh it). Nothing
in it is hand-maintained, and nothing is persisted that isn't re-detected at write time.

```json
{
  "schema": "ops.json/3",
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

The three top-level version fields are **independent** and version different things: `json_envelope`
freezes the `--json` envelope (§1), `api_version` the plugin SDK, and `schema` the *shape of this file*.
Only `schema` moved in this revision (`ops.json/2` → `ops.json/3`); the envelope and SDK are unchanged.

Per verb (copied from its `cmd.json` sidecar, plus injected fields):

| Field | Meaning |
|---|---|
| `verb`, `summary`, `usage`, `args` | what `ops help` renders |
| `risk` | guardrail class: `read` / `safe_write` / `draft_only` / `confirm` / `deny` |
| `reads`, `writes` | declared filesystem footprint |
| `source` | `engine` or `plugin:<name>` (injected by the manifest) |
| `group` | **(ops.json/3)** the display group the verb renders under (`SYSTEM`/`FLOW`/`KNOWLEDGE`/`TASKS`/`WORK`/`BUSINESS`/`JOBS`, else `OTHER`) — injected by the manifest from its `GROUPS` table so a UI groups verbs without re-encoding that table |
| `output` | `{mode: "scalar"|"rows", fields: {name: type}}` — the `--json` shape of the verb's default action |
| `hints` | when-to-use + the common mistake (also shown by `ops help <verb>`; becomes the MCP tool description) |
| `dry_run` | `true` if the verb supports the dry-run contract |
| `actions` | **(ops.json/3, optional)** the real subcommand grammar of a compound verb — see §5.1. Absent on scalar verbs |

Both new fields are additive: every `ops.json/2` field is retained, so a `schema`-unaware consumer that
keyed on the v2 shape keeps working. `group` is present on **every** verb; `actions` only on compound
verbs that declare it.

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

### 5.1 `actions[]` — the subcommand grammar (compound verbs, `ops.json/3`)

A **compound verb** (one whose first positional arg selects a subcommand — `task`, `wiki`, `files`, …)
may declare an **optional** `actions` array in its `cmd.json`. It is the machine-readable form of the
grammar that the verb's `usage` string states in prose and that `bin/__complete` hardcodes — one source
a generated form/TUI, `__complete`, the MCP layer, and an agent can all read instead of re-parsing usage.
It rides through into the verb's `ops.json` entry verbatim. It is purely additive: a verb keeps its
top-level `args`/`risk`/`output`/`dry_run`, which continue to describe the **default** action.

```json
"actions": [
  {
    "name": "add",                     // the subcommand token (required)
    "summary": "create a task",        // one line (optional)
    "risk": "safe_write",              // this action's guardrail class (optional; ∈ the §2 risk enum).
                                       //   Omitted ⇒ the verb's top-level risk applies (inherited).
    "dry_run": true,                   // this action honours --dry-run (optional bool).
                                       //   Omitted ⇒ it does NOT — no inheritance from top-level.
    "args": [                          // positional args + flags, IN ORDER (required; may be empty)
      { "name": "title", "type": "string", "required": true,
        "help": "the task title", "example": "Fix the Acme webhook" },
      { "name": "--due", "type": "string", "required": false, "help": "optional due date" }
    ]
  }
]
```

**Arg fields.** `name` and `type` are required; a `name` starting with `--` is a flag/option, otherwise
a positional. The rest are optional.

| Arg field | Meaning |
|---|---|
| `name` | the positional name, or `--flag` for an option (required) |
| `type` | `string` \| `int` \| `enum` \| `slug` \| `path` \| `flag` (required). `flag` = a valueless boolean switch |
| `enum` | the allowed values, a list — **required when `type` is `enum`** |
| `complete` | which live completion provider feeds this arg: `note-slug` \| `task-id` \| `hub` \| `note-type` \| `status` \| `layer` (optional) |
| `required` | `true` for a mandatory positional (optional; default `false`) |
| `default` | the value used when the arg is omitted (optional) |
| `help` | one-line description (optional) |
| `example` | a sample value for a generated form's placeholder (optional) |

Rules a consumer can rely on:
- The `name` values, in order, are the exact set of subcommand tokens the verb accepts.
- Each action's `args` are listed in invocation order.
- **`risk` inherits, `dry_run` does not.** A per-action `risk` omitted ⇒ the verb's top-level `risk`
  applies to that subcommand. A per-action `dry_run` omitted ⇒ that subcommand does **not** honour
  `--dry-run` (the top-level `dry_run` describes only the **default** action, per the note above — it is
  never inherited by the other subactions). So a UI offers `--dry-run` on exactly the actions that
  declare `dry_run: true`, and nowhere else.
- **`risk` is declarative today.** The engine guardrail currently gates on the verb's **top-level**
  `risk`; the per-action `risk` is published for consumers (a UI can confirm-gate just the subactions
  that need it) but the dispatcher does not yet enforce it per-action — that is Wave 3's contract-honesty
  pass. Until then a consumer should treat per-action `risk` as the intended class, not as what the
  guardrail will already refuse.

`test/run_json.py` validates every declared `actions[]` (typed args, enum lists present, `risk`/`complete`
in their enums) and fails the build on drift.

## 6. Stability policy

- The envelope changes only with an `ops_json` bump; `ops.json` structure only with a `schema` bump.
- **`ops.json/2` → `ops.json/3`** added two verb fields — `group` (always present) and the optional
  `actions[]` subcommand grammar (§5.1) — additively. Every v2 field is retained, so the bump is
  backward-compatible for a consumer that ignores the new fields; it is a `schema` bump (not an
  `ops_json`/`api_version` bump) because only this file's shape changed, not the envelope or SDK.
- `test/run_json.py` round-trips every read-class verb against its declared `output` block, asserts the
  `schema` value + every verb's `group` + every declared `actions[]`'s well-formedness, and fails the
  build on drift; `test/run_plugin.py` snapshots every SDK signature.
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
