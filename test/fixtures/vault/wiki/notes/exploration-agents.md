---
type: note
title: Exploration & Discovery Agents
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [exploration, research-agents, knowledge-mapping, hypothesis-generation, multi-source-search, discovery]
aliases: [research agents, discovery agents]
---

Exploration agents tackle open-ended research questions that require systematic investigation across many sources — not a single retrieval, but a multi-phase methodology more like detective work than RAG.

**Five-phase methodology:**

1. **Broad Scouting** — Fan-out parallel search across academic (arXiv, PubMed, Semantic Scholar), patent (USPTO, EPO), news, forums (Reddit, HackerNews), and datasets (Kaggle, HuggingFace). Credibility weights by source type: academic 0.9, patents 0.8, datasets 0.7, news 0.6, forums 0.4.

2. **Knowledge Mapping** — Extract concepts from each finding, cluster by semantic similarity into 3–7 thematic groups, identify cross-cluster connections. Clustering can be topic-based, methodology-based, timeline-based, or sentiment-based.

3. **Deep Dive Selection** — Score each cluster on four dimensions: novelty (0.3 weight), impact (0.35), feasibility (0.2), gap size (0.15). Select top 2–3 clusters for deeper investigation.

4. **Hypothesis Generation** — Synthesize each deep-dive cluster into 1–3 testable, falsifiable hypotheses that connect multiple findings. Good hypotheses are specific, novel, impactful, and come with proposed experiments.

5. **Iteration** — Repeat with refined queries derived from first-pass findings until 3+ high-confidence hypotheses (>0.7) are produced or budget is exhausted.

**Resource profile:** comprehensive exploration takes 40+ minutes with multiple parallel agents and high token usage. Three budget tiers: quick (10 min, 50K tokens, 1 iteration), standard (30 min, 150K tokens, 2 iterations), comprehensive (60 min, 500K tokens, 3 iterations).

**Production rules:** set hard time/token/iteration caps to prevent infinite exploration; require minimum coverage across source types to avoid source bias; explicitly search for contradicting evidence to counter confirmation bias; cache scouting results keyed by query hash for reuse; stream progress updates to keep users informed during long runs.

Not suitable for simple factual lookups (use RAG), time-critical responses (< seconds), or well-documented topics with a single authoritative source.

Part of [[advanced]].

Related: [[coordination-strategies]] · [[orchestration-patterns]] · [[vector-search-embeddings]] · [[retrieval-methods]] · [[hybrid-search-reranking]] · [[self-improving-agents]] · [[plan-and-execute]]
