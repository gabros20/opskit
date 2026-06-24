---
type: index
title: Vault Index
updated: 2026-06-19
---

This is the map of the vault. Each area hub below is the single source of compiled truth for its domain — start here, follow links to individual notes.

---

## Core Concepts

| Area | Description |
|------|-------------|
| [[foundations]] | LLM internals, model landscape, embeddings, sampling, token economics |
| [[prompts]] | Prompting techniques, system-prompt design, prompt management at scale |
| [[context]] | Context windows, caching, compression, and injection strategies |

## Building Agents

| Area | Description |
|------|-------------|
| [[agents]] | Agent fundamentals, the ReAct loop, tool calling, convergence |
| [[planning]] | Plan-and-execute, tree of thoughts, reflexion, preflight validation |
| [[tools]] | Tool definition, schema design, registry, security boundaries |
| [[memory]] | Working memory, long-term retrieval, subgoal memory, checkpointing |

## Retrieval & Knowledge

| Area | Description |
|------|-------------|
| [[rag]] | Chunking, vector search, retrieval methods, hybrid search, RAG ops |

## Reliability & Production

| Area | Description |
|------|-------------|
| [[errors]] | Error taxonomy, recovery strategies, resilience patterns, self-healing |
| [[hitl]] | Approval gates, feedback integration, adaptive autonomy |
| [[production]] | Observability, debugging, cost and performance optimization |
| [[multi-agent]] | Orchestration patterns, agent communication, coordination strategies |

## Frontier Topics

| Area | Description |
|------|-------------|
| [[advanced]] | Self-improving agents, code generation, multimodal, exploration agents |

---

## Non-wiki layers

- `tasks/` — active / waiting / done task files (T-YYYYMMDD-NN)
- `journal/` — daily notes at `journal/YYYY/MM/YYYY-MM-DD.md`
- `wiki/conventions.md` — normative filing rules for this vault
- `wiki/decisions.md` — append-only ADR log
