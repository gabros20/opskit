---
type: note
title: System Prompt Design
status: evergreen
created: 2026-01-10
updated: 2026-06-19
tags: [system-prompts, guardrails, prompt-architecture, structured-output, role-definition, hallucination-reduction]
aliases: [mission briefing, system message design]
---

# System Prompt Design

Part of [[prompts]].

System prompts are the AI's "mission briefing" — established before any user interaction, they define WHO it is (role), WHAT it can do (capabilities), HOW it must behave (rules), and WHAT format to produce (output). Role clarity improves domain accuracy by 20–40%; explicit capability boundaries reduce hallucination by 15–30%; clear tool inventories improve tool selection accuracy by 25–40%.

**Six-layer structure**: (1) Role & Identity, (2) Capabilities, (3) Rules & Constraints, (4) Output Format, (5) Dynamic Context, (6) Few-shot Examples. Message priority: System > User > Assistant.

**Capabilities declaration** is critical for preventing hallucination. Explicitly list available tools (e.g., `cms_getPage`, `cms_createPage`) and — equally important — what the AI CANNOT do (send emails, access external APIs, read file system). Graceful degradation: acknowledge → explain why → offer alternatives → stay helpful.

**Rules** follow a MUST / SHOULD / MUST NOT / PREFER hierarchy with safety as the highest priority. The optimal count is 5–10 core rules; more than 20 creates conflicts. **Layered guardrails** defend at three stages: input (prompt injection detection, malicious pattern checks), output (sensitive data redaction, hallucination checks, format validation), and runtime (loop detection after 5 identical calls, error escalation after 3 consecutive failures, token budget warnings).

**Output format** evolved from free-text to JSON Mode (2024) to JSON Schema with Zod + `generateObject()` (2025) — the latter guarantees 100% schema compliance. ReAct-style Thought/Action/Observation prefix markers are standard for agentic loops.

**Modular prompt architecture** composes prompts from reusable function-based or tag-based modules (role, capabilities, rules, format, context, examples), enabling multi-agent reuse via a `PromptModuleRegistry`. Store modules in a `prompts/modules/` directory and assemble per-agent in `prompts/agents/`.

Context engineering (Anthropic 2025) matters most above 30,000 tokens or 10+ tool calls: stabilize cacheable prefixes, preserve failed actions in context, and re-inject task objectives in long conversations.

## Related Notes

- [[prompting-techniques]]
- [[prompt-management]]
- [[tool-calling]]
- [[tool-definition]]
- [[react-pattern]]
- [[context-management]]
- [[tool-security]]
