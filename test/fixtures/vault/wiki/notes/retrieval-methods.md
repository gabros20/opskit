---
type: note
title: Retrieval Methods
status: evergreen
created: 2025-01-08
updated: 2026-06-19
tags: [retrieval, bm25, hybrid-search, hyde, query-decomposition, rag]
aliases: [RAG retrieval, search methods]
---

No single retrieval method handles all query types. Combining them via hybrid search improves recall by **15–30%** over any single approach.

**Core methods:**

- **Vector search (dense):** Embeds query and finds nearest neighbors. Excellent for semantic matching and synonyms; fails on exact codes, IDs, rare terms.
- **BM25 (sparse/keyword):** Probabilistic TF-IDF variant. Fast (inverted index), exact keyword matching, no ML needed. Misses synonyms. BM25S variant delivers 500x speedup with equivalent accuracy.
- **Fuzzy search:** Levenshtein/Damerau-Levenshtein edit-distance matching. Catches typos — 80% of typos are within 1 edit. Essential for user-facing search. Elasticsearch AUTO fuzziness: 0-2 chars exact, 3-5 chars 1 edit, 6+ chars 2 edits.
- **SPLADE (learned sparse):** Neural model producing sparse representations. 94% of BM25 speed, 98% of BERT accuracy. <4ms latency difference vs BM25.

**Query strategies:**

- **HyDE (Hypothetical Document Embeddings):** Generate a hypothetical answer with an LLM, embed that instead of the raw query. Retrieves better because generated text has richer terminology. Risk: wrong hypothetical → wrong retrieval; mitigate with ensemble.
- **Query decomposition:** Break complex multi-part questions into sub-queries, retrieve independently, aggregate. Combined with cross-encoder reranking yields the largest accuracy gains.
- **Query expansion:** Add synonyms, related terms, or LLM-generated alternatives.
- **Multi-query retrieval:** Generate 3–5 query variants, retrieve for each, deduplicate.

**Top-K patterns:**

| Application | Initial K | After Rerank |
|---|---|---|
| Chat / QA | 50–100 | 5–10 |
| Document search | 100–200 | 10–20 |
| Code search | 30–50 | 3–5 |

Retrieve-then-rerank: retrieve 100 candidates (50ms), cross-encoder rerank → top 10 (500ms). Precision: 94% vs 75% without reranking.

**MMR (Maximal Marginal Relevance):** `MMR = λ × Sim(doc, query) − (1−λ) × max(Sim(doc, retrieved_docs))`. Balances relevance and diversity; λ=0.5 is balanced.

Hybrid production default: BM25 top-50 + vector top-50 → RRF fusion (k=60) → rerank → 5–10 final results. Supports: Weaviate (built-in), Qdrant (sparse+dense), Elasticsearch (BM25+vector), Pinecone (sparse-dense indexes).

Part of [[rag]].

**Related:** [[vector-search-embeddings]] · [[hybrid-search-reranking]] · [[chunking-strategies]] · [[rag-architectures]] · [[long-term-memory-retrieval]] · [[context-management]]
