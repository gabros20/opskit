---
type: note
title: Cost-Latency-Quality Trade-offs
status: evergreen
created: 2025-12-03
updated: 2026-06-19
tags: [cost, latency, quality, iron-triangle, model-routing]
aliases: [LLM Iron Triangle, Cost vs Quality vs Speed]
---

Every AI model selection involves the **iron triangle**: cost, latency, and quality. Optimizing any two compromises the third. Production systems escape this constraint via **dynamic routing** — using different models for different tasks.

## The three dimensions

**Cost**: Ultra-cheap (GPT-4o-mini, Gemini Flash: $0.15/$0.60 per 1M) → Balanced (GPT-4o, Gemini 2.5 Pro: $1.25–$5) → Premium (Claude Sonnet/Opus: $3–$75) → Reasoning (o1/o3: $15–$60+).

**Latency (2025 benchmarks)**: Gemini 2.0 Flash: 0.34 s TTFT, 169 TPS · GPT-4o-mini: 0.35 s, 100 TPS · GPT-4o: 0.53 s, 75 TPS · Claude Sonnet: 1.17 s, 77 TPS · o1-mini: 8–15 s · o1-preview: 15–30 s. Threshold: > 3 s TTFT causes ~40 % user abandonment in interactive applications.

**Quality gap by task type**: Simple Q&A — cheap vs premium: 85 % vs 90 % (5 % gap, marginal). Code generation: 55 % vs 86 % (31 % gap, significant). Math reasoning: 35 % vs 83 % (48 % gap, dramatic).

## Routing patterns

| Pattern | When | Savings |
|---------|------|---------|
| Static tiering | Predictable, homogeneous workload | Baseline |
| Complexity-based routing | Mixed workloads | 70–80 % |
| Cascade with validation | Quality-critical + budget | 90 %+ |
| Parallel speculation | Ultra-low latency needed | — (pays 3× cost) |

## Real cost scenarios

100k queries/month chatbot: Gemini Flash $4.50 · GPT-4o-mini $6.80 · Claude Sonnet $165 · Claude Opus $825. Smart routing (Claude Opus always = $8,250/month vs hybrid = $150/month with 88 % quality vs 95 %). The 7 % quality difference is often not worth 55× the cost.

## Cost-reduction techniques

- **Prompt caching**: 50–90 % on repeated context (large system prompts, tool definitions). Cache when system prompt > 1000 tokens and request rate > 10/min.
- **Adaptive token budgets**: limit `maxTokens` by task type — 100 for Q&A, 500 for code snippets, 2000 for articles. Saves 50–60 % on output costs.
- **Batch API**: 50 % discount for 24-hour turnaround (analytics, translation, summarization jobs).

## Avoid common mistakes

Over-provisioning: Claude Opus for "What is 2+2?" wastes 100× cost vs Gemini Flash. Under-provisioning: Gemini Flash for differential equations yields 35 % accuracy vs 85 % with o1-mini. Ignoring latency: o1-preview for a chatbot (15–30 s TTFT) causes 40 %+ abandonment.

Part of [[foundations]].

**Related:** [[when-to-use-which]] · [[model-selection]] · [[standard-models]] · [[reasoning-models]] · [[optimization]] · [[training-vs-inference]]
