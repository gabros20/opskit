---
type: note
title: Approval Gates & Confirmation
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [human-in-the-loop, agent-safety, tool-calling, risk-management, compliance, workflow]
aliases: [hitl-gates, confirmation-checkpoints]
---

Approval gates intentionally pause autonomous agent execution at critical decision points, requiring explicit human confirmation before destructive, expensive, or sensitive actions proceed. This is a long-term architectural pattern for building trustworthy agents, not a temporary workaround.

**Why it matters.** 69% of enterprises deploy AI agents but only 21% have adequate security visibility (Obsidian Security, 2025). EU AI Act Article 14 mandates human intervention and override capability for high-risk systems. Regulations GDPR, HIPAA, and PCI-DSS all require human oversight gates.

**Risk-tiering framework.** Not every action needs approval. Three tiers: (1) Autonomous — read-only operations, queries, `ls`; (2) Approval Required — data writes, external API calls, uploads; (3) Prohibited/multi-approval — production deletions, payment processing. The tiering reduces approval fatigue while keeping safety for critical ops.

**Implementation patterns.**
- *Static approval* (`needsApproval: true` in AI SDK v6): always gates the tool, simple and explicit.
- *Dynamic approval* (`needsApproval: async (ctx, params) => bool`): conditionally gates based on parameters — e.g., external domain emails or salary-related subjects.
- *Approval queue* (enterprise): routes by priority, SLA, and reviewer role.
- *Two-phase commit*: stage reversible changes, validate invariants, pause for approval, then commit or rollback.

**Framework support.** AI SDK v6 provides native `needsApproval` on tool definitions with React frontend via `addToolOutput`. LangGraph uses `interrupt()` with PostgresSaver — state persists indefinitely across servers and can resume days later. Amazon Bedrock offers User Confirmation (boolean) and Return of Control (full parameter modification).

**Production rules.** Present human-readable context, not raw parameters. Set timeouts (e.g., 15 min) with escalation paths and a fallback default of reject. Log every approval decision with timestamp, user identity, action details, and reasoning. Centralize approval logic in a policy engine (OPA, Permit.io) rather than scattering it across tools. Start with the principle of least privilege; expand per-approval.

Part of [[hitl]].

Related: [[tool-security]] · [[tool-calling]] · [[tool-definition]] · [[react-pattern]] · [[loop-control]] · [[resilience-patterns]] · [[adaptive-autonomy]]
