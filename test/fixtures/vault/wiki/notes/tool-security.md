---
type: note
title: Tool Security & Safety
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [tool-security, risk-classification, prompt-injection, rbac, audit-logging, egress-control]
aliases: [tool safety, agentic security]
---

Tools give agents real-world power — and that power is the primary attack surface. OWASP Agentic AI Top 10 (2025) ranks tool misuse as a top-3 risk. Key threats: prompt injection via tool outputs hijacking agent behavior, privilege escalation by chaining low-risk tools to achieve high-risk outcomes, and data exfiltration through write tools.

**Defense-in-depth model (4 layers):**

1. **Risk classification** — every tool tagged `low` (read-only), `medium` (create/update with validation), `high` (delete, sensitive modifications), `critical` (financial, bulk operations, multi-account). Policies scale accordingly: full audit + dual approval for critical.

2. **Approval gates (HITL)** — AI SDK v6 `needsApproval` callback pauses execution and routes to a human for high/critical operations before proceeding. The approved-by field is stored in the audit entry. Implement fail-closed: default all tools to require approval, then explicitly mark proven-safe tools as auto-approved.

3. **Egress control** — HTTP tools enforce a domain allowlist, block private IP ranges (SSRF protection against `10.x`, `192.168.x`, `172.16.x`, and cloud metadata endpoints like `metadata.google.internal`), apply per-request timeouts (10s default), and rate-limit per tool and per user.

4. **RBAC + Audit logging** — role-to-tool mappings (`viewer` / `editor` / `admin`) gate which tools are even presented to the agent per user. All tool calls log `userId`, `sessionId`, `toolName`, `input`, `output`, `riskLevel`, `approved`, `duration`, and `errorCode`. Sanitize sensitive fields (`password`, `apiKey`, `token`, `ssn`) before storing. Alert on high/critical operations and unusual patterns (search → export → send sequences, cross-boundary reads).

**Key pitfalls:** Trusting tool outputs as safe prompt content (sanitize before re-injecting), overprivileged service accounts (apply least-privilege to the agent's DB credentials), and no rate limiting (agent can exhaust external APIs or incur runaway costs).

Part of [[tools]].

Related: [[tool-definition]] · [[tool-registry]] · [[context-injection]] · [[approval-gates]] · [[error-classification]] · [[resilience-patterns]]
