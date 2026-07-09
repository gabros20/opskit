# Decisions log — Personal OS design

Append-only ADR log for the *design itself* (the §8.2 pattern, applied to this design repo).
Each entry: context → decision → why → status. Newest at the bottom. Appendix A / A.1 in
`PERSONAL_OS_DESIGN.md` holds the per-merge table; this log holds the load-bearing "why".

---

## ADR-001 — Adopt six gbrain ideas into v3.7 (2026-06-17)
**Context.** Studied `garrytan/gbrain` (Postgres-native "compiled intelligence" runtime) for ideas
to sharpen this plaintext/git/shell design.
**Decision.** Transpose six ideas that fit the first principles: compiled-truth/timeline two-zone
notes (§7.2, §10.1), brain-first lookup (§1, §12.3), the Iron Law — model picks WHAT, system
guarantees WHERE/HOW (§1, §5, §12.3), zero-LLM auto-backlinks (§10), routing-eval fixtures (§11),
and a `consolidate` dream-lite job (§15). Reject gbrain's runtime weight (Postgres, embeddings
stack, minions/autopilot, skillopt, schema-packs).
**Why.** The ideas are substrate-independent discipline; the runtime is unearned complexity that
violates reversibility (principle 6). gbrain's own 147k-token agent file is the cautionary tale.
**Status.** Done (v3.7). Validated by the `test/` harness.

