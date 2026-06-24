---
type: note
title: Tool Registry & Discovery
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [tool-registry, semantic-search, dynamic-selection, embeddings, tool-scaling, agent-tools]
aliases: [tool discovery, dynamic tool selection]
---

As agent capability grows, tool count scales from 5 to 50+. But LLMs have practical limits: accuracy drops noticeably beyond ~20 tools, and 50 tools consume ~5,000 context tokens before the user's question is even considered. The registry pattern centralizes tools with rich metadata and uses semantic search to dynamically select only relevant tools per query.

**Benchmarks (LangGraph, 2024):** 56% improvement in Recall@5 with vector retrieval for tool selection, 70% reduction in execution time with dynamic selection, 40% power reduction on edge devices with tool filtering.

**Selection strategy by scale:**
- **1–10 tools:** Static `AGENT_TOOLS` object, pass all tools every time
- **10–30 tools:** Metadata-enriched registry — filter by `categories`, `riskLevel`, `ioType` (`read`/`write`/`both`), `estimatedLatency`
- **30–50 tools:** Semantic discovery — embed tool descriptions with `text-embedding-3-small`, cosine-similarity rank at query time, return top-K (typically 5–7) with `minSimilarity: 0.3–0.4`
- **50+ tools:** Hierarchical two-stage — first LLM call selects domain (cms / storage / users / search), second call operates within domain tools only

**Implementation notes:** Pre-compute and cache tool embeddings at startup (saves 100–500ms per request). Always include a set of always-available tools (`help`, `cancel_operation`, `get_status`) regardless of discovery results. If semantic search returns fewer than 2 results, fall back to a broader set or prompt the user for clarification.

**Pitfall:** Description quality affects embedding quality. "Gets a page" produces a weak embedding; "Fetch a page by ID or slug, returning title, content, and metadata" produces a useful one.

Part of [[tools]].

Related: [[tool-definition]] · [[context-injection]] · [[tool-security]] · [[vector-search-embeddings]] · [[retrieval-methods]] · [[embedding-models]]
