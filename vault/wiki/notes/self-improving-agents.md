---
type: note
title: Self-Improving & Meta-Learning Agents
status: evergreen
created: 2026-01-05
updated: 2026-06-19
tags: [self-improvement, meta-learning, reflexion, prompt-optimization, episodic-memory, dspy]
aliases: [meta-learning agents, self-correcting agents]
---

Self-improving agents learn from failures, optimize their own behavior, and compound capabilities over time — achieving 23–60% accuracy improvements over static baselines. The core insight is that LLMs can evaluate their own outputs and generate actionable natural-language feedback, creating a loop where each task makes the agent better.

**Four levels of self-improvement:**

1. **Error Correction (Reflexion, NeurIPS 2023)** — A three-component loop: Actor executes the task, Evaluator judges success, Reflector produces verbal analysis of failure. Insights stored in episodic memory are injected into future attempts. Results: 23–60% improvement on HumanEval, ALFWorld, HotPotQA.

2. **Prompt Evolution (DSPy/MIPROv2, 2024)** — Treats prompts as compilable code. MIPROv2 uses Bayesian optimization to jointly tune instructions and few-shot examples across a training set. Results: 13% accuracy gain on multi-stage pipelines. Requires labeled training data.

3. **Tool Selection Learning (ToolLLM / DFSDT, ICLR 2024)** — Depth-First Search Decision Tree explores tool paths and learns which APIs succeed in which contexts. Trained on 16,464 real-world APIs across 49 categories. Scores tools with exponential moving average over success/failure history.

4. **Skill Libraries (Voyager)** — Agent writes and stores reusable code skills that compound. New tasks check the library first, compose from sub-skills, then store verified new skills. Requires executable environment for verification.

**ADAS (2024)** extends this to meta-level: a meta-agent designs other agents, discovering architectures that outperform human-designed ones.

**Production rules:** cap reflection attempts (max 3), cap memory size (1,000 entries), use a cheap model (gpt-4o-mini) for evaluation to cut evaluation cost 70%, prune stale memories after 30 days. Filter infrastructure errors (timeouts, network) before triggering reflection to avoid learning spurious patterns. Memory-augmented agents show 26% accuracy boost and 90% token savings versus non-augmented baselines.

Best fit: repetitive task domains with programmatic success criteria and acceptable retry cost. Avoid for one-shot critical tasks or rapidly-changing domains where RAG is more appropriate.

Part of [[advanced]].

Related: [[reflexion-self-critique]] · [[react-pattern]] · [[memory-systems-working-memory]] · [[long-term-memory-retrieval]] · [[tool-calling]] · [[loop-control]] · [[optimization]]
