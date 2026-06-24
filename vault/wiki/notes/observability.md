---
type: note
title: Observability & Monitoring
status: evergreen
created: 2026-01-27
updated: 2026-06-19
tags: [observability, monitoring, opentelemetry, tracing, cost-tracking, llm-ops]
aliases: [agent monitoring, llm telemetry]
---

Production AI agents require specialized observability because they are non-deterministic, multi-step, and expensive — a single runaway agent can burn $1,000 in minutes. Effective observability captures the reasoning process, not just outcomes.

Part of [[production]].

## Three Pillars

**Traces, Metrics, Logs** — the standard triad — applied to agents means:

- **Traces**: request flow across steps, tool calls with params, LLM calls with prompts, state transitions
- **Metrics**: token usage (in/out/cached), latency percentiles (p50/p95/p99), cost per request, success/error rates
- **Logs**: structured JSON with `traceId` + `stepId` fields for correlation across distributed systems

## OpenTelemetry GenAI Semantic Conventions

The 2024 industry standard defines consistent span attributes across providers: `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.provider.name`, `gen_ai.operation.name`. Span hierarchy: `ai.agent.execute` → `ai.generateText` → `gen_ai.choice` → `ai.toolCall`.

Platforms: **LangSmith** (best for LangChain), **Langfuse** (open-source/self-hosted, 50K free/month), **Datadog LLM Observability** (enterprise), **Arize Phoenix + OpenLLMetry** (open-source).

## Agent Observability Primitives (LangSmith 2026)

Three granularities for debugging reasoning, not code:

| Primitive | Scope | Debug question |
|-----------|-------|----------------|
| **Runs** | Single LLM call | Why did the agent call `edit_file` at step 23? |
| **Traces** | Full agent execution | Where in 200 steps did the agent go off track? |
| **Threads** | Multi-turn conversation | What accumulated context caused turn 11 to fail? |

The same traces power offline evaluation datasets, online LLM-as-judge checks, and ad-hoc analysis. 6-7% annotation effort achieves full alignment quality via RLTHF (Microsoft 2025).

## Key Metrics and Alerting

- **TTFT** target <500ms, alert >1s; **p95 latency** target <5s, alert >10s
- Cost thresholds: warn at 80% daily budget, critical at 95%, flag single requests >$1, rate-limit users at >$50/day, investigate 50%+ spike vs 7-day average
- Success rate target >95%; tool call success >98%; hallucination rate <5%

## Best Practices

1. Instrument from day one — retrofitting is painful (60–80% MTTR reduction)
2. Alert on percentiles, not averages — p99 reveals real tail pain (e.g., p99 = 45s while avg = 1.5s)
3. Attribute costs granularly by `userId`, `featureId`, `teamId`, `environment`
4. Implement hard caps: max tokens per request, max cost per user per day, circuit breakers
5. Disable full prompt logging in production (100K req/day × 2KB = 200GB logs/day + PII risk)

## Related Notes

- [[debugging]] — checkpoint replay and time-travel debugging
- [[optimization]] — cost reduction strategies enabled by observability data
- [[react-pattern]] — the execution loop being traced
- [[tool-calling]] — tool call spans captured in traces
- [[error-classification]] — error rates surfaced by monitoring
- [[resilience-patterns]] — circuit breakers referenced in cost caps
- [[loop-control]] — loop convergence detectable via trace anomalies
