---
type: note
title: Prompt Management
status: evergreen
created: 2026-06-19
updated: 2026-06-19
tags: [prompt-versioning, template-engines, prompt-caching, langfuse, handlebars, jinja2]
aliases: [prompt infrastructure, prompt ops]
---

# Prompt Management

Part of [[prompts]].

Production prompt management replaces fragile string concatenation with three capabilities: **template engines**, **versioning**, and **caching**. Together they make prompts maintainable, auditable, and cost-efficient.

**Template engines** inject dynamic runtime data into prompt skeletons. Handlebars (TypeScript) uses `{{#if}}/{{#each}}` syntax; Jinja2 (Python) uses `{% if %}/{% for %}`. Both support conditional sections — environment (dev/staging/prod), user permission tier (admin/write/read-only), model family (o1 vs standard), and task complexity — eliminating the need for multiple prompt variants. Use raw triple-brace `{{{working_memory}}}` in Handlebars to preserve formatting for injected context blocks. A `PromptTemplateEngine` class caches compiled templates in-memory.

**Versioning** uses semantic versioning (MAJOR.MINOR.PATCH): MAJOR for breaking pattern changes (e.g., switching to ReAct), MINOR for new sections, PATCH for typo fixes. Two patterns: (1) **Langfuse** (open source) — git-style label promotion (dev → staging → production) with `getPrompt()` + `compile()` + rollback by version number; (2) **File-based with a `registry.json`** — version files stored as `prompts/react-agent/v2.1.0.hbs` with a JSON registry mapping labels to versions. A `PromptRegistry` class handles resolution and rollback.

**Caching** operates at two levels. Anthropic's native `cache_control: { type: "ephemeral" }` marker on the system message delivers 79% latency reduction and 90% cost reduction on subsequent requests (cache hit reads at ~10% of creation cost). For response caching across instances, Redis with SHA-256 prompt hashing and TTL-based expiry provides distributed deduplication. Combined versioned+cached engines must invalidate the cache on every version deploy.

**2024–2025 additions**: DSPy optimizers automate prompt refinement via gradient-like feedback loops, replacing manual template iteration. LLMLingua-2 compresses prompts 3–6x without quality loss. Target cache hit rate >50% in production.

## Related Notes

- [[prompting-techniques]]
- [[system-prompts]]
- [[context-management]]
- [[token-optimization]]
- [[injection-strategies]]
- [[observability]]
- [[optimization]]
