---
type: note
title: Prompting Techniques
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [chain-of-thought, few-shot-learning, zero-shot, self-consistency, reasoning-models, instruction-design]
aliases: [prompt engineering, CoT prompting]
---

# Prompting Techniques

Part of [[prompts]].

Prompting techniques transform generic LLMs into reliable, task-specific tools. The foundational layer is **instruction design**: the CLEAR framework (Concise, Logical, Explicit, Adaptive, Reflective) structures prompts by specifying role, context, output format, constraints, and clear separators. 78% of AI project failures stem from poor human–AI communication.

**Few-shot learning** provides 2–10 in-context examples — "show, don't tell." Even one well-chosen example improves accuracy 20–40%. Quality beats quantity: 5 good examples outperform 20 mediocre ones. The Signal-Derived Few-Shot pattern (Wangoo 2026) ranks examples by `semantic_similarity × signal_quality_score`, using behavioral signals (response time, abandonment, sentiment) to continuously improve without model retraining.

**Chain-of-Thought (CoT)** prompting externalizes working memory as text: +235% on GSM8K math, +50–400% on complex reasoning tasks. Zero-Shot CoT adds "Let's think step by step" for a 20–50% boost at ~1.1x token cost. **Chain of Draft** (Zoom 2025) delivers the same accuracy as CoT with 80% fewer tokens (78.6% reduction on GSM8K, 92.4% on sports Q&A) by constraining each reasoning step to 5 words.

**Self-consistency** generates 5–10 diverse reasoning paths and majority-votes the answer: +7–18% accuracy at 3–10x cost. The sweet spot is 5–7 paths; difficulty-adaptive sampling (Wang et al. 2024) cuts cost 65% by routing easy questions to single-path. **Graph of Thoughts (GoT)** models reasoning as DAGs: +62% quality on sorting vs Tree of Thoughts, +46.2% on GPQA with Adaptive GoT.

**2025 shift**: Reasoning models (o1, o3 at 96.7% AIME 2024, Claude 3.7 Sonnet) handle CoT natively — explicit "think step by step" may be redundant or counterproductive for frontier models. Always test technique against your specific model.

| Technique | Accuracy Gain | Token Cost |
|---|---|---|
| Few-Shot | +20–40% | 2–3x |
| CoT | +50–400% | 3–5x |
| Zero-Shot CoT | +20–50% | 1.1x |
| Self-Consistency (5) | +7–18% | 5x |
| Chain of Draft | Same as CoT | 0.2x CoT |

## Related Notes

- [[system-prompts]]
- [[prompt-management]]
- [[sampling-parameters]]
- [[react-pattern]]
- [[reasoning-models]]
- [[context-windows]]
- [[token-optimization]]
