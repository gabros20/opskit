---
type: note
title: Hybrid Search & Reranking
status: evergreen
created: 2025-01-08
updated: 2026-06-19
tags: [hybrid-search, reranking, rrf, cross-encoder, cohere, bge, two-stage-retrieval]
aliases: [two-stage retrieval, RRF fusion]
---

Two-stage retrieval — fast broad retrieval followed by precise reranking — is the 2024–2025 production standard for RAG. Hybrid fusion of BM25 + vector yields **15–30% better recall**; cross-encoder reranking adds **20–35% precision improvement** on top.

**The score fusion problem:** BM25 scores (12.4) and cosine similarities (0.89) are incomparable. Naive averaging or normalization degrades quality.

**Fusion strategies:**

- **RRF (Reciprocal Rank Fusion):** `RRF_score(doc) = Σ 1/(k + rank)`. Uses rank position only — immune to score scale differences. k=60 is the universal default; grid search on domain data can yield +10% F1.
- **RSF (Relative Score Fusion):** Normalize scores within each method, then combine with weight α. Default in Weaviate v1.24+. Retains score granularity but requires tuning.
- **Weighted fusion:** Manual weights (e.g., 0.6 BM25 + 0.4 vector for legal docs). Requires validation data.
- **Three-way hybrid (IBM 2024):** BM25 + dense vector + SPLADE sparse neural → RRF → optional ColBERT rerank. Best recall configuration.

**Reranker comparison (2024–2025):**

| Model | Latency | Cost | Notes |
|---|---|---|---|
| Cohere Rerank v3.5 | ~600ms | $$ | Market leader; Rerank 4 (Dec 2024) quadrupled context window |
| BGE Reranker v2-M3 | ~800ms | $ | Best open-source, Apache 2.0, multilingual |
| ColBERTv2 | ~30ms | $ | Pre-computed doc vectors, fastest reranking |
| SPLADE-v3 | ~10ms | $ | First-stage enhancement |
| LLM rerankers | 4–6s | $$$$ | Only +5–8% accuracy; avoid in production |

**Jina-ColBERT-v2 (Aug 2024):** 89 languages, 8192 tokens, Matryoshka-flexible dimensions. ColBERT MaxSim scoring: `Σ max(qi · dj)` for all query tokens — enables 30ms reranking because document vectors are pre-computed.

**Two-stage pipeline:**
- Stage 1 (50–100ms): BM25 top-100 + vector top-100 → RRF → 100 candidates.
- Stage 2 (500–1500ms): Cross-encoder scores all 100 → return top 5–20.
- **Sweet spot:** Rerank 50–75 documents.

Performance benchmark (bge-reranker-base): Hit Rate 0.854 → 0.895 (+4.1pp), MRR 0.640 → 0.708 (+6.8pp). Pinecone reports 48% retrieval quality improvement.

Conditional reranking: skip if top score >0.95. Cache results by `hash(query + sorted(candidate_ids))`. Batch reranking is 10x faster than single-document calls.

Part of [[rag]].

**Related:** [[retrieval-methods]] · [[vector-search-embeddings]] · [[rag-architectures]] · [[rag-operations]] · [[observability]] · [[optimization]]
