---
type: note
title: Orchestration Patterns & Specialized Agents
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [multi-agent, orchestration, supervisor-worker, swarm, specialization]
aliases: [multi-agent orchestration, supervisor pattern]
---

Multi-agent orchestration divides complex tasks among specialized agents coordinated by a supervisor that classifies intent, routes requests, transfers context, and assembles responses. Research (2024–2025) shows 88% vs 50% accuracy on strategic reasoning tasks for multi-agent vs single-agent, but at 3x latency and cost. **Rule of thumb**: an agent with 5 tools outperforms one with 50.

## Core Patterns

**Supervisor-Worker**: Single orchestrator with no tools routes all execution to focused workers. Clear accountability; adds one routing hop per call. Best for audit-required or regulated environments.

**Hierarchical Teams**: Nested supervisors for 6+ agents with natural domain groupings (e.g. research team + execution team each with their own lead). Scales well; risks over-engineering.

**Orchestrator-Worker with Dynamic Routing**: Orchestrator generates a full execution plan (with dependency graph and parallel flags) before dispatching. Handles complex multi-step tasks; adds planning overhead.

**Swarm (Peer-to-Peer Handoffs)**: Agents hand off directly to peers via `create_handoff_tool` (LangGraph Swarm, OpenAI Swarm 2024 → Agents SDK 2025). No central bottleneck; 30% lower latency vs supervisor; token usage stays flat with added domains. Best for internal systems where all agents are known. Benchmarks (LangChain June 2025): swarm slightly outperforms supervisor on 2+ domain tasks.

**Forward Message Tool**: Prevents supervisor paraphrasing loss by passing worker responses verbatim. Adding this alone yielded ~50% performance increase in supervisor architectures.

## Specialized Agent Types

| Type | Model tier | Permissions |
|------|-----------|------------|
| Planner/Architect | GPT-4/Opus | Read-only |
| Executor/Worker | Haiku/GPT-3.5 | Scoped CRUD |
| Critic/Reviewer | Sonnet/GPT-4-mini | Read + validate |
| Debug/Error Correction | Medium | Read logs + apply fix |

## Key Rules
- Supervisor has NO tools — delegates all execution
- Misrouted requests cascade; invest in routing accuracy (target >95%)
- Context transfer: use structured handoffs, not full message history
- Production infra: Redis for session state, PostgreSQL for checkpoints, BullMQ for async execution
- Graceful degradation: fallback to single agent on coordination failure

Part of [[multi-agent]].

## Related
- [[react-pattern]]
- [[tool-definition]]
- [[agent-communication]]
- [[coordination-strategies]]
- [[plan-and-execute]]
- [[observability]]
- [[loop-control]]
