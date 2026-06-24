---
type: note
title: Token Optimization & Context Compression
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [token-compression, llmlingua, context-window, cost-optimization, rag, agent-trajectories]
aliases: [context-compression, prompt-compression]
---

Token optimization reduces context size 60-90% while preserving 95%+ semantic accuracy through compression, importance scoring, lazy loading, and query-aware filtering — achieving $4,000+/month savings in production RAG systems and often improving response quality by eliminating noise.

## The Problem

Naive RAG loads full document corpora: 40,000+ tokens per request, scaling costs linearly. The "lost in the middle" paradox compounds this — at 32K tokens, 11/12 models dropped below 50% of short-context performance (NoLiMa benchmark). Compression breaks the cost-quality tradeoff by keeping only what is relevant to the current query.

## Compression Techniques

**LLMLingua family** (Microsoft, ACL 2024): coarse-to-fine token removal using perplexity scores from a small LM (XLM-RoBERTa 355M or GPT-2). LLMLingua-2 achieves 14× compression on GSM8K with 2-5% accuracy loss and runs 3-6× faster than v1, using 2.1 GB GPU vs 16.6 GB. LongLLMLingua adds +21.4% RAG accuracy at 1/4 tokens.

**Extractive summarization**: score sentences by cosine similarity to document centroid, select top N%. Fast, no LLM required, preserves exact wording. Best for technical docs (50-70% compression, very low quality impact).

**Abstractive summarization**: a fast model (GPT-4o-mini) rewrites content into compressed form. Best for conversation histories (70-80% compression). Risks hallucination and adds latency.

**AttentionRAG (2025)**: attention-pattern scoring achieves 6.3× compression, +10% over LLMLingua on LongBench.

## Agent-Specific Compression

**AgentDiet (2025)** reduces agent trajectory tokens 39.9-59.7% on SWE-bench with maintained or improved task performance via sliding window reflection and a separate compression LLM. **ACON (2025)** compresses observations and interaction histories with 26-54% memory reduction; enables Qwen3-14B to improve from 26.8% → 33.9% on AppWorld. **Observation masking** (JetBrains/NeurIPS 2025) often matches expensive LLM summarization at ~50% cost reduction — masking preserves "trajectory harshness" that helps agents recognize failure.

## Lazy Loading & Token Budgets

Two-tier fetching returns only metadata first; agents request full content on demand (70-90% token savings). Budget allocation per component prevents any single section from dominating a fixed context window (e.g., 8K: 1K system, 2K retrieved docs, 1.5K conversation, 500 buffer).

## Key Numbers

| Technique | Compression | Quality Impact |
|---|---|---|
| LLMLingua-2 | 14× | 2-5% loss |
| Query-aware RAG | 80-90% | Low (often improves) |
| AgentDiet | 40-60% | Maintained |
| Extractive (docs) | 50-70% | Very low |

Part of [[context]].

## Related Notes

- [[context-windows]] — prerequisite: token budget mechanics
- [[context-management]] — caching and window management strategies
- [[injection-strategies]] — where and how to place compressed context
- [[memory-systems-working-memory]] — working memory and trajectory compression
- [[rag-architectures]] — RAG pipeline where compression operates
- [[retrieval-methods]] — retrieval before compression
- [[optimization]] — cost and performance optimization in production
