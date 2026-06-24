---
type: note
title: Loop Control & Convergence
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [loop-control, convergence, stuck-detection, early-exit, entropy, agent-safety]
aliases: [agent termination, convergence detection]
---

Without explicit loop control, agents spin indefinitely — $0.05/step × 100+ steps = $5+ wasted, with no useful output. 85% of agent failures stem from unclear stopping conditions; 60% of failures involve action repetition loops.

## Layer 1: Hard Step Limits

Task-type baselines: simple Q&A 3–5 steps, data retrieval 5–10, CMS operations 8–15, debugging 15–25, research 25–50, code generation 30–60. AI SDK v6 pattern: `stopWhen: stepCountIs(N)`. Start conservative (10–15) and tune from telemetry; target <5% limit-hit rate with 40–70% average utilization.

## Layer 2: Convergence Detection

Three patterns: (1) **Explicit finish tool** — agent calls a `finish` tool when done (confidence 1.0); (2) **Text response** — no tool calls in the last step signals completion (confidence 0.9); (3) **Goal-state verification** — compare current state against tracked goals.

**ReflAct** (EMNLP 2025): Shifts reasoning from "plan next action" to "continuously reflect on state vs. goal." Result: 93.3% success on ALFWorld (GPT-4o) vs 57% ReAct baseline — 36.4% improvement. The reflection process itself (not just verbalising state) drives gains.

## Layer 3: Stuck Detection

Detect loops with a sliding action-hash window (size 5): exact repetition (same action ≥3 times), A-B-A-B oscillation, or no measurable state change. **Autono framework** (2025): probabilistic abandonment using exponential penalty `p = (β × p) mod 1`; success 96.7–100% on single/multi-step tasks.

## Layer 4: Early Exit

**Entropy-based stopping**: Shannon entropy from token-level logprobs as confidence signal. Low entropy → high confidence → stop early. Achieves 25–50% compute savings. **DEER** (2025): monitors reasoning transition points → 19–80% CoT sequence reduction. **REFRAIN** (2025): adaptive stopping → 20–55% token reduction.

## Ralph Loop Pattern (Long-Running Agents)

For agents that exceed context window limits: Initializer writes a plan file and tracking file to disk. Sub-agent reads plan, executes one item, commits progress via git, runs verification hook, repeats. Context survives window limits; git provides audit trail; failures are recoverable.

## Multiple Stop Conditions (AI SDK v6)

Compose conditions: `stopWhen: [stepCountIs(20), hasToolCall('finish'), hasToolCall('needsHuman')]` — first trigger wins. Progressive pattern: soft-limit warning at step 10 with checkpoint serialisation, hard stop at 20.

## Production Data

96.5% of agents converge within 3 iterations. Monitoring targets: limit-hit rate <5%, avg utilization 40–70%.

Part of [[agents]].

## Related

- [[react-pattern]] — The execution loop being controlled
- [[agent-fundamentals]] — Agent architecture context
- [[tool-calling]] — Tool design affecting loop behaviour
- [[reflexion-self-critique]] — Self-reflection for convergence
- [[error-classification]] — Error taxonomy guiding retry logic
- [[recovery-strategies]] — What to do when stuck
- [[state-persistence-checkpointing]] — Checkpointing in long-running loops
