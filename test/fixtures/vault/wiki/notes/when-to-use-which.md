---
type: note
title: When to Use Which Model
status: evergreen
created: 2025-11-28
updated: 2026-06-19
tags: [model-routing, cost-optimization, decision-framework, agents, llm-selection]
aliases: [Model Routing, LLM Decision Matrix]
---

The guiding principle: use the smallest/cheapest model that meets your requirements. Start with the cheapest, escalate only when quality is provably insufficient.

## 2025 model tiers (Nov 2025 pricing)

**Fast & Cheap** ($0.10–$1/M input): GPT-4.1 Nano ($0.10), Gemini 2.5 Flash ($0.10), GPT-4.1 Mini ($0.40), Claude Haiku 4.5 ($1.00). Use for high-volume simple tasks, classification, parsing.

**Balanced** ($1.25–$3/M input): GPT-4.1 ($2.00), Gemini 2.5 Pro ($1.25, 2M context), Claude Sonnet 4.5 ($3.00). Use for general production apps, coding, writing.

**Premium / Reasoning** ($5–$10+/M input): Claude Opus 4.5 ($5.00), o4-mini ($1.10), o3 ($10.00). Use for critical decisions, complex math, highest accuracy.

## Use-case decision matrix

| Need | Model | Why |
|------|-------|-----|
| Agentic tool calling | Claude Haiku 4.5 / Sonnet 4.5 | 97–99 % tool-calling success |
| Coding | Claude Sonnet 4.5 | 72.7 % SWE-bench |
| Long documents (50+) | Gemini 2.5 Pro | 2M token context |
| Budget-constrained | Gemini 2.5 Flash | $0.04 input, 200+ tok/s |
| Complex reasoning | o4-mini / o3 | AIME 2024: 41 %+ ARC-AGI-1 |
| Maximum quality | Claude Opus 4.5 | 68.1 LiveBench |

## Routing patterns

**Complexity-based router**: classify task complexity (0–1 score based on steps, math, code, context length); route to Flash < 0.3, Mini 0.3–0.7, Sonnet/o4-mini > 0.7. 80–90 % cost savings vs always using premium.

**Cascade**: try cheapest first, assess quality (score > 0.8?), escalate if not. Adds latency for escalated requests.

**Specialist routing**: o4-mini for outline (reasoning), Claude Sonnet for prose (writing), GPT-4.1 Mini for metadata (simple).

**Custom provider abstraction (AI SDK 6)**: `customProvider` with semantic aliases ("fast", "balanced", "coding", "reasoning") hides implementation details; swap models in one place.

## Cost-saving tactics

Prompt caching: 50–90 % savings on repeated context. Batch API (OpenAI/Anthropic): 50 % discount for 24-hour delivery. Set token budgets per task type. A/B test cheaper model substitutions before committing.

Part of [[foundations]].

**Related:** [[tradeoffs]] · [[standard-models]] · [[reasoning-models]] · [[model-selection]] · [[tool-calling]] · [[optimization]]
