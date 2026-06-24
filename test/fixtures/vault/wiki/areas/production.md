---
type: area
title: Production
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [production, llm-ops, observability, debugging, optimization, cost-management]
---

Production engineering for AI agents is a distinct discipline from traditional software operations. Agents are non-deterministic, multi-step, and expensive — a single runaway loop can burn thousands of dollars before human intervention. The field has converged around three interlocking concerns: visibility into what agents are actually doing, the ability to reproduce and diagnose failures, and systematic control of cost and latency.

Observability in this context means capturing Runs, Traces, and Threads — not just service-level metrics. OpenTelemetry GenAI Semantic Conventions (2024) provide a vendor-neutral standard for span attributes across providers, with specialized platforms (LangSmith, Langfuse, Datadog, Arize Phoenix) layering agent-specific visualization on top. Crucially, the same traces that power monitoring also power evaluation: offline test datasets, online LLM-as-judge pipelines, and ad-hoc analysis all draw from production trace stores.

Debugging non-deterministic agents requires checkpoint-based time-travel: capturing full agent state — messages, variables, tool results, external API responses, exact model version — after every step, then replaying from any checkpoint to inspect or fork execution. Free-form tool outputs must be replaced with structured JSON, and external state must be cached alongside checkpoints, or replay will diverge from production behavior.

Cost optimization is achievable at 40–90% reduction through a layered stack: model routing (RouteLLM, 85% savings at 95% quality retention), prompt caching (50–90% input reduction with Anthropic/OpenAI native support), semantic caching (68% API call reduction via SCALM-style vector lookup), batch APIs (50% discount for async workloads), and token compression (LLMLingua up to 20x). At large codebase scale, Merkle tree differential sync and content-addressable embedding caches achieve 15–690x faster incremental index updates. Autonomous agents require provisioned token budgets, not ad-hoc rationing, because their consumption is sustained rather than spiky.

## Timeline

- 2026-06-19 Imported 3 notes from the source KB.

## Notes

- [[observability]]
- [[debugging]]
- [[optimization]]
