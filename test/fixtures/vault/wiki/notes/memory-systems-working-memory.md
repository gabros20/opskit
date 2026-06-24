---
type: note
title: Memory Systems & Working Memory
status: evergreen
created: 2026-01-09
updated: 2026-06-19
tags: [working-memory, agent-memory, coala, entity-extraction, context-management, token-optimization]
aliases: [agent RAM, in-session memory]
---

Memory is the boundary between stateless chatbots and coherent AI agents. LLMs are fundamentally stateless; without explicit memory infrastructure every interaction starts fresh.

The **CoALA** (Cognitive Architectures for Language Agents, TMLR 2024) framework defines four memory types: **Working** (volatile, current context), **Episodic** (past events), **Semantic** (factual knowledge), and **Procedural** (skills). Working memory is the agent's RAM — an in-memory buffer of recently extracted entities enabling reference resolution ("this page", "that entry") in sub-millisecond time.

Key benchmarks (2024–2025): **Mem0** (arXiv 2504.19413) achieves 26% accuracy improvement, 91% latency reduction (17.12s → 1.44s p95), and 93% token savings (26K → 1.8K tokens/conversation) vs full-context approaches. **A-MEM** (NeurIPS 2025) uses a Zettelkasten-inspired design for 85–93% fewer tokens and a multi-hop ROUGE-L score of 44.27 vs 18.09 baseline. Counterintuitively, **Letta** filesystem agents (74% LoCoMo accuracy) outperform complex graph memory systems (68.5%) — simpler tools familiar from training data often win.

**Implementation patterns:**
- **Sliding window (FIFO)** — keep last N entities; zero latency, simple but drops oldest indiscriminately.
- **Relevance-based eviction** — score by recency (0.6 weight) + frequency (0.4 weight); better for production.
- **Hybrid + summarization** — full detail for recent turns, compressed summary for older turns; handles unlimited conversation length.
- **Mem0-style** — extract entities and relations, detect conflicts, store in Vector DB + optional Graph DB for cross-session learning.

**Production rules of thumb:** size at 1–2 entities per turn (20–50 cap); store entity IDs, not full content; set TTL of 5–10 minutes; monitor fill rate (alert >95%) and eviction rate (alert >30%). Fallback path: working memory (0.2ms) → database (50–200ms).

Part of [[memory]].

**Related:** [[hierarchical-subgoal-memory]] | [[long-term-memory-retrieval]] | [[state-persistence-checkpointing]] | [[context-windows]] | [[token-optimization]] | [[agent-fundamentals]] | [[context-management]]
