# Decisions log — Personal OS design

Append-only ADR log for the *design itself* (the §8.2 pattern, applied to this design repo).
Each entry: context → decision → why → status. Newest at the bottom. Appendix A / A.1 in
`PERSONAL_OS_DESIGN_v2.md` holds the per-merge table; this log holds the load-bearing "why".

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
  local Ollama, per ADR-003 (NOT a server).

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
**Status.** Decided.

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
