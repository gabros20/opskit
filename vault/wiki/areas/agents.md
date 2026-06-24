---
type: area
title: Agents
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [agents, autonomous-systems, react, tool-calling, loop-control, coala]
---

AI agents combine LLM reasoning with tool execution in a perception-reasoning-action-memory cycle. Unlike chatbots (text only) or functions (deterministic logic), agents dynamically decide what to do next based on observations from their environment. The field matured sharply between 2024 and 2026: enterprise multi-agent adoption grew from 23% to 72%, and leading benchmarks (SWE-bench Verified, WebArena) now show agents reaching 60–75% success on real-world tasks — up from single-digit figures two years ago.

The dominant execution pattern is **ReAct** (Yao et al. 2022): interleave an explicit Thought with one tool call, observe the result, repeat. Enhancements like Reflexion (verbal self-reflection from failed trajectories, +22 points on AlfWorld) and LATS (Monte Carlo Tree Search over ReAct steps, 94.4% HumanEval) extend the baseline. The CoALA framework provides a principled vocabulary: four memory types (Working, Episodic, Semantic, Procedural), two action classes (External, Internal), and a repeated decide-plan-execute cycle. GPT-3.5 improved from 48% to 95% on coding benchmarks when equipped with this architecture.

Tool quality is the primary reliability lever. Well-structured tool descriptions with Zod schemas and structured error responses move task completion from ~60% to 95%+. For large tool sets (>30 tools), dynamic tool search — two-stage retrieval with BM25 or vector search plus cross-encoder reranking — reduces context by 85% and improves accuracy by 8–25 points. The Anthropic Tool Search Tool (2025) and the MCP ecosystem (LiveMCPBench: 70 servers, 527 tools) formalise this pattern.

Loop control is mandatory: 85% of agent failures trace back to unclear stopping conditions. Layer the defences — hard step limits calibrated per task type, explicit finish tools, goal-state reflection (ReflAct: 93.3% ALFWorld), stuck-pattern detection, and entropy-based early exit (25–50% compute savings). For long-running agents that exceed context windows, the Ralph Loop pattern (plan file + tracking file + git commits + verification hooks) provides durable progress tracking. Production heuristics: start at 10–15 steps, target <5% limit-hit rate, 40–70% average utilisation.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[agent-fundamentals]]
- [[react-pattern]]
- [[tool-calling]]
- [[loop-control]]
