---
type: area
title: Errors
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [error-recovery, resilience, agent-failures, silent-failures, fault-tolerance]
---

Agent failures are categorically different from traditional software errors. They are often silent — returning plausible-looking but incorrect outputs — semantic, and cascading: a single root cause in one agent can propagate through multi-step reasoning chains before any symptom appears. 60%+ of agent issues are semantic, not technical, which means error rates and HTTP status codes miss the majority of real problems.

Effective error handling starts with classification. The Five-Module Taxonomy (Memory, Reflection, Planning, Action, System) derived from 500+ failed trajectories maps each failure type to a distinct recovery action. In multi-agent systems, the MAST taxonomy identifies 14 failure modes; 73% of those failures cascade from a single root cause, so tracing to origin rather than chasing the visible symptom is essential.

Recovery strategy selection is a decision problem, not a default. Retry with exponential backoff and jitter handles transient failures (rate limits, 5xx); fallback to an alternative handles persistent unavailability; skip with saga-pattern compensation handles non-critical steps; escalation with full context handles novel or compliance-sensitive failures. Applying the wrong strategy wastes resources and compounds errors.

Infrastructure-level resilience — circuit breakers, bulkheads, and timeouts — prevents cascades before they start. Circuit breakers reduce cascade propagation by 80%+ and cut mean time to recovery by 40%. Every external call needs a timeout; per-tool circuit breakers isolate dependency failures. Tool validation closes the remaining gap: post-mutation verification, schema and semantic validation, LLM-as-validator skepticism, and anomaly detection (XGBoost: 98% accuracy) catch the silent failures that infrastructure patterns cannot see.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[error-classification]]
- [[recovery-strategies]]
- [[resilience-patterns]]
- [[tool-validation]]
