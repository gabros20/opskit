---
type: note
title: Context Windows & Token Limits
status: evergreen
created: 2025-11-21
updated: 2026-06-19
tags: [context-window, tokens, kv-cache, memory-management, agents]
aliases: [Context Length, Token Limits]
---

A **context window** is the maximum tokens an LLM processes in one interaction — its entire working memory. Everything the model sees (system prompt, history, tool results, user message) must fit here.

## Why limits exist

Self-attention is O(n²): doubling context = 4× compute. 128k-token inference takes 20+ seconds vs 0.5 s at 1k tokens. GPU KV-cache grows ~2 KB/token; 1M-context × 1000 concurrent users = 2 TB GPU RAM — impossible. Additionally, the **"Lost in the Middle"** effect (Liu et al. 2023): LLMs achieve ~90 % retrieval accuracy at context boundaries but only ~60 % in the middle. Place critical information at start and end.

## 2025 model windows

GPT-4o: 128k · Claude Sonnet 4.5: 200k–1M · Gemini 1.5 Pro: 2M · Llama 4 Maverick: 1M · Llama 4 Scout: 10M. Standard in 2024: 128k–200k; cutting-edge 2025: 1M–2M.

## Token accumulation in agents

Typical agent step: system prompt (800) + tool definitions (1500) + history (3000) + working memory (200) + user message (50) = ~5550 tokens. After 100 agent steps without management: 80k–100k tokens → overflow.

## Context management patterns

1. **Hierarchical / Subgoal compression** — compress completed subgoals to 50–100-token summaries at 80 % capacity. HiAgent (2024) achieves 2× success rate on long-horizon tasks this way. 84 % token reduction in practice.
2. **Working memory / Entity injection** — extract recently accessed entities and inject only those (~200 tokens) instead of full history (10k tokens).
3. **Lazy content fetching** — return metadata first (100 tokens), fetch full content only on demand (87 % savings vs. eager loading).
4. **Message trimming + checkpointing** — keep last 20 messages active; persist full history to database every 3–5 steps.

## Token rules of thumb

English: 1 word ≈ 1.33 tokens. Chinese: 1–2 tokens/character. Code: 1 line ≈ 5–10 tokens. Structured JSON uses ~73 % fewer tokens than verbose prose equivalents.

Ultra-long context (1M+) is not always better: "Lost in the Middle" accuracy still degrades, latency is 20–60 s, and cost is 10–100× higher. Prefer smart context injection over brute-force length.

Part of [[foundations]].

**Related:** [[llm-intro]] · [[tokenization]] · [[sampling-parameters]] · [[token-optimization]] · [[context-management]] · [[injection-strategies]] · [[memory-systems-working-memory]]
