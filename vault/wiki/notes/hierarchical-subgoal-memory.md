---
type: note
title: Hierarchical & Subgoal Memory
status: evergreen
created: 2026-01-09
updated: 2026-06-19
tags: [hierarchical-memory, subgoal, context-compression, hiagent, long-horizon-tasks, token-optimization]
aliases: [HiAgent memory, subgoal-based memory]
---

Flat action-observation histories cause context overflow, cost spirals, and "lost in the middle" accuracy drops (90% → 60% at >80% context capacity). Hierarchical memory solves this by organizing agent memory around **subgoals** — intermediate objectives that chunk a complex task into phases.

**HiAgent** (ACL 2025) is the canonical reference: completed subgoals are compressed to one-sentence summaries (~40 tokens) while the active subgoal retains full action detail (~100 tokens). Across five long-horizon benchmarks the approach doubles the success rate (21% → 42%) and reduces context tokens by 35% (5,000 → 3,250) with a 10:1 compression ratio. Average steps also drop 27% (14.2 → 10.4).

The three-component architecture: (1) **Subgoal Generator** — decomposes the task into the next logical chunk; (2) **Action Generator** — selects the next action given current subgoal + recent actions only; (3) **Summarizer** — collapses completed subgoals into outcome-focused one-liners.

**Compression strategies:**
- **Outcome-focused summarization** — store conclusions, not raw reasoning traces.
- **SimpleMem recursive consolidation** — three-stage entropy-aware pipeline achieving 30× token reduction with +26.4% F1.
- **ReadAgent gist memories** — segment → compress → lookup-on-demand; provides 3.5–20× effective context extension.

**Subgoal detection:** LLM-based achieves ~95% accuracy; heuristic (keyword matching on observations) hits 60–70%; hybrid (heuristic first, LLM fallback) is recommended for production.

**Sizing guidelines:** target 3–7 actions per subgoal; compress at 80% context capacity (force partial compression if stuck); archive every 10 subgoals into phase summaries for 50+ subgoal tasks. Multi-level hierarchy: Level 0 full actions → Level 1 subgoal summaries (10:1) → Level 2 phase summaries (50:1) → Level 3 task overview (100:1).

**Use when:** tasks exceed 10 actions, context must stay bounded, subgoal structure is natural. Skip for short tasks (<5 actions), real-time requirements, or highly interconnected context.

Part of [[memory]].

**Related:** [[memory-systems-working-memory]] | [[long-term-memory-retrieval]] | [[state-persistence-checkpointing]] | [[loop-control]] | [[token-optimization]] | [[plan-and-execute]] | [[context-management]]
