---
type: note
title: Plan-and-Execute Agents
status: evergreen
created: 2025-01-07
updated: 2026-06-19
tags: [planning, agent-architecture, token-efficiency, replanning, cost-optimization, multi-step]
aliases: [plan-execute, planner-executor]
---

Plan-and-Execute separates agent reasoning into a dedicated **planning phase** and an **execution phase**, instead of interleaving thought and action like [[react-pattern|ReAct]]. The result: 5x token efficiency (ReWOO), 40% fewer dead-end failures, and 70% cost reduction by using a powerful model for planning and a cheaper model for execution.

Part of [[planning]].

## Core Architecture

1. **Planner** (expensive model, e.g. GPT-4): generates a full step-by-step plan with explicit tool calls, dependencies, and reasoning before any action is taken.
2. **Executor** (cheap model, e.g. GPT-4o-mini): carries out each step sequentially or in parallel.
3. **Replanner** (optional): if a step fails, receives the original goal, completed steps, failure details, and remaining steps, then emits a revised plan.

The plan is a first-class artifact—inspectable, auditable, cacheable, and swappable—unlike ReAct's interleaved traces.

## Key Techniques

**Alternative plan generation**: Generate 3–5 candidate plans in parallel with explicit constraints (speed-optimized, reliability-optimized, resource-efficient). Score on feasibility, complexity, parallelism, and risk. Three alternatives is the sweet spot—40% failure reduction at only 2.1× cost. Keep runner-up plans as warm fallbacks (80% faster recovery than replanning from scratch).

**Feasibility validation**: Pre-execution scoring across six dimensions—tool availability, parameter schema, resource existence, permissions, dependency resolution, constraint satisfaction. Static + resource checks catch 72% of doomed plans in ~150 ms; a full pipeline with LLM review catches 94% but adds 800 ms. Critical failures (missing tool, bad schema) block immediately; non-critical failures adjust plan ranking.

**Fallback strategies**: Map error types (TOOL_NOT_FOUND, PERMISSION_DENIED, RATE_LIMITED, SERVICE_UNAVAILABLE, TIMEOUT, VALIDATION_ERROR) to a three-tier fallback hierarchy: step-level (retry, alternative tool, skip) → plan-level (switch alternative plan, replan, graceful degradation) → task-level (partial results, human escalation).

**ReWOO variant**: Pre-plan all tool calls with variable substitution (#E1, #E2, …), execute in batch with no observation round-trips—5× fewer tokens than ReAct, 4% accuracy gain on HotpotQA.

**LLMCompiler variant**: Compile plans into parallel execution DAGs for 3.7× latency reduction (Kim et al., ICML 2024).

## Production Numbers

| Metric | ReAct | Plan-Execute |
|---|---|---|
| Task completion | 72% | 91% |
| Token usage | 8,500 | 3,200 |
| Dead-end rate | 28% | 9% |
| Cost per task | $0.34 | $0.11 |

**Key limits**: max 3 replans, 2 consecutive replans, 2-step cooldown. Cache plans (hash of task + context, 1-hour TTL) for up to 70% planning cost reduction on repetitive workflows.

## When to Use

Use for tasks with 4+ dependent steps, audit/compliance requirements, external API dependencies, or high-stakes mutations. Avoid for 1–2-step operations, rapidly changing state, or exploratory tasks—prefer ReAct or [[tree-of-thoughts]] there.

## Related Notes

- [[react-pattern]] — the reactive alternative this pattern improves on
- [[tool-calling]] — execution layer details
- [[preflight-validation]] — the feasibility-checking sub-pattern
- [[reflexion-self-critique]] — complementary self-improvement loop
- [[tree-of-thoughts]] — multi-path planning sibling
- [[loop-control]] — convergence and budget controls
- [[error-classification]] — error taxonomy used in fallback mapping
