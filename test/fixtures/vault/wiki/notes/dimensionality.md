---
type: note
title: Dimensionality Trade-offs
status: evergreen
created: 2025-12-03
updated: 2026-06-19
tags: [dimensionality, embeddings, pca, hnsw, vector-compression]
aliases: [Embedding Dimensions, Vector Dimensionality]
---

Embedding dimensionality — the number of float32 values per vector — controls the accuracy-cost-latency triangle for vector search. More dimensions capture more semantic nuance, but storage and search time scale linearly and ANN index quality degrades.

## Accuracy vs. dimensions (MTEB)

| Dims | MTEB Accuracy | Improvement |
|------|---------------|-------------|
| 128 | 52.3 % | Baseline |
| 384 | 61.4 % | +9.1 % |
| 768 | 63.8 % | +11.5 % |
| 1536 | 64.6 % | +12.3 % |
| 3072 | 65.1 % | +12.8 % (diminishing!) |

**Accuracy plateaus at ~1536 dimensions.** Beyond that, 2× cost for < 3 % gain.

## Storage and latency (linear scaling)

1 vector @ float32 = dims × 4 bytes. 1536 dims → 6 KB/vector → 6 GB/1M vectors. Cosine search over 100k vectors: 384 dims ≈ 20 ms · 1536 dims ≈ 80 ms · 3072 dims ≈ 160 ms.

**Curse of dimensionality**: in very high dimensions, all pairwise distances converge (std/mean drops from 0.34 in 2D to 0.034 in 1000D). HNSW recall falls from 98 % at 384 dims to 85 % at 3072 — meaning higher dimensions can actually hurt ANN performance.

## Dimensionality reduction options

**OpenAI flexible dimensions** (best): `dimensions: 512` in the API request — no post-processing, built into the model. 3× smaller, ~2–3 % accuracy loss. Available on text-embedding-3-small/large.

**PCA** (fast, linear): `sklearn.decomposition.PCA(n_components=384)`. 4× faster search, ~5 % accuracy loss. Must fit on corpus first.

**UMAP** (better quality, slower): preserves non-linear structure, 20× slower to fit than PCA. Use when PCA distorts cluster structure.

**Quantization**: combine reduced dims (768) + int8 quantization → 8× total storage reduction, ~7 % accuracy loss. Needed for > 1M vectors.

## Production sweet spots

| Use Case | Dims | Notes |
|----------|------|-------|
| Real-time < 10 ms | 256–384 | Mobile, edge |
| Standard RAG | 768–1536 | Best balance |
| Critical accuracy | 1536–3072 | Legal, medical |
| > 1M vectors | 384–768 + compression | Storage budget |

Benchmark on your actual queries before choosing — generic MTEB numbers may not reflect your domain.

Part of [[foundations]].

**Related:** [[embedding-models]] · [[vector-similarity]] · [[vector-search-embeddings]] · [[chunking-strategies]] · [[tradeoffs]]
