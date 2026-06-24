---
type: note
title: Coordination Strategies
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [multi-agent, coordination, parallel-execution, langgraph, scheduling]
aliases: [agent coordination, workflow coordination]
---

Coordination strategies govern how agents execute relative to each other. Modern frameworks model coordination as **graphs** (LangGraph `StateGraph`): nodes are agents, edges define execution flow — sequential, conditional, parallel fan-out, or cyclic.

**Key numbers**: Supervisor pattern improves performance by 50% over flat collaboration; parallel execution reduces latency by 60–70% for independent tasks. GPT-4o-mini achieves 84.13% task scores with graph-based coordination.

## Four Primary Patterns

**Sequential (Pipeline)**: A → B → C. Each stage depends on the previous output. Simple to debug; no parallelism; single point of failure. Use for data transformation, approval workflows, or iterative refinement loops.

**Parallel (Fan-Out / Fan-In)**: Init node spawns workers simultaneously (`Promise.all` in TypeScript, multiple edges from one node in LangGraph), then aggregator synthesizes results. Strategies: LLM synthesis, majority voting, concatenation, or structured merge. 60–70% latency reduction; requires an aggregation strategy; higher peak resource usage.

**Hierarchical (Manager-Worker)**: Supervisor creates a plan, team leads coordinate workers in parallel, leads synthesize, supervisor creates final response. Scales to many agents; natural domain boundaries; multiple latency hops.

**Peer-to-Peer (Negotiation)**: Agents share proposals, critique each other, then vote or reach consensus. **Contract Net Protocol**: manager announces task, agents bid (effort + confidence), highest-confidence bid wins. No single point of failure; harder to debug; may not converge.

## LangGraph Coordination Primitives

- `add_edge` for sequential flow
- Multiple edges from one node for parallel fan-out
- `add_conditional_edges` + router function for dynamic routing
- Cycles via `add_edge(refine, generate)` with a `should_continue` conditional (max iterations or quality threshold)
- **Subgraph composition**: compile team graphs and embed them as nodes in a main graph

## Task Scheduling: Triage Pattern

Priority = `(Value / Effort) × Urgency × Risk`. Aging boost (+0.1/hour waiting) prevents starvation; after 4 hours, a fixed +5 boost applies. Preemption fires when new task priority exceeds 2× current task. Strategies: priority queue (default), round robin, quota reservation, deadline-driven.

## Framework Selection

| Framework | Best for |
|-----------|----------|
| LangGraph | Complex workflows, cycles, checkpointing, production |
| AI SDK v6 | TypeScript / React, streaming UX, simpler coordination |
| CrewAI | Quick prototyping, role-based sequential/hierarchical |
| AutoGen | Research, conversational agents, HITL experiments |

## Production Rules
- Timeouts at every level: agent 30s, team 120s, full workflow 300s
- Graceful degradation: fallback to single agent when coordination fails
- Map dependencies before parallelizing — hidden dependencies cause deadlocks
- Per-stage observability traces with token counts and status

Part of [[multi-agent]].

## Related
- [[orchestration-patterns]]
- [[agent-communication]]
- [[react-pattern]]
- [[plan-and-execute]]
- [[loop-control]]
- [[approval-gates]]
- [[observability]]
