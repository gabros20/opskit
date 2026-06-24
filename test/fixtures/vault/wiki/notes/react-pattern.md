---
type: note
title: ReAct Pattern
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [react, reasoning-acting, agent-loop, transparency, self-correction, chain-of-thought]
aliases: [ReAct loop, Reasoning and Acting]
---

ReAct (Yao et al. 2022, ICLR 2023) interleaves explicit reasoning traces with tool execution in a **Think → Act → Observe** cycle. Unlike pure chain-of-thought (reasoning only) or pure tool-calling (acting only), ReAct makes agent decisions transparent and self-correctable.

## The Three Phases

**THINK**: LLM analyzes current context, identifies gaps, selects the next tool and why. Prompting methods combining ReAct with CoT and Self-Consistency outperform pure methods.

**ACT**: Execute exactly one tool per step with validated parameters. Parallel execution (LLMCompiler) offers 3.6× speedup at the cost of dependency management. High-risk actions may require HITL approval.

**OBSERVE**: Parse the tool result, update working memory, decide whether to continue or terminate. Agents that fail to integrate observations repeat actions in loops.

## Key Results

- ReAct hallucinates 6% vs 14% for CoT alone (HotpotQA)
- Simple/complex task latency: 3–8 s vs 15–45 s; cost $0.01–0.03 vs $0.05–0.20

## Advanced Variants

| Variant | Key Innovation | Result |
|---------|---------------|--------|
| **Reflexion** (Shinn 2023) | Long-term memory of failed trajectories for verbal self-reflection | 97% AlfWorld vs 75% baseline |
| **LATS** (ICML 2024) | Monte Carlo Tree Search for backtracking + LM value functions | 94.4% HumanEval pass@1 |
| **ReWOO** | Full tool-call chain generated upfront (single planning LLM call) | 2–3× latency reduction; less adaptive |
| **A³T** (2024) | ActRe explains actions → autonomous trajectory synthesis | 100% AlfWorld after 4 self-training rounds |

## Implementation (AI SDK v6)

Use `generateText` with a system prompt enforcing THINK/ACT/OBSERVE structure, `stopWhen: stepCountIs(10)`, and `onStepFinish` for logging. Multiple stop conditions can be composed: `[stepCountIs(20), hasToolCall('complete'), hasToolCall('needsHuman')]`.

## Debugging Checklist

Log thought, action, and observation at every step. Symptoms and fixes: agent loops forever → missing termination prompt; wrong tool → poor description; same action repeated → observation not integrated into memory; random exploration → unclear goal in system prompt.

Part of [[agents]].

## Related

- [[agent-fundamentals]] — Agent types and when to use agents
- [[tool-calling]] — Tool schema design
- [[loop-control]] — Step limits and convergence detection
- [[reflexion-self-critique]] — Reflexion self-reflection pattern in depth
- [[memory-systems-working-memory]] — Working memory updates in ReAct
- [[plan-and-execute]] — Planning-first alternative to ReAct
- [[system-prompts]] — Structuring THINK/ACT/OBSERVE instructions
