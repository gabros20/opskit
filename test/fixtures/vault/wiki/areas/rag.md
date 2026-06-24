---
type: area
title: Rag
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [rag, retrieval, embeddings, vector-search, hybrid-search, evaluation]
---

Retrieval-Augmented Generation (RAG) is the dominant pattern for grounding LLM responses in external knowledge. Rather than relying on model weights alone, RAG retrieves relevant document chunks at query time and injects them into the prompt, enabling up-to-date, source-cited, and hallucination-reduced answers. The market reached $1.85B in 2024 at 49% CAGR, reflecting enterprise-wide adoption.

The pipeline has three tightly coupled stages. First, documents are chunked and embedded into a vector index — the right chunking strategy alone accounts for up to 67% variance in retrieval failure rate. Second, queries are executed against the index using hybrid retrieval: BM25 for exact keyword matches fused with dense vector search via Reciprocal Rank Fusion (k=60), improving recall 15–30% over any single method. A cross-encoder reranker (Cohere Rerank, BGE-reranker-v2-M3) then reorders the top-50–100 candidates for a further 20–35% precision gain. Third, retrieved chunks are ordered strategically (sandwich pattern to combat "lost in the middle") and optionally compressed 50–70% before injection into the LLM prompt.

Architecture complexity scales with query difficulty. Naive RAG (single retrieval pass) works for prototypes. Advanced RAG (pre-retrieval query rewriting, hybrid search, post-retrieval reranking + compression) is the production default and handles 80% of use cases. Agentic RAG (Self-RAG, CRAG, multi-agent loops) adds self-correction for multi-hop reasoning at 5–10x higher cost. GraphRAG builds LLM-extracted knowledge graphs and community summaries for corpus-wide aggregation queries (+76% on global summarization). Reasoning-based RAG (PageIndex) replaces the vector DB with an in-context hierarchical tree index the LLM navigates directly, achieving 98.7% on FinanceBench.

Production RAG demands systematic evaluation from day one. The RAGAS framework defines the key metrics: faithfulness >0.90, answer relevancy >0.85, context precision >0.80, context recall >0.85, NDCG@10 >0.80. LLM-as-Judge (GPT-4) correlates 0.85+ with human judgment at a fraction of the cost. LLM tokens represent 95%+ of per-query cost; context compression, query routing to cheaper models, and prompt caching are the primary levers for cost reduction. 70% of RAG systems lack evaluation — measure before optimizing.

## Timeline

- 2026-06-19 Imported 6 notes from the source KB.

## Notes

- [[vector-search-embeddings]]
- [[chunking-strategies]]
- [[retrieval-methods]]
- [[hybrid-search-reranking]]
- [[rag-architectures]]
- [[rag-operations]]
