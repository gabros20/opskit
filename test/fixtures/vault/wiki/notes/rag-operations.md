---
type: note
title: RAG Operations
status: evergreen
created: 2025-01-08
updated: 2026-06-19
tags: [rag, evaluation, ragas, observability, cost-optimization, context-compression]
aliases: [RAG eval, RAG monitoring]
---

Building RAG is easy; operating it in production is hard. Two challenges dominate: **context optimization** (poor ordering → up to 30% accuracy drop) and **evaluation** (70% of RAG systems lack systematic evaluation frameworks).

**Lost in the Middle (Liu et al. 2024):** LLMs attend most strongly to context beginning and end. Information buried in the middle degrades performance by up to 30%. Llama-3.1-405B degrades after 32K tokens; GPT-4-0125 after 64K.

**Context ordering strategies:**
- *Relevance-first:* Highest similarity score at position 1.
- *Sandwich pattern:* Most relevant first, second-most relevant last, rest in middle — exploits primacy and recency effects.
- *Diversity-aware:* Alternate high-relevance with complementary docs to reduce redundancy.

**Context compression:** 50–70% token reduction with <5% accuracy loss.
- *Extractive:* Keep highest-query-relevance sentences. Fast, deterministic. 40–60% reduction.
- *LLM summarization:* Higher quality, 60–80% reduction, adds latency/cost.
- *Token budget allocation:* Allocate tokens proportionally to relevance score.

LLM input is 95%+ of total query cost. A typical RAG query costs ~$0.056 — $0.04 of that is LLM input tokens.

**RAGAS evaluation framework (EACL 2024):**

| Metric | Target | What it measures |
|---|---|---|
| Faithfulness | >0.90 | Answer claims supported by retrieved context |
| Answer Relevancy | >0.85 | Answer addresses the question |
| Context Precision | >0.80 | Fraction of retrieved chunks that are relevant |
| Context Recall | >0.85 | Fraction of needed info that was retrieved |
| NDCG@10 | >0.80 | Ranking quality with position discount |
| MRR | >0.70 | Rank of first relevant result |

**LLM-as-Judge:** GPT-4 evaluation correlates 0.85+ with human judgment at 10–100x lower cost. Evaluate correctness, completeness, and groundedness per query.

**Cost levers:**
- Context compression: −50–70% LLM input cost.
- Query routing: Route 60% of simple queries to cheaper models → ~50% cost reduction.
- Semantic caching: ~20% of queries repeat; cache hits cost ~$0.0001.
- Prompt caching (Anthropic): Up to 90% discount on repeated system prompt portions.

**Observability tools:** LangSmith (LangChain native), Arize Phoenix (open-source), TruLens (RAGAS-integrated), Weights & Biases. Log per query: retrieval method + latency, doc counts, top score, generation model + tokens, faithfulness + relevancy scores.

Production checklist: build 100+ eval pairs before deploying, set alert thresholds, implement user feedback loops, gracefully degrade when retrieval confidence is low, version all components (embedding model, chunking config, prompts) to enable rollback.

Part of [[rag]].

**Related:** [[rag-architectures]] · [[hybrid-search-reranking]] · [[observability]] · [[optimization]] · [[context-management]] · [[token-optimization]] · [[resilience-patterns]]
