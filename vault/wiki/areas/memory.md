---
type: area
title: Memory
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [memory, agent-state, working-memory, long-term-memory, checkpointing, context-management]
---

Memory is what separates coherent AI agents from stateless chatbots. The CoALA framework (TMLR 2024) defines the canonical four-type model: Working (volatile, in-session), Episodic (past events), Semantic (persistent facts), and Procedural (skills). Practical implementations stack these layers — working memory for sub-millisecond reference resolution within a session, long-term vector/graph stores for cross-session personalization, and state checkpoints for fault tolerance during long-running tasks.

For in-session use, **working memory** functions as the agent's RAM: a small buffer of recently extracted entities (typically 20–50 items) that enables natural reference resolution ("this page", "that entry") without hitting the database. Mem0 benchmarks show this approach yields 91% latency reduction and 93% token savings versus full-context approaches. Counterintuitively, simple filesystem-based agents (Letta, 74% LoCoMo accuracy) can outperform complex graph memory systems, suggesting that tools familiar from training data outperform novel memory abstractions.

**Hierarchical subgoal memory** is the dominant pattern for long-horizon tasks. By compressing completed subgoals to one-sentence outcomes and retaining full detail only for the active subgoal, HiAgent (ACL 2025) doubles task success rates while cutting context size 35%. The optimal subgoal granularity is 3–7 actions with a 10:1 compression ratio; multi-level hierarchies extend this to 50+ subgoal tasks.

**Long-term retrieval** combines vector databases (semantic similarity via HNSW indices) with optional knowledge graphs (multi-hop relationship traversal). Hybrid search — BM25 plus vector with Reciprocal Rank Fusion (RRF) — consistently outperforms either method by 28–42% NDCG. For relationship-heavy queries, graph memory (Graphiti/Zep temporal knowledge graph, 94.8% accuracy) is essential; pure vector approaches fail completely (0%) on queries involving 5+ entities. **State persistence and checkpointing** rounds out the area: saving agent state at strategic boundaries (before expensive LLM calls, at phase transitions, before human approval gates) reduces recovery time by 99%+ and API costs by 70–90%, with Redis (2,950 ops/sec, 0.34ms) the preferred backend for high-concurrency workloads.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[memory-systems-working-memory]]
- [[hierarchical-subgoal-memory]]
- [[long-term-memory-retrieval]]
- [[state-persistence-checkpointing]]
