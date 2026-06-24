---
type: note
title: Reflexion & Self-Critique
status: evergreen
created: 2025-01-07
updated: 2026-06-19
tags: [reflexion, self-critique, verbal-reinforcement, episodic-memory, iteration-control, code-generation]
aliases: [reflexion, self-refine]
---

Reflexion is a verbal reinforcement learning pattern (Shinn et al., NeurIPS 2023): agents generate output, evaluate it against explicit criteria, store a natural-language reflection in episodic memory, and refine in the next attempt—without any weight updates. Benchmarks: +22% on AlfWorld, +20% HotPotQA, +11% HumanEval (80.1% → 91.0% pass@1).

Part of [[planning]].

## Core Loop: Generate → Critique → Refine

**Actor** produces output given the task and any prior reflections. **Evaluator** scores the output (binary pass/fail, scalar 0–10, multi-dimensional, or descriptive). **Self-Reflection Generator** analyzes the failure and produces a lesson in natural language. **Episodic Memory** stores lessons that are injected into the actor's context on the next attempt, preventing repeated mistakes.

The loop terminates when the evaluator returns success, a target score is reached, improvement stagnates below a threshold (e.g. <0.02 delta), or a hard iteration cap is hit.

## Critical Constraint: External Feedback Is Essential

Pure self-correction without external verification _degrades_ output—GPT-4 GSM8K drops from 92% to 89% when asked to self-correct reasoning without feedback (Huang et al., ICLR 2024). External signals (test execution, an API validator, an LLM judge with a rubric, environment feedback) are required for Reflexion to help rather than hurt.

## Iteration Economics

Research shows consistent diminishing returns:
- Iteration 1: ~65% of total improvement
- Iteration 2: +20–25%
- Iteration 3: +5–10%
- After iteration 3: near-zero or negative

**Hard limit**: maxIterations = 3. Always track scores across iterations and return the _highest-scoring_ output, not the last—later iterations can regress.

## Adaptive Reflection Depth

| Score | Strategy |
|---|---|
| ≥ 0.9 | Accept, store success reflection |
| 0.7–0.9 | Light refinement, one more iteration |
| 0.4–0.7 | Deep reflection, consider alternative approach |
| < 0.4 | Escalate or pivot; if ≥ 3rd iteration, abort |

## Self-Refine Variant

When no external evaluator exists (creative writing, style improvement): the LLM critiques its own output against explicit criteria, lists issues with suggestions, then refines. Converges in ~2.3 iterations on average (Madaan et al., NeurIPS 2023). Warning: avoid for reasoning tasks where the same model produced the error.

## Episodic Memory Across Tasks

Store reflections keyed by task type. On future tasks, retrieve the 5 most relevant past lessons and inject them into the actor's prompt before generation. This prevents cross-task repetition of the same class of error.

## Best Practices

- Use separate prompts/models for generation and critique (same model, same biases = poor separation)
- Monitor score trajectory—stop immediately if current score drops more than 0.05 below previous
- For code, tests provide ground truth; for reasoning, use self-consistency voting instead of reflexion
- Calibrate the evaluator on known examples before relying on its scores

## Related Notes

- [[plan-and-execute]] — planning partner; reflexion often improves execution within a plan
- [[tree-of-thoughts]] — alternative multi-path exploration strategy
- [[preflight-validation]] — catches errors before they need reflection loops
- [[memory-systems-working-memory]] — episodic memory implementation
- [[long-term-memory-retrieval]] — cross-session lesson storage
- [[loop-control]] — iteration budgets and convergence
