---
type: note
title: Cost & Performance Optimization
status: evergreen
created: 2026-01-27
updated: 2026-06-19
tags: [cost-optimization, model-routing, prompt-caching, semantic-caching, batching, llm-ops]
aliases: [LLM cost optimization, token efficiency]
---

Production deployments consistently achieve 40–90% cost reduction through systematic optimization without sacrificing quality. The core principle: not every request needs your most expensive model. Route intelligently, cache aggressively, batch where possible.

Part of [[production]].

## The Six-Layer Optimization Stack

| Layer | Technique | Savings |
|-------|-----------|---------|
| 1 | Model routing (simple → cheap) | ~60% on routed subset |
| 2 | Prompt caching (static prefix) | 50–90% on input tokens |
| 3 | Semantic caching (similar queries) | 68% API call reduction |
| 4 | Batching (async workloads) | 50% discount |
| 5 | Token optimization (compression, lazy load) | 20–40% token reduction |
| 6 | Index infrastructure (Merkle trees + content hash) | 15–690x faster updates |

Combined in production case studies: **82% total cost reduction** (e.g., $6,000 → $1,080/month for 1M customer-support queries).

## Model Routing

**RouteLLM** (open-source): 85% cost savings while retaining 95% GPT-4 quality. Route 70% simple tasks to GPT-4o-mini ($0.15/1M input) vs GPT-4o ($2.50/1M) — 16x price difference. Routing strategies: rule-based (<1ms, 70–80% accuracy), embedding similarity (10–20ms, 85–90%), small LLM classifier (50–100ms, 90–95%).

## Prompt Caching

Place static content (system prompt, few-shot examples) at the START of the prompt; vary dynamic content at the END. Provider discounts: Anthropic 90% off (min 1024 tokens, TTL 5 min), OpenAI 50% (24h), Google 75%. Monitor `cacheReadTokens` metric to track hit rate. Also reduces latency.

## Semantic Caching

Embed the query, vector-search a cache, return cached response if cosine similarity > threshold. **SCALM architecture** achieves 63% better hit ratio vs GPTCache. Recommended threshold: 0.90–0.95 (medium hit rate, good accuracy). Exclude personalized/stateful queries. Risk: stale answers — implement cache invalidation for changing data.

## Batching

OpenAI and Anthropic batch APIs offer 50% discount with up to 24h turnaround. Only suitable for async workloads: nightly reports, content summarization, data enrichment, training data prep. LexisNexis case study: 4x faster processing, 35% cost reduction, 95% GPU utilization.

## Token Efficiency Techniques

- **LLMLingua** (Microsoft): up to 20x prompt compression, <5% quality loss
- **Lazy context loading**: give agents tools to fetch on demand rather than loading all documents upfront (40–60% reduction for multi-step tasks)
- **Prompt trimming**: removing verbose filler can cut 83% of system-prompt tokens with same effectiveness

## Index Infrastructure (Cursor 2025)

For large codebases: **Merkle tree differential sync** re-embeds only changed files (15x faster median, 690x faster at p99 for large repos). **Content-addressable embedding cache**: sha256(chunk_content) as key — unchanged code always hits cache, deterministically. **Simhash deduplication**: 92% content overlap among org clones means new team members reuse existing indexes (4 hours → 21 seconds). **Syntactic code chunking**: split by AST boundaries, not token counts.

## Autonomous Agent Cost Caveat

Autonomous agents have sustained (not spiky) token consumption. Provision explicit token budgets; enforce wall-clock timeouts, max-step caps, and per-task accounting rather than per-call rationing.

## Related Notes

- [[observability]] — measure baseline costs before optimizing
- [[debugging]] — debugging informs which paths to optimize
- [[context-windows]] — context length directly drives token cost
- [[token-optimization]] — complementary token compression techniques
- [[context-management]] — caching and context reuse strategies
- [[tradeoffs]] — cost-latency-quality triangle
- [[retrieval-methods]] — retrieval efficiency affects RAG costs
