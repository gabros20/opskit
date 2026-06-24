---
type: note
title: Preflight Validation
status: evergreen
created: 2026-01-07
updated: 2026-06-19
tags: [preflight, validation, fail-fast, schema-validation, saga-pattern, design-by-contract]
aliases: [pre-execution validation, action validation]
---

Preflight validation verifies that an action will succeed _before_ committing resources—catching 70–80% of failures in the cheapest possible way. Without it, 35% of tool calls fail in production, wasting an average of 2,400 tokens per failure and causing partial state mutations. With it: runtime failures drop from 35% to 8%, auto-recovery rate rises from 15% to 72%, and wasted tokens drop to zero.

Part of [[planning]].

## Five Check Categories (ordered by cost)

1. **Tool availability** (<1 ms, static): does the tool exist and is it enabled? Fuzzy-match suggestions on miss reduce retries by 60%. Tool hallucination accounts for 10–15% of agent failures.
2. **Parameter schema** (<5 ms, CPU): Zod/Pydantic validation—required fields, types, formats, cross-field refinements. AI SDK 6 strict mode (default) reduces schema-related failures by 90%. Always run schema _first_ and short-circuit on failure; no point querying the DB if the input is malformed.
3. **Resource existence** (20–100 ms, cacheable): batch-check all referenced IDs in a single DB round-trip (not N individual queries). Cache positive results for 30–60 s (80–90% hit rate). 40–60% of production failures are resource-not-found errors.
4. **Authorization** (10–50 ms, cacheable): user role, rate limits, feature flags.
5. **Constraint satisfaction** (30–150 ms, partial cache): uniqueness (slug collision), valid state transitions (draft → published → archived), relationship rules (circular reference prevention), business invariants (published post requires featured image).

## Validation-to-Suggestion

Generic error messages produce 15% auto-recovery. Specific, actionable suggestions—fuzzy-matched IDs, recent resources of the same type, valid enum options, corrective-action pointers ("upload an image first using uploadImage")—push recovery to 72% (+380%). Limit suggestions to 1–3, ranked by specificity.

## Saga Transaction Pattern (SagaLLM, VLDB 2025)

For multi-step workflows, pair every operation with a compensating operation. On failure, compensations execute in reverse order to restore consistent state:

```
createUser → createOrder → chargePayment → [FAILS]
Rollback: refundPayment ← cancelOrder ← deleteUser
```

SagaLLM demonstrated 78% reduction in workflow failures through transactional safeguards. State is tracked across three orthogonal dimensions: application state (entities, checkpoints), operation state (inputs/outputs, reasoning chains), and compensation metadata.

## Key Numbers

| Check type | Latency | Cache TTL |
|---|---|---|
| Tool availability | <1 ms | Static |
| Schema validation | <5 ms | N/A |
| Resource existence | 20–100 ms | 30–60 s |
| Authorization | 10–50 ms | Session TTL |
| Constraints | 30–150 ms | 10–30 s |

Total preflight overhead: 50–200 ms vs 2–5 s for a failed execution.

## Framework Notes

- **AI SDK 6**: strict mode on by default; `needsApproval` callback for dynamic human-in-the-loop on destructive operations.
- **Instructor** (Python): automatic retry with validation errors fed back to the LLM; 85% auto-recovery rate without manual handling.
- **Guardrails AI**: 100+ pre-built validators, real-time streaming validation with automatic correction.

## When to Apply

Full preflight for mutations, resource-dependent operations, privileged actions, multi-step saga workflows. Schema-only for read queries. Skip entirely for latency-critical read paths (<200 ms budget) and truly idempotent operations.

## Related Notes

- [[plan-and-execute]] — preflight is the feasibility-scoring sub-pattern of plan-and-execute
- [[tool-calling]] — execution layer that preflight gates
- [[tool-validation]] — broader tool self-healing patterns
- [[error-classification]] — taxonomy that maps to fallback chains
- [[recovery-strategies]] — what happens after preflight catches a failure
- [[approval-gates]] — human-in-the-loop escalation path
