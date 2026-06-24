---
type: area
title: Planning
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [planning, agent-architecture, multi-step, reasoning, replanning, validation]
---

Planning is the discipline of deciding _what to do_ before doing it. In LLM-agent systems this means generating explicit, inspectable plans, validating them before committing resources, and adapting when execution diverges from expectations. The area covers four interlocking patterns: structured plan-and-execute architectures, multi-path tree search, verbal self-improvement loops, and pre-execution safety checks.

The current best understanding is that **planning and execution should be decoupled**. Using a powerful model to plan and a cheaper model to execute cuts costs by 70% with minimal accuracy loss. Plans are first-class artifacts—auditable, cacheable, and replaceable—unlike the interleaved thought/action traces of reactive agents. Generating 3–5 alternative plans before starting execution reduces dead-end failures by 40% at only 2.1× the planning cost, and pre-computing fallback plans enables recovery that is 80% faster than replanning from scratch.

**Iterative self-critique** (Reflexion) adds a second layer of improvement: after execution, verbal reflections stored in episodic memory prevent the agent from repeating the same class of mistake. Two to three iterations capture ~90% of available improvement; beyond that, scores plateau or regress. External feedback—test execution, validators, environment signals—is essential; pure self-correction without verification degrades reasoning.

**Tree search** (Tree of Thoughts, LATS, rStar) enables exploring multiple reasoning paths simultaneously and backtracking from dead ends. Results are dramatic on hard problems (4% → 74% on Game of 24) but carry 10–50× computational overhead. A cascade architecture—CoT first, then CoT-SC, then full ToT only for the hardest 10% of problems—brings average cost down to ~7× while preserving accuracy gains where they matter most. Test-time compute scaling (o1/o3, rStar2-Agent) is emerging as an alternative to larger models: a 14B model with RL-guided search can match a 671B model on math benchmarks.

**Preflight validation** applies "fail fast" at the action level: check tool availability, schema validity, resource existence, permissions, and constraint satisfaction before any mutation. This catches 70–80% of doomed actions cheaply (50–200 ms total overhead) and—critically—generates actionable suggestions that raise agent auto-recovery rates from 15% to 72%.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[plan-and-execute]]
- [[reflexion-self-critique]]
- [[tree-of-thoughts]]
- [[preflight-validation]]
