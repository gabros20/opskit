---
type: note
title: Embedding Models & Vector Spaces
status: evergreen
created: 2025-12-03
updated: 2026-06-19
tags: [embeddings, vector-search, semantic-search, rag, sbert]
aliases: [Text Embeddings, Semantic Vectors]
---

Embeddings are dense, fixed-size vectors that map text to a high-dimensional space where semantic similarity corresponds to geometric proximity. "King" and "monarch" end up near each other; "car" and "airplane" do not. This enables semantic search, RAG retrieval, clustering, and classification without exact string matching.

## How embeddings work

Text → tokenization → embedding model (encoder-only Transformer, trained with contrastive learning) → fixed-size dense vector (384–3072 dimensions). Properties: dense (no zeros), fixed-size, learned, semantic. Analogy: GPS coordinates for meaning.

## 2025 model landscape (MTEB benchmark)

| Model | Dims | Cost/1M | Strength |
|-------|------|---------|----------|
| Voyage-3-large | 1024 | $0.18 | MTEB retrieval leader |
| text-embedding-3-large | 3072 | $0.13 | General-purpose |
| text-embedding-3-small | 1536 | $0.02 | Cost-effective |
| Cohere Embed v3 | 1024 | $0.10 | 100+ languages |
| all-MiniLM-L6-v2 | 384 | Free | Fast, local |
| BGE-large-en-v1.5 | 1024 | Free | Best open-source |

**Critical caveat**: MTEB results are self-reported and often inflated by fine-tuning on MTEB datasets. Always validate on your actual production queries.

## Hybrid search (best practice)

Combine vector search (semantic, 70 % weight) with keyword/BM25 search (exact, 30 % weight). Merge results by boosting items appearing in both. Handles both "contact form" → "Get in Touch" (semantic) and exact slug lookups (keyword).

## Deployment patterns

**API (OpenAI/Voyage)**: no infrastructure, multilingual, high quality, $0.02–$0.18/1M. **Self-hosted (SBERT via `@xenova/transformers`)**: free, private, < 10 ms latency, but English-focused and lower quality. **Flexible dimensions (OpenAI)**: request `dimensions: 512` on text-embedding-3-small for 3× smaller vectors with ~2–3 % accuracy loss.

## Production rules

Cache all embeddings (Redis or DB, 24h TTL): 1M re-queries → $0 vs $20 recalculation. Chunk text before embedding; 8191-token limit (truncation is silent). Normalize text before embedding (lowercase, collapse whitespace) for consistency. Never compare embeddings from different models — they inhabit different vector spaces.

Part of [[foundations]].

**Related:** [[tokenization]] · [[vector-similarity]] · [[dimensionality]] · [[vector-search-embeddings]] · [[chunking-strategies]] · [[hybrid-search-reranking]]
