---
type: area
title: Tools
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [tool-design, agent-tools, function-calling, tool-security, dynamic-selection]
---

The Tools area covers everything required to design, deploy, and operate tools that agents call at runtime. Tools are the boundary between LLM reasoning and real-world execution — they read databases, call APIs, modify files, and trigger side effects. Getting this boundary right is as important as prompt engineering itself: Anthropic's guidance explicitly states that agent-computer interfaces deserve the same investment as human-computer interfaces.

Tool design begins with schema quality. A tool's description governs when an LLM selects it; its Zod schema is a contract that prevents malformed inputs from reaching execution. The `service_resource_action` naming convention, combined with explicit "USE WHEN / DO NOT USE WHEN" description patterns, raises selection accuracy above 90%. Dependencies should never be module-level singletons — they must flow through a per-request `AgentContext` object injected at runtime, enabling testability, multi-tenancy, and environment flexibility.

At scale, static tool lists become a liability. Beyond ~20 tools, selection accuracy degrades and context costs balloon. The registry pattern — a central metadata-enriched catalog with `riskLevel`, `ioType`, and category tags — enables dynamic selection. Embedding tool descriptions with a model like `text-embedding-3-small` and ranking by cosine similarity at query time yields a 56% Recall@5 improvement (LangGraph, 2024). For 50+ tools, a two-stage hierarchical approach (domain selection then tool selection) is preferred.

Security is non-negotiable in production. The OWASP Agentic AI Top 10 (2025) ranks tool misuse as a top-3 risk. Best practice is defense-in-depth: classify every tool by risk level (low / medium / high / critical), gate high-risk operations with human approval (`needsApproval`), restrict egress to allowlisted domains with SSRF protection, enforce RBAC so users only access tools their role permits, and log every tool call with full audit fields. Default deny; explicitly promote proven-safe tools to auto-approve.

## Timeline

- 2026-06-19 Imported 4 notes from the source KB.

## Notes

- [[tool-definition]]
- [[context-injection]]
- [[tool-registry]]
- [[tool-security]]
