---
type: note
title: Reasoning Models Deep Dive
status: evergreen
created: 2025-11-28
updated: 2026-06-19
tags: [reasoning-models, reinforcement-learning, chain-of-thought, deepseek, openai-o3]
aliases: [Thinking Models, Chain-of-Thought Models]
---

Reasoning models generate hidden **thinking tokens** — a long internal chain-of-thought — before producing a final answer. The key training innovation is **process supervision**: reward each reasoning step individually (Lightman et al. 2023), not just the final outcome. This prevents "motivated reasoning" and enables backtracking.

## Training approaches (2025)

**OpenAI o3/o4-mini**: outcome-based RL; model discovers its own test-time strategies (e.g., writing brute-force code to verify an optimized solution). 10× more training compute than o1. Thinking tokens are hidden from users.

**DeepSeek-R1 (Jan 2025, open-source)**: GRPO (Group Relative Policy Optimization). R1-Zero proved pure RL without SFT can develop reasoning. Distillation pipeline transfers reasoning to smaller models (32B distilled outperforms o1-mini). Fully open weights.

**Qwen3-235B (Apr 2025, open-source)**: four-stage pipeline: CoT cold start → Reasoning RL → Thinking/non-thinking fusion → General RL. Hybrid modes: single model switches between fast (non-thinking) and thorough (thinking) on demand. Thinking budget up to 38k tokens, controllable via API.

## Reasoning effort levels (OpenAI)

| Level | Latency | Cost | Steps |
|-------|---------|------|-------|
| low | 2–5 s | $0.15/1k | 5–10 |
| medium | 10–20 s | $0.50/1k | 20–50 |
| high | 30–60 s | $3.00/1k | 100+ |

## Implementation (AI SDK 6)

`reasoningEffort: "medium"` in `providerOptions.openai` for o3/o4-mini. `extractReasoningMiddleware({ tagName: "think" })` via `wrapLanguageModel` for DeepSeek/Groq/Fireworks. `sendReasoning: true` in `toDataStreamResponse` to stream thinking tokens to the client. Access reasoning trace via `result.reasoning` (DeepSeek) or `providerMetadata.openai.reasoningTokens` for token counts.

## Production practices

- Monitor thinking tokens separately — they can be 2k–10k+ per query.
- Cache results for repeated problems (aggressive caching → 90 % cost savings).
- Store reasoning traces for debugging failed queries.
- Set timeouts and fall back to standard models for queries exceeding 30 s.

## ARC-AGI context

ARC-AGI-2 (March 2025): o3 and o4-mini both score < 3 % vs 60 % for average humans. Reasoning models excel at verifiable domains; general intelligence remains unsolved.

Part of [[foundations]].

**Related:** [[standard-models]] · [[when-to-use-which]] · [[tradeoffs]] · [[model-selection]] · [[sampling-parameters]]
