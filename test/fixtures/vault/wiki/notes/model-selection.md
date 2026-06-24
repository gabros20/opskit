---
type: note
title: Model Selection Guide
status: evergreen
created: 2025-11-21
updated: 2026-06-19
tags: [model-selection, cost, benchmarks, agents, llm-providers]
aliases: [Choosing an LLM, LLM Comparison]
---

Model selection balances **cost**, **latency**, **quality**, and **reliability**. With 100+ models in 2025, the guiding principle is: use the smallest/cheapest model that meets your requirements.

## 2025 top models (Nov 2025 benchmarks)

| Model | LiveBench | Tool-calling | Cost (in/out per 1M) | Best for |
|-------|-----------|--------------|----------------------|----------|
| Claude 4.5 Opus | 68.1 | 99 %+ | $15/$75 | Maximum quality |
| Claude 4.5 Sonnet | 65.2 | 99 %+ | $3/$15 | Coding, agents |
| GPT-5.1 | 63.8 | 98 %+ | $1.25/$10 | Balanced |
| Claude 4.5 Haiku | 60.5 | 97 %+ | $1/$5 | Speed + value |
| GPT-4.1 Mini | 58.3 | 97 %+ | $0.40/$1.60 | Best all-round value |
| Gemini 2.5 Flash | 56.8 | 89 % | $0.10/$0.40 | High-volume, speed |

**Coding**: Claude Sonnet 4.5 leads SWE-bench at 77.2 %. **Reasoning**: o3 (96.7 % AIME 2024, 53 % ARC-AGI-1). **Long context**: Gemini 2.5 Pro (2M tokens); Gemini 3 Pro (1M). **Open-source agentic**: MiniMax M2 (SWE-bench 69.4 %, free, 4× H100).

## Tool-calling reliability matters most for agents

At 1000 tool calls/day: Claude (99 %) → 10 failures/day; Gemini Flash (89 %) → 110 failures/day. The 10 % gap = 10× operational overhead. Real cost = API cost + (error rate × retry cost) + lost revenue from failures.

## Routing patterns

1. **Static selection** — one model for all tasks; simplest; suboptimal.
2. **Complexity-based routing** — classify task complexity (simple/moderate/complex) and route to Gemini Flash / GPT-4.1 Mini / Claude Sonnet respectively. Saves 80–90 % vs always using premium.
3. **Cascade / try-cheap-first** — attempt Gemini Flash, validate quality, escalate to Sonnet on failure.
4. **Specialist routing** — o4-mini for outlines (reasoning), Claude Sonnet for content (writing), GPT-4.1 Mini for metadata (simple).

## Prompt caching

Anthropic and OpenAI both support prompt caching (90 % discount on re-used tokens after first call). Cache system prompts > 1000 tokens; batch non-urgent tasks for 50 % discount.

Part of [[foundations]].

**Related:** [[standard-models]] · [[reasoning-models]] · [[when-to-use-which]] · [[tradeoffs]] · [[llm-intro]] · [[sampling-parameters]]
