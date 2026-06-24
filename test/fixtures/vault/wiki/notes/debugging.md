---
type: note
title: Debugging Techniques
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [debugging, checkpoint-replay, time-travel, agent-diagnostics, state-inspection, llm-ops]
aliases: [agent debugging, time-travel debugging]
---

AI agents are non-deterministic — traditional debugging fails because the same input can produce different outputs across runs (LLM temperature, context drift, changed external data, provider weight updates). Multi-step agent tasks have only a 30–35% success rate without proper debugging infrastructure (CMU/Salesforce 2024). Visual trace inspection reduces debugging time by 80% (Agent Prism).

Part of [[production]].

## Core Concept: Time-Travel Debugging

Capture complete agent state as a **checkpoint** after every step. Load any checkpoint later to inspect, modify, fork, or re-execute from that exact point.

**Checkpoint structure** captures: full message history, working memory variables, current tool and prior tool results, exact model version (`gpt-4o-2024-11-20`, not just `gpt-4o`), temperature/maxTokens/system prompt, and cached external API responses and DB snapshots needed for deterministic replay.

**Replay modes**:
| Mode | Purpose |
|------|---------|
| Inspect Only | Understand failure without executing |
| Continue | Resume from checkpoint to test a fix |
| Fork | Branch to A/B test alternative decisions |
| Modify & Replay | Edit state then re-run for what-if analysis |

## Step-by-Step Execution

Pause before/after LLM calls, before/after each tool call, and at state transitions. At each interrupt point: view full state, edit variables, skip or inject a response. Tooling: **LangGraph Studio** (LangGraph workflows), **LangSmith** (LangChain), **Langfuse** (self-hosted), **Agent Prism** (open-source custom visualization).

## LLM Call Inspection Checklist

| Check | What to look for |
|-------|-----------------|
| System prompt | Missing instructions, conflicting guidance |
| Context window | Truncation, missing critical info |
| Tool definitions | Schema errors, unclear descriptions |
| Token usage | Near limit? Truncation risk? |
| Temperature | Too random vs too deterministic |

## Checkpoint Storage Strategy

- **Dev**: SQLite (fast, local, zero setup)
- **Prod**: PostgreSQL (durable, queryable, team-accessible)
- **High-throughput**: Redis with TTL (fast writes, auto-expiry)

Retention: successful traces 7 days, failed 30 days, user-flagged 90 days, compliance per policy.

## Determinism Requirements

1. Enforce **structured JSON tool calls** — free-form parsing breaks replay
2. Cache all external API responses and DB queries in the checkpoint
3. Pin exact model version in every checkpoint
4. Use consistent random seeds where supported

## Debug Workflow

`Identify trace → Locate divergence step → Inspect checkpoint → Hypothesize → Fork + modify → Fix codebase → Replay original → Add regression test → Update alerts`

## Related Notes

- [[observability]] — trace/log infrastructure that feeds debugging
- [[optimization]] — cost gains informed by debugging findings
- [[react-pattern]] — the step loop being checkpointed
- [[tool-calling]] — tool call replay and schema validation
- [[resilience-patterns]] — recovery patterns that debugging informs
- [[state-persistence-checkpointing]] — broader checkpointing concepts
- [[error-classification]] — classifying failures found during debugging
