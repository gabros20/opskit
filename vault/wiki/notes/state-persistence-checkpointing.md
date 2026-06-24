---
type: note
title: State Persistence & Checkpointing
status: evergreen
created: 2026-01-09
updated: 2026-06-19
tags: [checkpointing, state-persistence, crash-recovery, langgraph, fault-tolerance, durable-execution]
aliases: [agent checkpointing, durable agent state]
---

Checkpointing saves agent state at strategic execution points, enabling resume-on-failure rather than full restart — like a video game save point. Production impact: **70–90% cost savings** and **99%+ recovery time reduction**.

**Five core use cases:** (1) crash recovery after API failures or OOM; (2) multi-day conversation resume; (3) human-in-the-loop pause-and-resume at approval gates; (4) time-travel debugging (fork from any past checkpoint); (5) multi-agent coordination via shared state.

**What to checkpoint:** conversation messages, current step + pending tool calls, completed step results, working memory entities, subgoal state (current + completed summaries), and metadata (threadId, userId, version, timestamp). Store only plain serializable data — no functions, no circular references.

**When to checkpoint:** LangGraph defaults to post-node boundaries (after each node completes). The **Young/Daly formula** gives the optimal frequency: `T = √(2Cμ)` where C = checkpoint cost and μ = mean time between failures. Practically: always before expensive LLM calls, before destructive actions, at phase transitions, before human approval gates. Target <5% overhead.

**Storage backends (LangGraph benchmarks):** In-memory (8,392 ops/sec, volatile) | SQLite (7,083 ops/sec, local) | **Redis 0.1.0** (2,950 ops/sec, 0.34ms — 12.4× faster gets than prior version) | PostgreSQL (1,038 ops/sec, most durable) | MongoDB (659 ops/sec). For parallel branches, Redis handles 100 branches in 846ms vs PostgreSQL's 1,959ms. **ByteCheckpoint** (ByteDance 2024) achieves 529× faster checkpoint saves for LLM training workloads.

**Restate** provides durable execution at the framework level — each `ctx.run()` step is automatically checkpointed and replayed on failure without manual retry logic.

**Recovery three-phase flow:** Load → validate schema → deserialize | Reconstruct in-memory structures + reconnect services | Continue from next step. LangGraph resumes automatically when the same `thread_id` is reused. Time-travel forks by specifying a past `checkpoint_id`.

**Key pitfalls:** shared thread IDs (data collision), ignoring checkpoint save errors (fail fast instead), checkpointing after destructive actions (too late), storing non-serializable state.

Part of [[memory]].

**Related:** [[memory-systems-working-memory]] | [[hierarchical-subgoal-memory]] | [[long-term-memory-retrieval]] | [[resilience-patterns]] | [[loop-control]] | [[approval-gates]] | [[observability]]
