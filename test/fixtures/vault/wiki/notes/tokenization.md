---
type: note
title: Tokenization
status: evergreen
created: 2025-12-03
updated: 2026-06-19
tags: [tokenization, bpe, sentencepiece, tiktoken, token-counting]
aliases: [BPE Tokenization, Subword Tokenization]
---

Tokenization converts raw text to integer IDs that LLMs can process. Every API cost, context limit, and latency figure depends on it. The dominant approach is **subword tokenization** — units smaller than words but larger than characters — balancing vocabulary size, sequence length, and OOV handling.

## Three algorithms

**BPE (Byte Pair Encoding)** — used by GPT-2/3/4, Llama, Mistral. Greedy frequency-based merging: starts from characters, iteratively merges the most frequent adjacent pair until vocabulary reaches target size (50k–128k). Fully lossless. Byte-level BPE (GPT-4) operates on 256 bytes → never OOV. GitHub's 2024 BPE implementation is 4× faster than tiktoken, O(n) vs O(n²).

**WordPiece** — used by BERT, DistilBERT. Selects merges that maximize corpus likelihood (semantic coherence) rather than raw frequency. Uses `##` prefix for continuation tokens. Slightly lossy (spaces between tokens lost).

**SentencePiece** — used by T5, mT5, ALBERT. Language-agnostic: treats input as raw byte/character sequence with no pre-tokenization. Uses `▁` (U+2581) as a space character. Works identically for Chinese, Japanese, and English. Supports both BPE and Unigram algorithms internally.

## Token estimation rules

| Content | Tokens per unit |
|---------|-----------------|
| English text | 1 word ≈ 1.33 tokens |
| English characters | 4 chars ≈ 1 token |
| Code | 1 line ≈ 5–10 tokens |
| Chinese/Japanese | 1 char ≈ 1–2 tokens |
| Compact JSON | ~30 % fewer than pretty-printed |

Non-English languages cost 1.5–2× more tokens than English for equivalent meaning.

## Production practices

Use `tiktoken` (cl100k_base for GPT-4) to count tokens before expensive API calls and estimate costs. Use compact `JSON.stringify(data)` over pretty-printed (30 % savings). Truncate to token boundaries safely before embedding (8191-token limit; APIs truncate silently without warning). Monitor token usage per agent step to catch runaway accumulation early. Don't assume token counts are identical across models — same text can vary 20–30 % between GPT-4 and BERT tokenizers.

Part of [[foundations]].

**Related:** [[llm-intro]] · [[context-windows]] · [[embedding-models]] · [[tradeoffs]] · [[token-optimization]]
