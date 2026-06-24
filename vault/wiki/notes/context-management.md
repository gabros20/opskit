---
type: note
title: Context Management & Caching
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [kv-cache, prompt-caching, sliding-window, hierarchical-memory, streaming, context-engineering]
aliases: [kv-cache-optimization, prompt-caching]
---

Context management addresses memory and efficiency constraints as conversations grow: sliding windows enable infinite streaming, hierarchical memory compresses older content progressively, KV-cache optimization slashes GPU memory usage, and prompt caching cuts costs 60-90% on static content.

## Context Failure Modes

Drew Breunig (2025) identifies four failure modes beyond simple degradation: **context poisoning** (hallucinations compound across turns), **context distraction** (agent over-relies on history vs. training after 100K tokens), **context confusion** (too many tools degrade accuracy — 46 → 19 tools = 44% improvement), and **context clash** (conflicting info; multi-turn prompts perform 39% worse on average). Solutions: isolate tasks in separate threads, summarize + offload, curate tool loadout, single-turn reformulation.

## The 4-Bucket Framework (Lance Martin, 2025)

**Write** — scratchpads, episodic memory, filesystem offloading. **Select** — embeddings, RAG for tool defs (3× improvement). **Compress** — summarization, trimming, tool result compression. **Isolate** — multi-agent split (15× tokens but 90% performance gain). Examples: Manus writes old tool results to files, Cursor offloads trajectories, Claude Code auto-compacts at 95% window fill.

## Sliding Windows & Streaming

**StreamingLLM (ICLR 2024)**: first 4 tokens are "attention sinks" — keeping them plus a recent window enables stable generation beyond 4M tokens at 22.2× speedup over full recomputation. Limitation: model only "sees" recent tokens; it does not expand comprehension. **Cascading KV Cache (2025)** adds +12.13% on LongBench. **LongRoPE** extends context from 128K to 2M+ tokens with ~1,000 fine-tuning steps.

## Hierarchical Memory

**HiAgent (ACL 2025)**: organizes agent memory around subgoals as chunks — current subgoal gets full detail, previous subgoals get compressed summaries, cross-trial learnings accumulate. Results: 2× success rate, −3.8 steps per task. **MemGPT-style** mirrors OS virtual memory: primary context (RAM) spills to recall storage (searchable DB) and archival storage (vector store) when usage exceeds ~70%.

## KV-Cache Optimization

KV cache often exceeds model parameters: LLaMA-2 13B at 100K tokens = ~80 GB vs 26 GB model weights. Key strategies:

- **KIVI (ICML 2024)**: 2-bit asymmetric quantization → 2.6× less peak memory, 4× larger batch size
- **SnapKV (2024)**: evict low-attention tokens → 3.6× faster generation, 8.2× memory efficiency, 380K token context
- **MiniCache (2024)**: merge adjacent-layer K/V states → 5.02× compression, 41% memory reduction
- **RocketKV (ICML 2025)**: two-stage (SnapKV + HSA) → up to 400× compression, 3.7× end-to-end speedup
- **DeepSeek MLA**: compress KV into latent space → 93.3% KV reduction, 5.76× generation throughput

## Prompt Caching

| Provider | Max Discount | TTL | Min Tokens |
|---|---|---|---|
| Anthropic | 90% | 5 min | 1,024–4,096 |
| OpenAI | 50–90% | 5–10 min | 1,024 |
| Google | 75–90% | 1 hour | 1,024–4,096 |

Best practice: place static content (tools, system instructions) first; use up to 4 cache breakpoints (Anthropic). Two-layer caching: exact match (L1, ~53ms, 123× faster) then semantic match (L2, ~87% hit rate with tuning).

## Production Inference

**vLLM PagedAttention**: non-contiguous KV pages → memory waste from 60-80% to <4%, 14-24× throughput vs HuggingFace. **SGLang RadixAttention**: radix tree for shared prefixes → 6.4× throughput. **Prefill-decode disaggregation** (Mooncake): separate compute-bound prefill cluster from memory-bound decode cluster → 59-498% capacity gains.

Part of [[context]].

## Related Notes

- [[token-optimization]] — prerequisite: compression before caching
- [[injection-strategies]] — where to place managed context
- [[context-windows]] — token limits that make management necessary
- [[memory-systems-working-memory]] — working memory hierarchies
- [[hierarchical-subgoal-memory]] — HiAgent subgoal chunking pattern
- [[state-persistence-checkpointing]] — cross-session memory persistence
- [[optimization]] — production cost and throughput optimization
