---
type: note
title: Error Classification & Taxonomy
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [error-taxonomy, agent-failures, silent-failures, multi-agent, debugging, cascading-errors]
aliases: [agent error taxonomy, failure classification]
---

Agent errors differ fundamentally from traditional software errors — they are often silent, semantic, and cascading rather than explicit exceptions with stack traces.

## Why classification matters

The same symptom (wrong output) can have different root causes requiring different fixes. Retrying a planning failure just repeats the mistake; falling back when the issue is hallucination changes nothing. Classification must precede recovery. Research shows 87% root-cause detection accuracy with automated classification, and a 24% accuracy improvement using the AgentDebug structured taxonomy.

## Five-module taxonomy (AgentDebug)

Derived from analysis of 500+ failed agent trajectories, five failure modules map directly to recovery actions:

| Module | Examples | Recovery |
|--------|----------|----------|
| **Memory** | Context loss, retrieval failure, state inconsistency | Re-fetch context |
| **Reflection** | No error recognition, no adaptation | Re-prompt with trace |
| **Planning** | Wrong task decomposition, hallucinated subtasks | Re-plan from start |
| **Action** | Wrong tool selection, invalid arguments | Re-execute with fixes |
| **System** | Rate limits, API down, OOM | Retry / fallback |

## Three-source error model (tool-using agents)

- **Input errors** — wrong arguments, usually produce explicit error messages; recovery: re-parse or validate schema
- **Context errors** — incomplete environmental information; recovery: fetch additional context
- **Tool errors** — tool executes but returns semantically wrong result with no error signal; requires cross-validation

## MAST taxonomy (multi-agent systems)

14 failure modes across specification/system design, inter-agent misalignment, and task verification/termination. Baseline: 50% average task completion across 7 popular MAS frameworks. 73% of multi-agent failures cascade from a single root cause — always trace to origin, not symptom.

## Key heuristics

- Same tool called 3+ times with same args → infinite loop (Action module)
- Output references non-existent entity → hallucination (Response stage)
- Tool returns success but state unchanged → silent failure (Tool source)
- Task incomplete after max steps → planning failure

Part of [[errors]].

## Related notes
- [[recovery-strategies]] — selecting the right fix per error class
- [[resilience-patterns]] — preventing cascades at infrastructure level
- [[tool-validation]] — detecting silent tool errors
- [[react-pattern]] — the loop where most action errors surface
- [[loop-control]] — convergence failures and infinite loops
- [[observability]] — logging and monitoring for error detection
- [[coordination-strategies]] — inter-agent misalignment (MAST)
