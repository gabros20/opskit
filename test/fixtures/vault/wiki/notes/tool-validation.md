---
type: note
title: Tool Validation & Self-Healing
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [tool-validation, silent-failures, semantic-validation, self-healing, anomaly-detection, llm-as-judge]
aliases: [self-healing agents, silent failure detection]
---

Tools can fail silently: the API returns 200 OK, the response schema is valid, but the data is wrong. 60%+ of agent issues are semantic (silent) failures, not technical errors. Status codes do not validate correctness.

## Three classes of silent failures

- **Drift** — agent takes wrong path but produces a plausible-looking answer; wastes tokens, wrong result
- **Cycles** — agent loops without progress, times out at max iterations
- **Missing details** — output parses correctly but lacks required fields

## Validation layers

**Schema validation** — JSON structure, required fields, type correctness. Catches malformed responses, not wrong ones.

**Semantic validation** — value ranges (no negative counts, dates in reasonable range), referential integrity (foreign keys point to real records), business rules (order total equals sum of line items), freshness (timestamp within expected window). This is the layer that catches valid-looking wrong data.

**Post-mutation verification** — after any write, read back state to confirm the change took effect. Cost: ~50–100ms per mutation. Essential for financial transactions, data modifications. Watch for read-your-writes issues in eventually consistent systems.

**LLM-as-validator** — generate an independent answer without the tool, compare against tool output; flag significant divergence. Simply prompting the LLM with "tools can make mistakes" improves accuracy up to 30% by reducing over-trust. Use for unstructured outputs requiring judgment.

**Anomaly detection pipeline** — extract features (call sequences, response times, result sizes, error patterns, token usage) and classify with XGBoost or SVDD. Research results: XGBoost achieves 98% accuracy on 4,275 labeled traces; SVDD achieves 96% with minimal labeled data (semi-supervised). Requires production-scale traffic.

## Multi-layer validation stack (production)

DocuSign / CrewAI pattern for mission-critical outputs: Layer 1 (LLM-as-Judge for quality/coherence) → Layer 2 (hallucination check, cross-reference against retrieved documents) → Layer 3 (rule-based scoring, schema, business rules). Each layer failure points to a distinct fix: Layer 1 → prompt/model issue; Layer 2 → retrieval/context issue; Layer 3 → logic/schema issue.

## Self-healing loop

Error detected → classify → known fix available? → apply fix (retry, broader query, cache refresh, schema re-prompt) → re-validate → pass? continue, fail? escalate. Keep failed actions in context so the agent naturally avoids repeating mistakes.

Key: log all auto-corrections. Silent corrections mask systemic issues. Alert on correction rate patterns and investigate root causes.

## Risk-based validation

Not all operations need equal rigor: display to user → schema only; internal processing → schema + basic semantic; modify user data → full validation; financial transaction → full + human review.

Part of [[errors]].

## Related notes
- [[error-classification]] — classifying the silent failures this note detects
- [[resilience-patterns]] — infrastructure-level protection complementing validation
- [[recovery-strategies]] — what to do after validation detects an error
- [[tool-calling]] — the tool execution layer being validated
- [[tool-definition]] — schema design that makes validation tractable
- [[observability]] — logging validation decisions and anomaly scores
- [[approval-gates]] — human review when validation cannot auto-resolve
