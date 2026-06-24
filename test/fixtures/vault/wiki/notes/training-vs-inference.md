---
type: note
title: Training vs Inference
status: evergreen
created: 2025-11-21
updated: 2026-06-19
tags: [training, inference, fine-tuning, lora, cost-optimization]
aliases: [LLM Training Pipeline]
---

**Training** is a one-time operation — adjusting billions of weights over massive datasets ($1M–$100M+, weeks, done by OpenAI/Google/Meta). **Inference** is every API call you make — forward pass only, fixed weights, $0.0001–$0.10/request. As a developer, 99.9 % of your production costs are inference.

## Three stages of training

1. **Pretraining** — next-token prediction on diverse corpora. Llama 4 used 30T+ tokens (2 × Llama 3). Costs: GPT-4 ≈ $100M, DeepSeek v3 ≈ $5.6M (efficient MoE).
2. **Fine-tuning** — SFT on labeled pairs (1k–100k examples). Cost: as low as $45 to fine-tune GPT-4o-mini on 10k examples × 3 epochs. LoRA (Parameter-Efficient Fine-Tuning) reduces trainable params 140–280×, training time 32–44 %, with 98–99 % of full-fine-tune performance.
3. **Alignment (RLHF)** — reinforcement learning from human feedback to make outputs helpful and safe.

Advanced LoRA variants (2024): DoRA, PiSSA, LoReFT each improve convergence further.

## Inference optimization techniques

- **Quantization**: 4-bit reduces model 4–8× in size, 2–4× faster (< 2 % accuracy loss). Llama 3.1 70B: 280 GB (FP32) → 35 GB (INT4).
- **KV-Cache**: caches key-value matrices from prior tokens; 3–10× faster generation. KVQuant (NeurIPS 2024) extends this to 10M-token context on one A100-80GB GPU.
- **Batching**: 2–10× throughput by processing multiple requests on one GPU.
- **Distillation**: teacher (large) → student (small) inherits behavior. GPT-4o-mini is 225× smaller than GPT-4, 6× faster, 16× cheaper.

## Decision thresholds

Fine-tune only when: > 100k requests/month on a specialized domain AND base model achieves < 80 % accuracy. Otherwise, prompt engineering is faster and cheaper. Self-hosting breaks even around 1M requests/month vs. API.

## Pricing snapshot (Nov 2025)

Gemini 2.5 Flash: $0.10/$0.40 per 1M tokens. GPT-4o-mini: $0.15/$0.60. Claude Sonnet 4.5: $3/$15. GPT-5: $1.25/$10.

Part of [[foundations]].

**Related:** [[llm-intro]] · [[context-windows]] · [[model-selection]] · [[tradeoffs]] · [[token-optimization]]
