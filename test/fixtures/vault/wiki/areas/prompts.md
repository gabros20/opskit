---
type: area
title: Prompts
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [prompt-engineering, chain-of-thought, system-prompts, few-shot, template-engines, prompt-management]
---

# Prompts

Prompt engineering is the discipline of shaping LLM inputs to produce reliable, accurate, and cost-efficient outputs. It spans three layers: the techniques used inside individual prompts, the system-level "mission briefing" that defines an agent's identity and guardrails, and the infrastructure needed to manage prompts at scale in production.

The core technique hierarchy runs from basic instruction design (CLEAR framework: Concise, Logical, Explicit, Adaptive, Reflective) through few-shot learning (+20–40% accuracy with 2–10 examples), Chain-of-Thought reasoning (+50–400% on math/logic), and advanced variants — Zero-Shot CoT ("Let's think step by step"), Chain of Draft (80% token reduction), Self-Consistency (majority vote across 5–7 paths), and Graph of Thoughts (+46% on GPQA). As of 2025, frontier reasoning models (o1, o3, Claude 3.7 Sonnet) internalize CoT natively, making explicit prompting for step-by-step reasoning increasingly redundant.

System prompt design operationalizes identity and behavior at the infrastructure level: a six-layer structure covering role, capabilities, limitations, rules (MUST/SHOULD/MUST NOT), output format, and dynamic context. Layered guardrails defend at input (injection detection), output (schema validation, sensitive-data redaction), and runtime (loop detection, error escalation). JSON Schema via Zod + `generateObject()` is the 2025 production standard for structured output, delivering 100% compliance. Modular prompt architectures compose these layers as reusable components across multiple agents.

Prompt management turns one-off templates into maintainable infrastructure: Handlebars or Jinja2 template engines handle dynamic injection and conditional sections; Langfuse or file-based registries provide semantic versioning (MAJOR.MINOR.PATCH) with dev→staging→production label promotion and rollback; Anthropic's native `cache_control` achieves 90% cost reduction and 79% latency reduction on repeated system prompts. DSPy optimizers and LLMLingua-2 compression (3–6x) represent the frontier of automated prompt refinement.

## Timeline

- 2026-06-19 Imported 3 notes from the source KB.

## Notes

- [[prompting-techniques]]
- [[system-prompts]]
- [[prompt-management]]
