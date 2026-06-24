---
type: note
title: RAG Architectures
status: evergreen
created: 2026-01-27
updated: 2026-06-19
tags: [rag, agentic-rag, graphrag, self-rag, architecture, knowledge-graphs]
aliases: [RAG patterns, retrieval-augmented generation architectures]
---

RAG has evolved through distinct paradigms, each adding capability at the cost of latency and complexity. Choose based on query type, accuracy requirements, and cost tolerance.

**Architecture overview:**

| Architecture | Accuracy gain | Latency | Cost/query | Best for |
|---|---|---|---|---|
| Naive RAG | ~25% baseline | 1–2s | $0.01 | Prototypes, simple factoid |
| Advanced RAG | +30–50% | 2–4s | $0.05 | Production default |
| Agentic RAG | +40% | 5–15s | $0.10–0.50 | Multi-hop reasoning |
| GraphRAG | +76% summarization | High | High | Global corpus queries |
| Reasoning-Based (PageIndex) | 98.7% on FinanceBench | Medium | Medium | Structured long docs |

**Naive RAG:** Embed query → vector search top-k → inject into prompt → generate. Fastest, cheapest. No mechanism to detect or fix retrieval failures.

**Advanced RAG** adds three phases:
- *Pre-retrieval:* Query rewriting, HyDE, decomposition into sub-queries.
- *Retrieval:* Hybrid search (BM25 + vector, RRF k=60).
- *Post-retrieval:* Cross-encoder reranking, context compression (50–70% token reduction), citation extraction.

**Agentic RAG** — LLM drives an iterative retrieve-evaluate-refine loop:
- **Self-RAG (2023):** Single model with reflection tokens `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]`. Adaptively decides if retrieval is needed. +40% over standard RAG.
- **CRAG (2024):** 0.77B-param evaluator routes to: use retrieved docs (confidence >0.8), web search fallback (<0.3), or combined approach (0.3–0.8). 67% fewer failures with reranking.
- **Multi-agent RAG:** Orchestrator coordinates specialized agents (web, document, code, synthesis).
- Quality gates prevent runaway loops: max 5 iterations, 30s timeout, 0.7 confidence threshold.

**GraphRAG (Microsoft 2024):** LLM extracts entities → builds knowledge graph → detects communities → pre-generates community summaries. Queries map to communities for global sensemaking. 76% improvement on summarization queries. Open source: `github.com/microsoft/graphrag`.

**Reasoning-Based RAG / PageIndex (2025):** Replaces vector DB with an in-context hierarchical tree index (Table of Contents JSON). LLM *reasons* over structure, navigates cross-references ("See Appendix G"), and iterates. Achieved 98.7% on FinanceBench vs substantially lower for vector RAG. Use for structured long documents; too slow for high-volume low-latency workloads.

**Selection rule:** Start with Advanced RAG. Add Agentic capabilities incrementally after measuring failure modes. Use GraphRAG only for corpus-wide aggregation queries.

Part of [[rag]].

**Related:** [[hybrid-search-reranking]] · [[retrieval-methods]] · [[rag-operations]] · [[react-pattern]] · [[agent-fundamentals]] · [[plan-and-execute]] · [[orchestration-patterns]]
