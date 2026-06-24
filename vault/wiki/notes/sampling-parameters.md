---
type: note
title: Sampling Parameters
status: evergreen
created: 2025-11-21
updated: 2026-06-19
tags: [temperature, top-p, sampling, inference, agents]
aliases: [Temperature and Top-P, Decoding Parameters]
---

After all Transformer layers, an LLM outputs raw **logits** over the full vocabulary (50k–200k tokens). Sampling parameters control how one token is selected from the resulting probability distribution, directly affecting quality, creativity, cost, and agent reliability.

## Core parameters

- **Temperature** — scales the distribution. 0 → deterministic (greedy); 0.7 → balanced; 1.0+ → creative/chaotic. Machine translation is extremely sensitive (192 % performance variance); in-context learning is stable in large models.
- **Top-P (nucleus sampling)** — keeps the smallest set of tokens whose cumulative probability ≥ P, then samples from them. Adaptive: expands when model is uncertain, contracts when confident. Preferred over top-k.
- **Top-K** — keeps exactly K highest-probability tokens. Less adaptive than top-p; avoid combining both.
- **Min-P (ICLR 2025)** — sets a minimum probability threshold as α × max_probability (α ≈ 0.1). Adapts to model confidence dynamically. Outperforms top-p on GPQA (82 % vs 76 %, Mistral 7B) across all temperature ranges. Widely adopted in Hugging Face Transformers and vLLM.
- **Frequency / Presence penalty** — reduces repetition; add 0.3–0.5 for long-form content or agent loops.

## Recommended settings by task

| Task | Temperature | Top-P | Notes |
|------|-------------|-------|-------|
| Agent tool calling | 0.3–0.5 | 0.85 | Reliability > diversity |
| General chat | 0.7 | 0.9 | Default baseline |
| Creative writing | 1.0–1.2 | 0.95 | Add frequency penalty |
| Math / factual | 0.1–0.3 | 0.3–0.5 | Near-deterministic |

## 2025 research findings

**Monte Carlo Temperature (TrustNLP 2025)**: sample temperatures dynamically from a range [0.1, 1.0] across queries, aggregate results. Achieves oracle-level performance without expensive hyperparameter tuning. **Multi-temperature test-time scaling (2025)**: different temperatures solve different problem subsets; varying T across 3–5 samples yields +7.3 points on AIME/MATH500/LiveCodeBench vs. single-temperature.

## Cost impact

Lower temperature → shorter, more direct responses. T=0.2 vs T=0.7 on "summarize this" → 45 tokens vs 68 tokens (51 % more). At 1M requests/month, parameter tuning alone can save $70k–$200k annually. Min-P achieves additional 15–20 % token reduction vs top-p.

Part of [[foundations]].

**Related:** [[llm-intro]] · [[training-vs-inference]] · [[model-selection]] · [[tool-calling]] · [[react-pattern]]
