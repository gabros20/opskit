---
type: note
title: Introduction to Large Language Models
status: evergreen
created: 2025-11-21
updated: 2026-06-19
tags: [llm, transformer, autoregressive, neural-networks, self-attention]
aliases: [LLM Fundamentals, What is an LLM]
---

Large Language Models are neural networks built on the Transformer architecture (Vaswani et al. 2017) that learn by predicting the next token in a sequence. Trained on trillions of tokens, they emergently acquire capabilities — grammar, facts, reasoning, code generation — without those abilities being explicitly programmed.

## Core mechanism

The LLM pipeline: text is tokenized to integer IDs → embedded into high-dimensional vectors (768–1536 dims) → passed through stacked Transformer blocks using self-attention → a language model head converts the final vectors to a probability distribution over the vocabulary → one token is sampled → fed back as input. This **autoregressive loop** continues until a stop condition.

Self-attention lets every token attend to every other token, enabling resolution of long-range references ("it" → "cat"). Capabilities emerge at scale: GPT-3 (175B params) gained few-shot learning absent in GPT-2 (1.5B) with no architectural changes.

## 2025 model landscape

- **Claude Sonnet 4.5**: 77.2 % SWE-bench Verified (best coding/agentic), 200k–1M context
- **GPT-5**: ~45 % fewer hallucinations than GPT-4o, unified adaptive thinking
- **Gemini 3.0 Pro**: best multimodal, "Deep Think" mode, #1 LMArena
- **Llama 4 Scout**: open-source MoE, 10M token context, 30T+ training tokens, 2T total params / 288B active

Architecture trend: 2025 marked shift to Mixture-of-Experts (MoE) and extended context windows (up to 10M tokens).

## Practical limits

Hallucination rate remains 3–5 % even on frontier models; real-time latency (0.5–2 s) precludes sub-100 ms applications; LLMs are non-deterministic even at temperature = 0 (require validation). Use RAG for factual grounding, structured output for reliability.

## Production rules of thumb

Temperature: 0.2 for code/facts, 0.7–0.9 for creative. Implement sliding-window or subgoal-compression context management for multi-turn agents. Estimate 1 token ≈ 0.75 English words.

Part of [[foundations]].

**Related:** [[training-vs-inference]] · [[context-windows]] · [[sampling-parameters]] · [[tokenization]] · [[standard-models]] · [[react-pattern]]
