---
type: area
title: Context
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [context-engineering, token-optimization, kv-cache, prompt-caching, rag-injection, context-management]
---

Context engineering is the discipline of deciding what information enters an LLM's context window, how it is compressed, where it is placed, and when it is retrieved. It sits between raw retrieval and generation, and its quality determines both cost and accuracy at scale.

Modern compression methods (LLMLingua-2, ACON, AgentDiet) routinely achieve 40-90% token reduction with less than 5% accuracy loss, and often improve quality by eliminating "lost in the middle" noise. KV-cache techniques (SnapKV, RocketKV, DeepSeek MLA) address the GPU memory bottleneck that becomes the primary constraint beyond 4K-token contexts. Prompt caching from providers (Anthropic 90%, OpenAI 50-90%) stacks on top, targeting the static portions of prompts.

Placement and timing are as important as volume. The "lost in the middle" effect penalises information buried in context centre by −30%+; role-based assignment (static instructions → system, dynamic RAG → user, reasoning traces → assistant) keeps caches warm and signals clear. Retrieval timing — from always-retrieve to DeepRAG's knowledge-boundary calibration (0.28 retrievals/query, +26.4% accuracy) — determines whether retrieval is an asset or overhead.

The current best practice combines the 4-bucket model (Write / Select / Compress / Isolate), progressive disclosure for domain expertise (Agent Skills), iterative retrieval for complex reasoning (RAT), and hierarchical memory for long-horizon agents (HiAgent, MemGPT). Context is not free: every token influences model behaviour, and context poisoning, distraction, confusion, and clash are failure modes as real as hallucination.

## Timeline

- 2026-06-19 Imported 3 notes from the source KB.

## Notes

- [[token-optimization]]
- [[context-management]]
- [[injection-strategies]]
