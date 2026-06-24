---
type: note
title: Agent Communication & Shared State
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [multi-agent, shared-state, message-passing, blackboard, mcp]
aliases: [inter-agent communication, shared state pattern]
---

Agents communicate through **message passing** (loose coupling, explicit coordination) or **shared state** (tight coupling, implicit coordination via common knowledge base). Choosing wrong costs dearly: naive multi-agent context sharing uses 15x more tokens than single-agent chat, with 67% of those tokens wasted on redundant information.

## Message Passing Patterns

**Direct Agent-to-Agent**: Structured handoff object with `summary`, `keyFacts`, `constraints`, and `expectation` fields. Simple to trace; doesn't scale past a handful of agents.

**Broadcast / Pub-Sub**: Agents publish to named topics (e.g. `research.complete`, `error.detected`); subscribers react. Decouples producers from consumers; requires message bus; ordering not guaranteed.

**Request-Response**: Synchronous blocking call when one agent needs another's result before continuing.

## Shared State Patterns

**Blackboard Pattern** (ACL 2025): All agents read/write a common store divided into Facts, Status, Artifacts, and Tasks sections. Improves task success by 13–57% over message-only approaches. Requires concurrency control (compare-and-swap atomic updates).

**Scoped Shared State**: Global read-only layer → team-scoped read/write layer → agent-private scratchpad. Prevents token explosion; reduces total context from ~18k tokens (naive) to ~5k tokens (scoped).

**Memory Architecture**: Short-term (thread-scoped checkpointer, e.g. LangGraph `PostgresSaver`) + long-term (cross-thread store, e.g. `PostgresStore`) + working memory (active context window).

## Conflict Resolution

- **Voting**: 13.2% better for reasoning tasks (avg 3.38 rounds) — ACL 2025
- **Consensus**: 2.8% better for knowledge tasks (avg 1.42 rounds)
- **Authority hierarchy**: Safety agent holds veto; supervisor breaks ties; domain expert takes priority in their specialty

## Standards & Protocols

**MCP (Model Context Protocol)**: Anthropic, November 2024. Emerging industry standard for tool and resource sharing across agents via a standardized server/client architecture. Adopted by Anthropic and OpenAI.

**A2A Protocol**: Google, 2024. Agent-to-agent communication standard.

## Production Pitfalls
- Unbounded context growth → implement compaction, TTLs, summarization
- Circular dependencies → use DAG-based dependency graphs with timeouts
- Silent state overwrites → version every state update with `agentId` and timestamp

Part of [[multi-agent]].

## Related
- [[orchestration-patterns]]
- [[coordination-strategies]]
- [[memory-systems-working-memory]]
- [[state-persistence-checkpointing]]
- [[context-management]]
- [[tool-registry]]
- [[resilience-patterns]]
