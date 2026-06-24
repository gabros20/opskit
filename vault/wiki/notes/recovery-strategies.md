---
type: note
title: Recovery Strategy Selection
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [error-recovery, retry, fallback, escalation, exponential-backoff, saga-pattern]
aliases: [recovery selection, error recovery framework]
---

Effective recovery requires matching the strategy to the error type. Retrying a planning error repeats the mistake; falling back when input is wrong fails identically; escalating every error creates alert fatigue.

## The four strategies

**Retry with exponential backoff** — for transient failures (rate limits 429, timeouts, 5xx). Use jitter to prevent thundering-herd: without randomization, multiple agents on the same backoff schedule overwhelm the recovering service simultaneously. Config: 250–750ms initial delay, 1.5–2x backoff factor, cap at 30–60s, max 3–5 attempts. Never retry 4xx client errors, auth failures, or validation errors.

**Fallback to alternative** — for persistent failures where an alternative path exists. Hierarchy: primary tool → secondary tool → cached/stale data → degraded functionality → human escalation. Provider rotation between LLM vendors (e.g., GPT-4 → GPT-3.5) dramatically improves availability during quota exhaustion. Important: fallback changes the executor, not the input — if the request itself is wrong, fallback fails identically.

**Skip with compensation (Saga pattern)** — for non-critical steps where downstream logic is independent. Each action has a defined compensating action executed in reverse order on failure (e.g., credit account if downstream inventory check fails). Use for optional enrichment steps, analytics, parallelizable tasks. Never skip steps that affect data integrity or have sequential dependencies.

**Escalate to human** — for unrecoverable failures, novel errors, compliance decisions, or when confidence falls below threshold on high-stakes operations. Quality matters: include what was attempted, what failed, what recovery was tried, and recommended action. Reserve for genuinely novel or high-stakes failures; batch non-urgent escalations.

## Decision tree

Transient? → Retry. Persistent + alternative exists? → Fallback. Non-critical step? → Skip. Otherwise → Escalate.

## Recovery budgets

Set bounds: time budget (e.g., 2 min total), retry budget (e.g., 5 attempts), cost budget (tokens/API calls), cascade budget (max 3 fallback levels). Unbounded recovery delays failure notification and wastes resources.

## Research results

- 90% reduction in failures with proper retry + exponential backoff (transient errors)
- 40% reduction in dead-ends with strategy selection based on error classification (SuperAGI)
- 3x faster MTTR with AI-driven diagnostics and correct recovery routing

Part of [[errors]].

## Related notes
- [[error-classification]] — prerequisite: classify before selecting strategy
- [[resilience-patterns]] — circuit breakers and bulkheads that complement recovery
- [[tool-validation]] — detecting silent failures that trigger recovery
- [[approval-gates]] — human escalation patterns
- [[loop-control]] — preventing runaway retry loops
- [[observability]] — logging recovery attempts for continuous improvement
