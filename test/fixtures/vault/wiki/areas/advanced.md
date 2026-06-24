---
type: area
title: Advanced
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [advanced-agents, self-improvement, code-generation, multimodal, exploration, cutting-edge]
---

The advanced area covers frontier agent patterns that go beyond standard tool-calling and RAG. These techniques compound capabilities, cross modality boundaries, and tackle open-ended research — trading higher complexity and cost for qualitatively new behaviors that simpler agents cannot achieve.

Self-improving and meta-learning agents (Reflexion, DSPy/MIPROv2, ToolLLM, Voyager) are the most foundational: they close the loop between execution and learning, so each task makes the agent measurably better. The Reflexion pattern alone delivers 23–60% accuracy gains without fine-tuning; MIPROv2 adds 13% on multi-stage pipelines through Bayesian prompt optimization. The unifying principle is that LLMs can evaluate their own outputs and generate actionable verbal feedback — making episodic memory and bounded retry loops the key infrastructure investment.

Code generation agents apply these ideas to autonomous software engineering. The gap between raw LLM performance (~3.8% on SWE-Bench) and tool-equipped agents (26–49%) is driven entirely by the Code-Test-Fix loop, sandboxed execution (E2B, Modal, Docker), and purpose-built interfaces (SWE-Agent ACI, Aider diff format). Tests are the oracle; human review remains critical for security-sensitive changes. Multimodal agents extend action space to visual interfaces, voice, and documents — enabling computer use on legacy systems, real-time voice with WebRTC/WebSocket, and VLM-based document parsing (LlamaParse) that outperforms traditional OCR on complex layouts at the cost of 5–10x higher token spend.

Exploration agents address open-ended research through a five-phase detective methodology: broad fan-out scouting across academic, patent, news, forum, and dataset sources; knowledge mapping and clustering; scored deep-dive selection; hypothesis generation; and iterative refinement. A comprehensive run takes 40+ minutes and hundreds of thousands of tokens — appropriate for competitive intelligence, literature reviews, and strategic decisions, not for factual lookups.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[self-improving-agents]]
- [[code-generation-agents]]
- [[multimodal-agents]]
- [[exploration-agents]]
