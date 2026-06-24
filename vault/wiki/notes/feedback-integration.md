---
type: note
title: Feedback Integration & Learning
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [rlhf, dpo, alignment, feedback-loops, model-training, agent-improvement]
aliases: [rlhf-pipeline, preference-learning]
---

Feedback integration enables agents to learn from user corrections, preferences, and ratings to improve over time. The core challenge: explicit feedback is collected in fewer than 4% of interactions — it is sparse, noisy, and can degrade performance if naively incorporated.

**Key numbers.** RLHF alignment reduces misleading/incorrect information by 40–60% (OpenAI, 2024). RLTHF (Microsoft, 2025) achieves full human-annotation-level alignment with only 6–7% of annotation effort. DPO is 40% faster and 60% cheaper than traditional RLHF with comparable results. Online iterative RLHF outperforms offline RLHF on all benchmarks.

**Feedback taxonomy.** Explicit signals: binary thumbs (3–4% response rate), star ratings (~40%), written corrections, pairwise comparisons. Implicit signals: hesitation time, regeneration requests, abandonment, follow-up action clicks, session return rate. Passive signals cover 100% of interactions vs. the 3–4% explicit rate — UI design to maximize passive collection is the highest-leverage investment.

**Training approaches.**
- *RLHF (PPO)*: SFT → reward model on preference pairs → RL policy optimization. Best for nuanced, multi-dimensional objectives.
- *DPO (Direct Preference Optimization)*: reformulates RLHF as supervised learning on preference pairs (`max log P(chosen|x) − log P(rejected|x)`). 40% faster, stable, comparable quality. Best when GPU budget is constrained.
- *Online iterative RLHF*: collects feedback from the current policy each iteration, avoiding distribution shift. Outperforms offline variants.
- *RLTHF*: LLM labels the bulk of data, humans annotate only the top 6–7% high-uncertainty samples. Pareto-efficient.
- *Safe RLHF*: separate reward model (helpfulness) and cost model (harmlessness), then constrained RL. Avoids the tension of combining objectives.

**Critical rule: never auto-train on raw feedback.** Always log → batch → filter for quality → validate against guidelines → add to curated training set. Reward hacking (signal overoptimization) is a real risk: agents game a single metric (e.g., fast response time → one-word answers → churn). Counter with multi-dimensional weighted signals balancing engagement, quality, and safety.

**Decision matrix.** Limited budget → DPO. High-stakes domain → full RLHF. Scale with cost constraints → RLTHF. Safety-critical → Safe RLHF. Continuous improvement loop → online iterative RLHF. Minimum viable data: 1,000+ validated preference pairs.

Part of [[hitl]].

Related: [[approval-gates]] · [[adaptive-autonomy]] · [[react-pattern]] · [[tool-validation]] · [[observability]] · [[self-improving-agents]]
