---
type: note
title: Tree of Thoughts
status: evergreen
created: 2026-01-07
updated: 2026-06-19
tags: [tree-of-thoughts, multi-path-reasoning, mcts, search-algorithms, test-time-compute, branching]
aliases: [ToT, multi-path exploration]
---

Tree of Thoughts (ToT) maintains a tree of partial solutions and explores multiple reasoning paths simultaneously, evaluating intermediate states and backtracking from dead ends. Canonical result: 4% → 74% on Game of 24 (Yao et al., NeurIPS 2023). Cost: 10–50× a single Chain-of-Thought call—justified for high-stakes, complex reasoning where single-path approaches fail.

Part of [[planning]].

## Four Architectural Components

1. **Thought decomposition** — break the problem into discrete intermediate steps; each node is a coherent reasoning unit representing partial progress.
2. **Thought generation** — _sample strategy_ (independent samples at temperature > 0.7, parallelizable, high diversity) or _propose strategy_ (sequential deliberate proposals, higher quality, better for structured problems). Typical branching factor k = 3–5.
3. **State evaluation** — scalar score (0–1), sure/maybe/impossible classification, majority voting across paths, or execution-based feedback (test results). Process Reward Models (PRM) trained at step level outperform Outcome Reward Models: 78.2% vs 72.4% on math tasks.
4. **Search strategy** — BFS (top-b beam), DFS with backtracking, Best-First (priority queue by score), or MCTS (UCB1 formula: exploitation = Q/N, exploration = C × √(ln N_parent / N), C = √2).

## Key Variants

**LATS** (Zhou et al., ICML 2024): combines MCTS with LM-powered value functions and self-reflection. HumanEval 67% → 92.7% with GPT-4 (k=5, 8 iterations). Grounded in external tool execution, reducing hallucinations.

**rStar** (Microsoft, 2024): generator SLM + discriminator SLM mutual consistency. LLaMA2-7B 12.51% → 63.91% on GSM8K (+51.4%). Five human-like actions: propose, generate remaining steps, decompose into sub-questions, answer sub-questions, rephrase.

**rStar2-Agent** (2025): 14B model matches DeepSeek-R1 671B using agentic RL—48× smaller, trained in one week.

**Graph of Thoughts** (GoT): arbitrary graph instead of tree enables path merging and feedback loops; +62% quality on sorting, >31% fewer tokens than ToT.

**ToTRL** (Chen et al., 2025): RL training on puzzle games teaches models _when_ to branch autonomously—emergent ToT behavior, transfers to math benchmarks (AIME 2025: 0.633).

## Cost vs. Benefit

| k | Cost | Typical use |
|---|---|---|
| 1 | 1× | CoT baseline |
| 3 | 3× | Standard tasks |
| 5 | 5–15× | Complex multi-step |
| 10+ | 50–100× | Strategic/creative; rarely justified |

**Cascade architecture** (production best practice): attempt CoT first (1×, 70% of problems solved), then CoT-SC k=5 (5×, 20% more), then full ToT/LATS (50×, hardest 10%). Average cost ≈ 6.7× vs 50× uniform.

**Model routing**: generate thoughts with a cheap model (GPT-4o-mini), evaluate/verify with a premium model—60–80% cost reduction.

**Test-time compute scaling**: OpenAI o1 (93% AIME 2024 with 1,000 reranked samples), o3 (96.7% AIME 2024). Adaptive allocation—easy problems 1–2×, hard problems 50–100×—gives 4× efficiency over uniform best-of-N.

## Pruning Strategies

- **Beam search**: keep top-b at each level; b = 5–10 in production.
- **Score threshold pruning**: prune if score < 0.2 (absolute) or < 50% of best sibling (relative). Moderate threshold (0.2–0.3) saves 50–60% nodes with <3% quality loss.
- **Depth limit**: always set as safety net (k^MAX_DEPTH worst-case nodes).
- **Dead-end detection**: LLM classification "sure/maybe/impossible"; prune if p(dead-end) > 0.8.

## When to Use

High-stakes code generation, mathematical proofs, legal analysis, long-horizon planning. Not justified for chatbots, simple Q&A, real-time applications (<5 s latency), or budget-constrained deployments.

## Related Notes

- [[plan-and-execute]] — prerequisite planning architecture
- [[react-pattern]] — simpler alternative for reactive tasks
- [[reflexion-self-critique]] — complementary iteration-based improvement
- [[reasoning-models]] — o1/o3 internalize ToT-like search via RL
- [[sampling-parameters]] — temperature and k control thought diversity
- [[loop-control]] — budget limits and convergence criteria
- [[retrieval-methods]] — for caching and reusing thought evaluations
