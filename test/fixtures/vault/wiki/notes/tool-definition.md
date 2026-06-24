---
type: note
title: Tool Definition & Schema
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [tool-design, zod-schema, type-safety, agent-tools, naming-conventions, tool-selection]
aliases: [tool schema, function calling]
---

Tools extend LLM capabilities beyond text generation—they enable agents to fetch data, modify state, and interact with external systems. Tool quality directly determines agent reliability: vague descriptions cause wrong selection, missing validation causes schema mismatches, and inconsistent naming creates ambiguity.

Per Anthropic (2024): "Invest just as much effort in creating good agent-computer interfaces as you would for human-computer interfaces." Key benchmarks: **90%+ tool selection accuracy** achievable with clear descriptions, **<0.5% invalid tool calls** with strict schema validation, **70% latency reduction** with proper I/O classification enabling parallel execution.

**The four properties of a well-designed tool:** (1) Description — when to use and explicitly when NOT to use; (2) Input schema — typed and constrained with Zod; (3) Output format — consistent `{ success, data/error }` shape; (4) Execute — clearly idempotent or side-effectful.

**Naming convention:** `service_resource_action` (e.g. `cms_pages_update`, `storage_images_upload`). Action verbs: `get`, `list`, `search`, `create`, `update`, `delete`, `upload`. Enforcing this pattern across 5+ tools prevents the "getPage vs fetch_user vs searchContent" confusion common in ad-hoc codebases.

**Zod schema patterns:** `.uuid()` for IDs, `.regex()` for slugs, `.coerce.date()` for ISO date inputs, `.describe()` on every parameter with actionable guidance (e.g. "UUID of the page to update. Get from cms_pages_search or cms_pages_list"). Vague parameter descriptions increase argument errors by 60%+.

**Standardized error codes** enable LLM recovery: `NOT_FOUND`, `VALIDATION_ERROR`, `PERMISSION_DENIED`, `CONFLICT`, `RATE_LIMITED`. Beyond ~10 tools, add semantic discovery (see [[tool-registry]]).

Part of [[tools]].

Related: [[tool-registry]] · [[tool-security]] · [[context-injection]] · [[tool-calling]] · [[tool-validation]] · [[react-pattern]]
