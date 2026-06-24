---
type: note
title: Tool Calling & Execution
status: evergreen
created: 2026-01-27
updated: 2026-06-19
tags: [tool-calling, function-calling, zod-schema, mcp, tool-registry, dynamic-tool-search]
aliases: [function calling, tool use]
---

Tool definitions are the contract between LLMs and executable functions. Well-structured tools with Zod schemas, clear descriptions, and structured error responses are the primary lever for agent reliability — going from ~60% to 95%+ task completion.

## Tool Anatomy

Every tool has three pillars: **description** (when/what/output), **inputSchema** (Zod-typed parameters), and **execute** function (implementation with validation). Descriptions matter more than names; LLMs read descriptions to decide selection. Template: `[ACTION] [WHAT] [by PARAMS]. Use when [SCENARIO]. Returns [FORMAT].`

## Key Research Numbers

- 90%+ tool selection accuracy with clear descriptions (Anthropic 2024)
- 60–80% error reduction with proper Zod schemas (Scalifiai 2025)
- 85% token reduction with deferred tool loading (Anthropic Tool Search)
- 37% token reduction with programmatic tool calling (Anthropic)
- 60% of agent failures are silent — tool returns success but had no effect (read-after-write verification catches 85%)

## Context Injection

AI SDK v6 `experimental_context` passes services (DB, CMS, logger, user session) into tool execute functions without global state. Dynamic tool selection based on auth status or permissions is a first-class pattern.

## Tool Registry

Centralized catalog metadata (category, riskLevel, keywords, requiresApproval) enables 30–50% duplication reduction and permission-gated tool access. 79% enterprise adoption of registries in 2025.

## Dynamic Tool Search

Beyond ~30 tools, static loading bloats context and degrades selection. Two-stage retrieval: Stage 1 fast candidate retrieval (vector search with e5-small at 16 ms, or BM25); Stage 2 cross-encoder reranking to top-5.

- **Tool2Vec**: Usage-based embeddings (not description-based) → +27–30 Recall@K vs baseline
- **ToolShed**: Example-query embeddings → +46–56% Recall@5
- **Anthropic Tool Search Tool** (2025): `tool_search_tool_bm25_20251119` or `tool_search_tool_regex_20251119`; `defer_loading: true` for lazy loading; 85% token reduction, +8.6 to +25 accuracy points (LiveMCPBench 2025)

LiveMCPBench (70 servers, 527 tools, 95 tasks): Claude-Sonnet-4 leads at 78.95%; retrieval errors cause ~45% of all failures.

## Fake Tool Calls

Inject pre-fetched data as if the model requested it via `convertToModelMessages()` — useful for pre-loading known context (user prefs, weather) without forcing the model into specific tool calls.

Part of [[agents]].

## Related

- [[agent-fundamentals]] — Agent architecture and CodeAct pattern
- [[react-pattern]] — ReAct execution loop that drives tool calls
- [[loop-control]] — Stop conditions and convergence
- [[tool-definition]] — Tool schema patterns (cross-area)
- [[tool-registry]] — Registry and discovery (cross-area)
- [[tool-security]] — Safety and approval gates
- [[retrieval-methods]] — Retrieval techniques for dynamic tool search