## ADR-002 — Retrieval staging: Karpathy wiki foundation; local file-based vectors as stage-2 (2026-06-18)
**Context.** Open question: does this system need vector embeddings? Surveyed the 2026 X landscape
(Karpathy LLM Wiki, Farzapedia, gbrain, FalkorDB, LightRAG, Kwipu, RDF) and measured retrieval on a
fixture corpus with a real local embedder (ollama `mxbai-embed-large`).
**Decision.** Keep the compiled-markdown + index-files + wikilink-graph + agent-navigation
foundation (the dominant validated pattern — this design already is it). Stage retrieval:
rg → FTS5 + wikilink-graph → (when earned) `sqlite-vec` + local Ollama embeddings + RRF hybrid.
Reject the server/graph-DB tier (Postgres+pgvector, FalkorDB, LightRAG, Kùzu-as-server, RDF).
**Why.** The **retrieval add-on test** (§10.2.1): file-based + locally-computed + rebuilt-from-
plaintext = allowed (it's "one SQLite file over a server"); a server or an LLM-extracted second
graph that goes stale = rejected (principle 6). Measurement: on queries sharing no vocabulary with
the target note, keyword+graph = 0.00 recall@5, local vectors = 1.00 — vectors recover exactly what
keyword structurally cannot. The graph need is already met for free by `[[wikilinks]]` + backlinks.
**Status.** Decided; magnitude now MEASURED. A fair, ops-shaped vault was built from a real
58-note LLM/agents KB (13 area hubs, 435 wikilinks, frontmatter; `vault/`, built by a 14-agent
workflow) and queried with 25 realistic queries (`test/vault_queries.txt`: 11 exact-term, 14
natural-language) via `run_search_live.py` with real local embeddings (ollama mxbai-embed-large):
- All 11 exact-term queries: keyword+graph == vector (keyword suffices).
- Of 14 natural-language queries: **~8 clear vector wins** (keyword put the wrong note #1),
  and on **5 of them keyword+graph missed the right note entirely even at rank 3**; vectors got
  them at #1. Net: ~32% clear vector wins, 40% divergence — **above the ~25% threshold**.
- Verdict: **stage-2 vectors are EARNED for natural-language / conceptual retrieval.**
- Caveat: this corpus is conceptual (curriculum); an entity/proper-noun-heavy vault (clients,
  people, dates) skews more lexical. `ops search` query-logging (`.logs/queries.jsonl`) is live,
  so the production log confirms the per-domain mix over time. Engine when built: `sqlite-vec` +
  local Ollama, per ADR-003 — **revised by ADR-006 for scale: vectors in LanceDB, not sqlite-vec.**

## ADR-003 — Vector engine: SQLite + `sqlite-vec`, not libSQL (2026-06-18)
**Context.** Evaluated libSQL (Turso's MIT SQLite fork): file-format-compatible, embedded single-file,
*native* vector search (`F32_BLOB`, `vector_distance_cos`, DiskANN `vector_top_k`).
**Decision.** Use plain SQLite + the `sqlite-vec` extension. Keep libSQL as a documented, zero-
migration drop-in fallback (same file format); its sync/cloud features stay off-limits.
**Why.** Reversibility (principle 6): plain SQLite is already present (Python `sqlite3` stdlib, the
CLI, public domain, outlives any company); libSQL is a one-company fork whose reason-for-being —
embedded replicas / sync / cloud — is the server gravity this design walls off. The index is a
disposable rebuilt-from-markdown cache, so native-vs-extension vectors is mere ergonomics, and
DiskANN's ANN only matters past ~100k vectors (brute-force cosine is instant at this scale).
**Status.** Decided for the *keyword/metadata/graph* store (SQLite FTS5 stays). **Revised in part by
ADR-006:** at the target scale (100k–500k+ notes → ~1M+ chunks) sqlite-vec's brute-force does NOT
hold, so VECTORS live in LanceDB (embedded, file-based ANN), not sqlite-vec. SQLite remains the
keyword/metadata/graph engine.

## ADR-004 — Validate the design by simulation, not just review (2026-06-16 → ongoing)
**Context.** The system has no implementation yet — only a spec. A spec can't be unit-tested, but it
can be modeled and attacked.
**Decision.** Build `test/`: a deterministic guardrail/jobs/sweep/wiki/state model exercised by
adversarial cases, plus an LLM-operator simulation (the design's own AGENTS.md + operate-ops fed to
a real model) judged for drift/bypass/misfiling, with a two-model agnosticism diff.
**Why.** It catches what review misses by eye. It found ~17 real spec gaps/holes — `ops repo adopt`,
the sweep write-zone carve-out, backup risk class, symlink/case-insensitivity/transmit-by-any-tool
guardrail escapes, global slug uniqueness, worktree sanctioning, the swept-rescue rule — each fixed
in the spec then re-validated. Prompt-injection (6 attacks) and the agnosticism diff both pass clean.
**Status.** Ongoing. Hard gates are structural; free-text checks match meaning to avoid LLM-phrasing
flakiness (see `test/README.md`).

## ADR-005 — Stage-2 embedding model: EmbeddingGemma-300m (default, configurable) (2026-06-19)
**Context.** ADR-002 earned stage-2 vectors; ADR-003 fixed the store (sqlite-vec + local Ollama).
Open: which local, multilingual (EN + HU + DE + common), efficient, mid-sized, frontier embedder?
Researched MTEB multilingual standings (HF Hub + web) and A/B'd on the vault with real local models.
**Decision.** Default **`embeddinggemma` (google/embeddinggemma-300m)**: 303M, 768-dim Matryoshka
(→256/128), Gemma license, 100+ langs incl. Hungarian/German, #1 under 500M on MTEB multi/en/code,
Ollama-native. Keep the model a one-line config (`OPS_EMBED_MODEL`) with **per-model prompt
profiles**, so `bge-m3` (MIT, proven low-resource/Hungarian) and `qwen3-embedding:0.6b` (Apache-2.0,
modern, ~2×) are drop-in alternatives. Engine per ADR-003 (local file, no server).
**Why (measured `test/run_search_live.py`, vault):**
- **Prompt prefixes are MANDATORY, not optional.** Run *without* them, EmbeddingGemma collapsed
  (80% divergence, degenerate repeated top-1, Hungarian unusable). *With* the doc/query prompts
  (`title: none | text:` / `task: search result | query:`) it behaved correctly (48% divergence on
  English, comparable to mxbai's 40%). The implementation MUST encode per-model prompts.
- **No English regression:** with prompts, EmbeddingGemma ≈ mxbai-embed-large on the English vault,
  so switching from English-only mxbai to multilingual Gemma costs nothing on English and adds
  multilingual headroom.
- **Multilingual is vectors-only:** on Hungarian queries vs the English vault, keyword+graph scored
  ~0 (no cross-language token overlap) while EmbeddingGemma bridged several correctly (e.g.
  "token költség"→token-optimization, "több ágens koordinálása"→coordination-strategies). Cross-
  lingual is a stress case; mono-lingual HU→HU will be stronger. For any non-English content,
  keyword cannot work and a multilingual embedder is the only path.
**Caveat.** A/B corpus is English; Hungarian tested cross-lingually (no HU notes yet). Confirm with
real HU content + the production query log before final lock. `bge-m3` is the fallback if Hungarian
quality disappoints (longest low-resource track record). **Status.** Default chosen; implement on go-ahead.

## ADR-007 — Accept and implement the v4 platform roadmap (2026-07-02)
**Context.** The 15-agent research synthesis produced `docs/design/proposals/2026-07-01-v4-platform-roadmap.md`
(machine contract → plugins → frontends → pipeline → durability). The owner accepted the whole
roadmap for implementation (5.3 `ops publish` and 3.5 TUI stay deferred, per the proposal itself).
**Decision.** Implement Parts 0–5 as specified, on branch `v4-platform`, one revertible commit per
package: 0.1–0.5 trust fixes (exit-code protocol 0/2/3/4/5, `script/update` 3-way merge keyed on
`.ops-engine-ref`, doctor sync-wall/second-remote/churn checks, system-wide `--dry-run`); 1.1–1.2
the machine contract (`--json` envelope via `bin/lib/output.py` on every verb, ops.json v2 with
capabilities/source/hints/output blocks); 2.1–2.4 the platform (multi-root resolver `bin/` →
`plugins/` → `$OPS_PATH`, frozen `lib/api.py` SDK v1.0, `ops plugin` with guardrail trust ceiling,
`ops mcp` stateless stdio server re-entering the dispatcher); 3.1–3.4 surfaces (Obsidian Frontend
Zero pack + Bases + JSON Canvas, Raycast script commands, `ops open`/`ops orient`, search snippets);
4.1–4.4 the pipeline (`files extract` tiers, checked provenance planes, `files distill`,
`ops organize` propose→review→apply with closed op catalog); 5.1–5.4 durability (restic backup
family, zero-knowledge `ops share` with vendored worker, `script/get` install funnel).
**Why.** Ten sequential implementation agents + one QA agent + operator validation: full offline
suite green (36 sections, incl. 12 new v4 suites), all 12 anti-roadmap constraints verified with
zero violations, no verb spelling removed (22 kept, 6 added: mcp/open/orient/organize/plugin/share),
stdlib-only zero-install path intact, guardrail remains the single enforcement path.
**Status.** Done on `v4-platform` (a2ac7f3…285f5e5). QA's one wrinkle (`organize apply` ignored
`--dry-run`) was fixed post-QA: `apply --dry-run` now previews the exact replay — budget and
protected-path accounting included — writing no files, commits, ledger lines, or journal entries.

## ADR-006 — Scale to 100k–500k+ notes from day one, single-machine, no server (2026-06-19)
**Context.** Owner's ambition is gbrain-scale (hundreds of thousands of notes), not a small personal
KB. Prior ADRs sized some choices for small scale. Re-architect for volume *without* abandoning the
first principles (plaintext truth, reversibility, no server). Grounded in research: sqlite-vec is
brute-force (fails >~1M vectors); git degrades badly past ~10k files (gbrain abandoned git-wiki at
~5k); LanceDB is embedded/file-based with disk IVF-PQ ANN, <20ms @1M, larger-than-RAM, billions-scale
single-node; SQLite FTS5 scales to millions of rows.
**Decision — the scale-ready stack (all embedded, no server, rebuildable from markdown):**
1. **System of record stays plaintext markdown in ONE git repo** (principle 1–2 intact, unbent).
   Correction to an earlier overstatement: a single repo IS enough at 100k–500k *text* notes.
   Git slows from three independent causes — (a) working-tree file count, (b) repo size / binary
   blobs, (c) a single flat directory — and only the ones this design already neutralizes bite:
   - **(a) file count** is solved by git's large-repo features (`feature.manyFiles`, `core.fsmonitor`,
     `core.untrackedCache`, `commit-graph`) — near-constant `git status` regardless of count
     (Microsoft runs the 3.5M-file Windows repo on git; 100k–500k is far below any wall);
   - **(b) size/binaries** is the cause that actually choked gbrain (its "7,471-file/2.3GB wiki" was
     ~300KB/file = embedded media, NOT 7k text files). This design **structurally excludes it**:
     the sorting rule is plaintext→git, binary→`~/files`. 500k notes × ~5KB ≈ 2.5GB of well-delta-
     compressed text — fine;
   - **(c) flat directory** is solved by **subdirectory fanout** (`notes/<aa>/<slug>.md`) *within the
     one repo* — a filesystem hygiene step, not a reason to split repos.
   So **"git is the spine" holds unbent** — one repo, fanned out + tuned, binaries already elsewhere.
   **Multiple repos are an OPTIONAL, much-later lever**, not a day-one requirement — justified only by
   millions of files, or a desire to separate cadence/backup (e.g. a noisy auto-ingest feed) or do
   per-machine selective sync. Truth never moves into a DB.
2. **Keyword + metadata + graph:** SQLite **FTS5** (+ a `links`/typed-`edges` table, recursive-CTE
   multi-hop). Scales to millions of rows; stays one file.
3. **Vectors:** **LanceDB** (embedded, file-based, IVF-PQ disk ANN) — NOT sqlite-vec. Flat index at
   small N, auto/again to IVF-PQ as the table grows, so there is **no migration** between small and
   large — we build on LanceDB from day one. Embeddings via local EmbeddingGemma (ADR-005).
4. **Two-stage retrieval:** ANN candidate-gen (LanceDB) + BM25 (FTS5) → RRF → **local cross-encoder
   rerank** (e.g. `bge-reranker-v2-m3` via Ollama/llama.cpp) for precision at scale. The reranker
   is gbrain's zerank role, run locally.
5. **Indexing at volume:** batched + parallel + **resumable/checkpointed** embedding (initial 100k
   backfill is a multi-hour job — `op_checkpoint` pattern, incremental by file-hash already in
   `indexlib`); a file-watcher for live incremental; QAT-quantized embedder (~200MB) for throughput.
6. **Background work:** a resumable indexing/consolidate worker under launchd (single-node);
   escalate to a job queue only if multi-source/multi-machine (still out of scope).
**Why this keeps the philosophy at scale.** LanceDB + SQLite are BOTH embedded and file-based — so
100k–1M notes are served **single-machine with no server**, preserving principle 6. Markdown stays
truth and every index rebuilds from it (`rm -rf .index && ops index`), preserving principles 1–2 and
reversibility. We reach gbrain *capability* without gbrain's Postgres server — the embedded-ANN era
(LanceDB) is what makes that newly possible. And the storage spine does NOT bend: one git repo of
plaintext, fanned out and tuned, carries the whole scale (point 1) — gbrain's git pain was binary
*size*, which the plaintext→git / binary→`~/files` rule already prevents.
**What this explicitly reverses.** No more "at your scale you don't need it." ANN, two-stage
rerank, subdirectory fanout, and resumable bulk indexing are CORE from day one, brought up small on the
same architecture so there is never a re-platforming. **Status.** Architecture set; supersedes the
small-scale framing in ADR-002/003 and §10.2. **Stages 1–3 IMPLEMENTED** (`bin/lib/indexlib.py`,
`embed.py`, `vectorstore.py`, `rerank.py`; `ops index`/`search`): FTS5+graph → LanceDB ANN +
EmbeddingGemma (OPS_VECTORS=1) → fastembed cross-encoder rerank (OPS_RERANK=1), all embedded /
local / no-server, opt-in, rebuildable. Remaining: scale-out *plumbing* (repo sharding + resumable
batched backfill + file-watcher), which earns its keep only as the vault approaches 100k — the
architecture itself does not change.

## ADR-008 — Drop zero-knowledge sharing for capability URLs (2026-07-10)
**Context.** The operator's actual job with `ops share` is "paste one link into any chat/coding
agent and it reads the note" — no headers, no second URL, no local tooling. The shipped
zero-knowledge design (AES-256-GCM, key in the URL `#fragment`, PrivateBin pattern) cannot clear that
bar, because HTTP never sends `#fragment` to a server: a server-side agent-fetchable route
structurally cannot receive a fragment-only key. Every variant tried to bridge the gap failed the
same way or worse: `?k=<key>` query param (key lands in worker access logs and browser history),
`X-Ops-Share-Key` header (unusable by generic fetch tools that can't set custom headers), a second
`agent_url` printed alongside the human link (two-link contract — the exact ergonomics failure being
fixed), `ops share pull` local decrypt (requires `ops` installed — fails for "any chat/coding agent"),
and mechanical URL-math instructions for agents to derive the fetch URL themselves (fragile, another
thing to get wrong). See `docs/design/proposals/2026-07-10-ops-share-agent-markdown-url.md` §11.5 and
`docs/design/proposals/2026-07-10-capability-url-share.md` for the full exhausted-alternatives table.
**Decision.** Remove zero-knowledge encryption entirely (not kept as a flag). `ops share <slug>
--yes` now PUTs the plaintext OPSX bundle to the worker under a single 24-char unguessable token
(~124 bits, up from the old 10-char id). ONE link: the bare URL renders HTML in a browser; append
`.md` (or let content negotiation handle a bare non-browser fetch) and the same link returns raw wiki
markdown. `PUT /` additionally requires an `X-Publish-Token` when the `PUBLISH_TOKEN` wrangler secret
is set, so a discovered endpoint can't be abused as an anonymous file host. Links published under the
old encrypted model return `410` on every route — re-publish.
**Why.** Zero-knowledge and "one link an agent can fetch" are logically incompatible, not just
hard to engineer: a fragment is by definition never transmitted, so any route a server-side fetch
tool can use must carry the key somewhere the server (and therefore anyone with log access) can see
it — at which point ZK has already been given up in substance, and keeping the fragment charade only
costs a second URL. The content being shared is, by definition, content the operator chose to
publish (never `~/files`, never anything outside the explicit `ops share` invocation) — so "the
provider can technically read it" is a narrower exposure than it sounds, not a new category of risk.
An unguessable token over TLS with a TTL is exactly the trust model already accepted for the
`--gist` fallback (a GitHub secret gist); this makes the primary path match the trust model of the
fallback instead of promising a stronger property it can't structurally deliver.
**Status.** Implemented (this refactor: `bin/share/worker/worker.js`, `bin/lib/sharelib.py`,
`bin/share/run.py`). Requires a worker redeploy (`wrangler deploy` + `wrangler secret put
PUBLISH_TOKEN`) before publish/fetch routes reflect this ADR in production; `ops share init` prints
the exact steps.
