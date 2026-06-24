---
type: note
title: Long-Term Memory & Retrieval
status: evergreen
created: 2026-01-09
updated: 2026-06-19
tags: [long-term-memory, vector-database, hybrid-search, knowledge-graph, mem0, retrieval]
aliases: [persistent agent memory, cross-session memory]
---

Long-term memory lets agents persist facts, preferences, and experiences across sessions. Without it, every new session starts from scratch. With it, token costs drop ~90% and latency ~91% compared to passing full conversation history.

**Vector database flow:** text → embedding model (e.g., `text-embedding-3-small`, 1536 dims) → HNSW or IVF index → cosine similarity search at query time. Key databases (2025): **LanceDB** (<20ms, OSS, embedded, best for <10M vectors); **Qdrant** (<5ms, self-hosted, high performance); **Pinecone** (<50ms, managed SaaS, $70+/mo); **pgvector** (30–100ms, good for existing Postgres stacks); **Weaviate** (hybrid search focus).

**Hybrid search (BM25 + vector)** consistently outperforms either method alone: **+42% NDCG** over vector-only and **+28% NDCG** over BM25-only (Weaviate 2025). **Reciprocal Rank Fusion (RRF, k=60)** merges the two ranked lists. **HyDE** (Hypothetical Document Embeddings) bridges the gap between short queries and long documents by embedding a generated hypothetical answer instead of the raw query.

**Knowledge graphs for relationships:** **Mem0** (arXiv 2504.19413) extracts entities and relations, detects conflicts, and stores to Vector DB + optional Neo4j graph. **Graphiti/Zep** uses bi-temporal modeling (four timestamps per edge: transaction time + event time) to track fact validity; achieves 94.8% accuracy on Deep Memory Retrieval at 300ms P95 with no LLM calls during retrieval. Critical finding (FalkorDB 2025): vector accuracy drops to **0%** on queries involving 5+ entities — graph traversal is essential for multi-hop reasoning.

**Benchmark summary:** Graphiti/Zep 94.8% | Letta filesystem 74.0% | Mem0 graph 68.5% | Mem0 vector 66.9% | Full context 61% | OpenAI Memory 52.9%.

**Three-tier production architecture:** Tier 1 Redis (session, <5ms) → Tier 2 Vector DB (user facts, <50ms) → Tier 3 cold storage (archive, <500ms).

**Cost tips:** batch embeddings (10× savings); use namespaces per user (faster than metadata filters); `text-embedding-3-small` is best cost/quality; BGE-M3 is free and excellent.

Part of [[memory]].

**Related:** [[memory-systems-working-memory]] | [[hierarchical-subgoal-memory]] | [[state-persistence-checkpointing]] | [[vector-search-embeddings]] | [[hybrid-search-reranking]] | [[embedding-models]] | [[retrieval-methods]]
