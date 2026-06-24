---
type: note
title: Vector Search & Embeddings
status: evergreen
created: 2025-01-08
updated: 2026-06-19
tags: [vector-search, embeddings, semantic-search, hnsw, rag, embedding-models]
aliases: [semantic search, dense retrieval]
---

Vector embeddings transform text into dense numerical representations (512–3072 dimensions) where semantically similar content clusters together, enabling retrieval by meaning rather than exact keyword overlap. A query like "make app faster" can retrieve "performance optimization" despite zero keyword match.

**Embedding model landscape (2024–2025):**

| Model | Dims | Key note |
|---|---|---|
| OpenAI text-embedding-3-small | 1536 | $0.02/1M, cost-effective default |
| OpenAI text-embedding-3-large | 3072 | $0.13/1M, balanced |
| Voyage-3 | 1024 | +7.55% over OpenAI large, 2.2x lower cost |
| Voyage-3-lite | 512 | +3.82% over OpenAI large at 6.5x lower cost |
| BGE-M3 | 1024 | Self-hosted, dense+sparse+multi-vector, Apache 2.0 |
| Cohere embed-v4 | 1536 | Multimodal (text+images), 128K context |

**Similarity metrics:** Cosine similarity is the default for 85% of RAG. Dot product is equivalent for pre-normalized vectors and 2–3x faster. Wrong metric choice can degrade recall by 30–40%.

**Index types:**
- **Flat (brute force):** 100% recall, only suitable for <100K vectors.
- **HNSW:** <10ms latency, 95–99% recall, production default for <50M vectors. Parameters `M`, `ef_construction`, and `ef_search` trade memory/build time for recall.
- **DiskANN:** Billions of vectors, SSD-backed, ~40x cheaper infrastructure than HNSW at scale. Azure PostgreSQL DiskANN went GA October 2024; NVIDIA cuVS provides 40x GPU speedup.

**Advanced techniques:**
- **Matryoshka (MRL):** Truncate 3072→512 dims with only 3–5% accuracy loss, 6x storage savings.
- **Late chunking (Jina AI 2024):** Embed full document first, then chunk embeddings — preserves 15–25% more cross-chunk context (arXiv:2409.04701).
- **ColBERT / multi-vector:** One vector per token; MaxSim scoring gives token-level precision.

Production checklist: batch embed (40x faster), normalize vectors, monitor for embedding drift on model updates, use HNSW with defaults before tuning.

Part of [[rag]].

**Related:** [[chunking-strategies]] · [[retrieval-methods]] · [[hybrid-search-reranking]] · [[embedding-models]] · [[vector-similarity]] · [[dimensionality]]
