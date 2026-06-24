---
type: note
title: Context Injection Strategies
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [context-injection, rag, prompt-engineering, retrieval-timing, working-memory, xml-formatting]
aliases: [rag-injection, context-placement]
---

Context injection strategy — where, when, and how information enters the prompt — determines RAG accuracy and agent coherence. Strategic placement achieves +10-43% accuracy gains through optimal role assignment, retrieval timing, structured formatting, and working memory patterns.

## Location: System vs User vs Assistant

The "lost in the middle" effect (Stanford/UW, ACL 2024) shows a U-shaped performance curve: information buried in the context center suffers −30%+ accuracy degradation. Place critical content at start or end.

**Role assignment guide:**
- **System** — agent identity, capabilities, universal rules, tool definitions. Static → fully cacheable (60-90% cost reduction).
- **User** — RAG-retrieved docs (query-specific), working memory, session constraints, the actual query.
- **Assistant** — previous responses, ReAct reasoning steps, tool execution results, self-corrections.

Mixing static instructions with dynamic RAG in the system message breaks caching and bloats prompts. Strategic distribution keeps the system message cacheable and the user message query-specific.

## Timing: When to Retrieve

**Always retrieve**: simple baseline, ~5 retrievals/query.
**FLARE (confidence-based)**: retrieve when model is uncertain; +5% accuracy.
**DeepRAG (2025)**: knowledge-boundary calibration — decompose query into subqueries, retrieve only when parametric knowledge is insufficient. Result: 0.28–1.09 retrievals/query vs 4.52 for Auto-RAG, +26.4% accuracy, 90% retrieval cost reduction.
**RAT (NeurIPS 2024)**: iterative retrieval per reasoning step — retrieve after each Chain-of-Thought thought and revise it. Results: +13.63% code generation, +16.96% math, +42.78% task planning.

## Format: XML, JSON, Markdown

Structured formats improve complex task performance 15-40% (2024). XML is recommended for RAG: clear tag boundaries, source and relevance attributes visible to the LLM. JSON suits tool results and API integration. Markdown works for debugging and simple Q&A. Plain text adds zero overhead for trivial queries.

**RankRAG (2024)**: ordering documents by relevance inside the prompt adds +18% accuracy on its own.

## Working Memory Patterns

Inject entity memory extracted from conversation turns (name, type, attributes, recency) via structured XML blocks in the user message. Importance scoring formula: `0.60 × semantic_relevance + 0.25 × recency_decay + 0.15 × explicit_importance`. **Mem0 (2025)** achieves +26% accuracy vs OpenAI Memory and 91% latency reduction.

## Advanced RAG Injection Patterns

**CRAG (2024)**: three-level confidence filter — >70% correct (decompose/recompose), 30-70% ambiguous (combine with web search), <30% incorrect (discard, use web fallback).

**ACE Framework (2025)**: agentic context playbooks that evolve via Generator → Reflector → Curator loop. Results: +12.5% (AppWorld normal), +24.5% (challenge), +8.6% (finance). Incremental delta updates prevent context collapse.

**Agent Skills (Anthropic 2025)**: three-level progressive disclosure — metadata YAML (~50 tokens, always loaded), SKILL.md body (~500-2,000 tokens, loaded on activation), supplementary files (loaded on demand). Packages domain expertise composably vs monolithic 10,000-token system prompts.

## Production Budget (128K window)

- System prompt: 5-10% (cached)
- Persistent memory: 10-15%
- Retrieved context: 30-40%
- Conversation: 30-40%
- Response buffer: 10%

Cache ordering by stability: tools (1h) → system instructions (5m-1h) → background context (5m) → RAG docs (no cache) → user query (never cache).

Part of [[context]].

## Related Notes

- [[context-management]] — prerequisite: caching and window management
- [[token-optimization]] — compression before injection
- [[system-prompts]] — system message design principles
- [[retrieval-methods]] — what gets retrieved before injection
- [[hybrid-search-reranking]] — reranking for relevance-ordered injection
- [[rag-architectures]] — end-to-end RAG pipeline
- [[memory-systems-working-memory]] — working memory entity patterns
