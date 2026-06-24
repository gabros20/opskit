---
type: note
title: Vector Similarity Metrics
status: evergreen
created: 2025-12-03
updated: 2026-06-19
tags: [cosine-similarity, dot-product, euclidean, vector-search, embeddings]
aliases: [Vector Distance Metrics, Similarity Functions]
---

Once text is embedded as vectors, similarity between two vectors is computed with a metric. Choosing the wrong one silently degrades search quality. For text embeddings, **cosine similarity** is the standard.

## The four metrics

**Cosine Similarity** — measures the angle between vectors, ignoring magnitude. Formula: `(A · B) / (||A|| × ||B||)`. Range: −1 (opposite) to 1 (identical). Magnitude-invariant: "cat sleeps" and "cat sleeps softly" (one being 2× the other in magnitude) score 1.0 — correct for text.

**Dot Product** — measures direction AND magnitude combined: `Σ aᵢ × bᵢ`. Range: −∞ to +∞. For L2-normalized vectors (||v|| = 1), dot product = cosine similarity — but 3× faster (no square root). Prefer dot product when vectors are pre-normalized.

**Euclidean Distance** — straight-line distance in space: `√Σ(aᵢ − bᵢ)²`. Range: 0 to ∞ (smaller = more similar). Sensitive to magnitude; penalizes longer documents unfairly. Suffers from the curse of dimensionality in high dims.

**Manhattan Distance** — grid-like distance: `Σ|aᵢ − bᵢ|`. No square root → fast. More robust to outliers. Better for sparse or high-dimensional data.

## Metric selection guide

| Situation | Metric | Reason |
|-----------|--------|--------|
| Text embeddings | Cosine Similarity | Ignores document length |
| Normalized vectors + speed | Dot Product | Equivalent, 3× faster |
| Spatial / image data | Euclidean | Position matters |
| Sparse / high-dim data | Manhattan | Robust, efficient |

## Score interpretation (cosine)

> 0.9: excellent match · 0.7–0.9: good · 0.5–0.7: weak · < 0.5: likely irrelevant.

## Production practices

Pre-normalize at index time, use dot product at query time (3× speedup). Match the metric your embedding model was trained with — OpenAI and SBERT use cosine. Never mix normalized and unnormalized vectors in the same index. Monitor score distributions: average similarity < 0.3 across top-100 results signals a bad embedding or wrong metric.

**HNSW impact**: ANN recall degrades at very high dimensions: 98 % recall at 384 dims → 85 % at 3072.

Part of [[foundations]].

**Related:** [[embedding-models]] · [[dimensionality]] · [[vector-search-embeddings]] · [[retrieval-methods]] · [[hybrid-search-reranking]]
