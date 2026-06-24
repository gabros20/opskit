---
type: area
title: Multi Agent
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [multi-agent, orchestration, coordination, swarm, blackboard, langgraph]
---

Multi-agent systems distribute complex tasks across specialized agents rather than burdening a single monolithic agent with dozens of tools. The core insight from 2024–2025 research is that an agent with 5 focused tools consistently outperforms one with 50, and a well-structured multi-agent system achieves 88% accuracy on strategic reasoning tasks versus 50% for a single agent — but at a real cost of 3x latency and token overhead that must be justified before deployment.

The area spans three interlocking concerns. **Orchestration** decides the structural shape of the system: a supervisor-worker hierarchy, a hierarchical team tree, a dynamic orchestrator that generates full execution plans, or a peer-to-peer swarm where agents hand off directly without a central bottleneck. The swarm pattern (OpenAI Swarm 2024 → Agents SDK 2025, LangGraph Swarm) has emerged as the lower-latency default for internal systems, while supervisor architectures remain preferred where external agents or audit trails are required. **Communication** governs how agents share information — message passing (direct, pub-sub, request-response) for loose coupling, or a shared blackboard for complex coordination. The blackboard pattern improves task success by 13–57% (ACL 2025) but demands concurrency control and disciplined context scoping to avoid the 15x token overhead of naive multi-agent setups. **Coordination** covers execution flow: sequential pipelines for dependent stages, parallel fan-out/fan-in (60–70% latency reduction) for independent work, hierarchical delegation for large teams, and LangGraph `StateGraph` cycles for generate-critique-refine loops.

Practical production guidance runs through all three notes: always add timeouts at every level (agent 30s, team 120s, workflow 300s), implement graceful degradation to a single-agent fallback, instrument per-stage traces with token counts, and use MCP (Model Context Protocol, Anthropic November 2024) as the emerging standard for inter-agent resource and tool sharing. Start with a single agent and extract specialists only after identifying concrete bottlenecks — the overhead is real.

## Timeline

- 2026-06-19 Imported 3 notes from the source KB.

## Notes

- [[orchestration-patterns]]
- [[agent-communication]]
- [[coordination-strategies]]
