---
type: note
title: Resilience Patterns
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [circuit-breaker, bulkhead, timeout, cascading-failures, fault-isolation, production]
aliases: [fault tolerance patterns, circuit breaker pattern]
---

Naive retry logic amplifies load on degraded services, turning partial outages into total outages. Resilience patterns — circuit breakers, bulkheads, and timeouts — contain failures at their origin and fail fast when recovery is unlikely.

## Circuit breaker

Three states: CLOSED (normal), OPEN (reject all immediately), HALF-OPEN (limited test traffic). Transitions: consecutive failures exceed threshold → OPEN; cooldown elapses → HALF-OPEN; test succeeds → CLOSED; test fails → OPEN again.

Config: failure threshold 5 consecutive OR 50% in 100-request window; open duration 30–60s; half-open test count 1–3 requests. Assign per-tool circuits so a slow search API does not block fast database lookups. Without circuit breakers, retry attempts can 10x load on degraded services; circuit breakers reduce cascade propagation by 80%+.

## Bulkhead

Limits concurrent requests per dependency so one slow service cannot exhaust shared resources. Named after ship compartments containing flooding.

- Thread-pool bulkhead: dedicated worker pools per dependency (e.g., 5 for search API, 10 for database, 3 for LLM)
- Semaphore bulkhead: lighter-weight concurrent-call cap, common in async Node.js/TypeScript agents

Typical concurrency limits: fast APIs <100ms → 20–50; slow APIs 1–5s → 5–10; LLM calls → 3–10; database → 10–20.

## Timeout

Every external call must have a timeout — no exceptions. Layer timeouts: connection (3–5s) → read/response (10–30s) → overall request (30–60s) → agent step (60–120s). Calibrate at p99 latency × 1.5 per service; a blanket 30s timeout for a 50ms lookup wastes user time and a 5s timeout for a 10s LLM call creates false failures.

Timeout and retry interact: with a 60s total budget, 15s per-attempt timeout, and 3 attempts, total elapsed is 48s — within budget.

## Combining all three

Request arrives → circuit open? fail immediately → bulkhead full? queue/reject → execute with timeout → on success, return result. Fail-fast patterns reduce mean time to recovery by 40%.

## Key pitfalls

- Same threshold for all services — calibrate per baseline error rate (set at 3–5x baseline)
- Circuit breaker without fallback — define degraded behavior before opening the circuit
- Global circuit for a multi-instance service — use per-instance circuits or route via load-balancer health checks

Part of [[errors]].

## Related notes
- [[recovery-strategies]] — retry/fallback strategies that feed into resilience design
- [[error-classification]] — classifying failures that trigger circuit state changes
- [[tool-validation]] — detecting silent failures before they cascade
- [[observability]] — monitoring circuit state changes as high-signal events
- [[tool-calling]] — external tool calls are the primary targets for these patterns
- [[optimization]] — cost and latency implications of timeout and bulkhead tuning
