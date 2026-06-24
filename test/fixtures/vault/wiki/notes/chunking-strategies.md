---
type: note
title: Chunking Strategies
status: evergreen
created: 2025-01-08
updated: 2026-06-19
tags: [chunking, rag, retrieval, text-splitting, contextual-retrieval, document-processing]
aliases: [text splitting, document chunking]
---

Chunking — how documents are split before embedding — has an outsized impact on RAG quality. Wrong strategy can cause up to 9% recall loss (Chroma 2024) or 67% more retrieval failures (Anthropic 2024 contextual retrieval benchmark).

**Core strategies and performance:**

| Strategy | Recall | Cost | Notes |
|---|---|---|---|
| LLM-based chunking | 0.919 | $$$$ | Highest quality, slowest |
| ClusterSemanticChunker | 0.913 | $$ | Embedding-based topic splits |
| RecursiveCharacterTextSplitter | 0.881–0.895 | $ | Production default |
| Fixed-size (512 tokens) | 0.85–0.87 | $ | Simple, needs overlap |
| Page-level | 0.648* | $ | NVIDIA FinanceBench winner; best for PDFs |
| Late chunking | +15–25%** | $$ | Jina AI embed-then-chunk |
| Contextual Retrieval | +67%*** | $$$ | Anthropic; LLM prepends context per chunk |

*Different evaluation protocol. **Over baseline on cross-reference queries. ***Reduction in failures with reranking.

**Production default:** `RecursiveCharacterTextSplitter` at **400–512 tokens, 10–20% overlap**, using separators `["\n\n", "\n", " ", ""]`. Use token-based counting (tiktoken), not character-based — 15–20% more accurate.

**Document-specific guidance:**
- **Markdown:** Split on heading hierarchy (`\n## `, `\n### `).
- **Code:** Split on `class`/`def`/`function` boundaries, not line counts.
- **PDFs:** Convert to Markdown first (Docling, Azure Document Intelligence), then page-level or section chunking.
- **Tables:** Extract as separate chunks in Markdown or JSON.

**Contextual Retrieval (Anthropic 2024):** Prepend 50–100 tokens of LLM-generated document context to each chunk before embedding. Alone: 35% fewer failures. With BM25: 49%. With reranking: 67%.

**Late chunking (Jina AI 2024):** Embed the full document, then split the resulting embedding sequence. Requires 8K+ token context model and mean pooling. Prevents "the city" losing its Berlin reference across chunk boundaries.

Overlap is non-negotiable: never use fixed-size chunking without 10–20% overlap. Version your chunks — changing strategy requires full re-embedding.

Part of [[rag]].

**Related:** [[vector-search-embeddings]] · [[retrieval-methods]] · [[rag-architectures]] · [[injection-strategies]] · [[token-optimization]] · [[context-management]]
