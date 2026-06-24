---
type: area
title: Foundations
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [llm, transformers, embeddings, model-selection, tokenization]
---

The Foundations area covers the core concepts every practitioner needs before building with LLMs: what they are, how training differs from inference, what controls their output, and how to choose between them.

Large Language Models are autoregressive next-token predictors built on the Transformer architecture (Vaswani et al. 2017). Scale unlocks emergent abilities — few-shot learning appeared at 175B parameters, reasoning at 1T+. The 2025 landscape is dominated by frontier models from OpenAI, Anthropic, and Google alongside capable open-source alternatives (Llama 4, DeepSeek-R1, Qwen3). A new model class — **reasoning models** (o3, o4-mini, DeepSeek-R1) — uses reinforcement learning to generate internal chain-of-thought, achieving 6–8× better performance on math, science, and code at 10–30× higher cost and latency.

Inference economics drive most production decisions. Training is a one-time cost ($1M–$100M+, done by providers); inference is what you pay every call ($0.0001–$0.10). Context windows (128k–2M tokens in 2024–2025) act as the model's working memory; efficient management via subgoal compression, entity injection, and lazy fetching is non-negotiable for multi-step agents. Sampling parameters — temperature, top-p, and the 2025 innovation min-p — control output randomness and directly affect both quality and cost.

The embedding sub-area covers the vector representations that power semantic search and RAG. Key concepts: dense fixed-size vectors (384–3072 dims), trained via contrastive learning; cosine similarity as the standard metric for text; the accuracy plateau above 1536 dimensions; and the practical choices between API providers (Voyage-3-large, OpenAI text-embedding-3) and self-hosted options (SBERT, BGE).

## Timeline

- 2026-06-19 Imported 13 notes from the source KB.

## Notes

- [[llm-intro]]
- [[training-vs-inference]]
- [[context-windows]]
- [[sampling-parameters]]
- [[model-selection]]
- [[standard-models]]
- [[reasoning-models]]
- [[when-to-use-which]]
- [[tradeoffs]]
- [[tokenization]]
- [[embedding-models]]
- [[vector-similarity]]
- [[dimensionality]]
