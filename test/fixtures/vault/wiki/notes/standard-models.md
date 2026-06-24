---
type: note
title: Standard Models vs Reasoning Models
status: evergreen
created: 2025-11-28
updated: 2026-06-19
tags: [standard-models, reasoning-models, chain-of-thought, model-comparison, agents]
aliases: [Standard LLMs vs Thinking Models]
---

Standard models (GPT-4o, Claude, Gemini) generate tokens immediately — fast, cheap, suitable for 90–95 % of tasks. Reasoning models (o3, o4-mini, DeepSeek-R1, Qwen3) produce a hidden internal chain-of-thought before answering — 6–8× better on complex math/logic/science, but 10–30× slower and more expensive.

## Why standard models fail on hard tasks

Standard training optimizes next-token prediction: the model learns to pattern-match, not to verify. On multi-step math, it jumps to answers without checking intermediate steps. Success rate on multi-step problems: ~85 % for standard vs near-perfect for well-trained reasoning models.

## Reasoning model mechanics

Reasoning models are trained with Reinforcement Learning (RL) where rewards are given per step (process supervision), not just for final correctness. This teaches: (1) native chain-of-thought without explicit prompting, (2) backtracking when a path fails, (3) self-verification. Training: o3 used 10× more compute than o1. DeepSeek-R1 uses GRPO (Group Relative Policy Optimization) and is fully open-source (Apache 2.0).

## Benchmark comparison (Nov 2025)

| Model | AIME 2024 | GPQA Diamond | ARC-AGI-1 |
|-------|-----------|--------------|-----------|
| GPT-4o | 13.4 % | 56 % | 5 % |
| o3 (medium) | ~96.7 % | ~83 % | 53 % |
| DeepSeek-R1-0528 | 91.4 % | 81.0 % | — |
| Qwen3-235B (Thinking) | 85.7 % | — | — |

ARC-AGI-2 (March 2025): even best models score < 3 % vs 60 % for average humans — reasoning still far from general intelligence.

## Hybrid routing: the optimal pattern

Route 90–95 % to standard models; send only complex tasks (math proofs, algorithm design, multi-step logic) to reasoning models. Hybrid (5 % reasoning) costs ~$144/month vs $500/month for all-reasoning at 10k queries/month.

Cost-efficient option: o4-mini achieves 41 % ARC-AGI-1 at ~5 ¢/task. Open-source alternative: DeepSeek-R1-0528 or Qwen3-Thinking match proprietary performance.

Part of [[foundations]].

**Related:** [[reasoning-models]] · [[when-to-use-which]] · [[tradeoffs]] · [[model-selection]] · [[llm-intro]]
