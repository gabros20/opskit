---
type: note
title: Adaptive Autonomy & Proactivity
status: evergreen
created: 2026-01-04
updated: 2026-06-19
tags: [autonomy-levels, proactivity, trust-building, agent-design, human-oversight, ux]
aliases: [autonomy-framework, proactive-agents]
---

Adaptive autonomy allows agents to operate at different independence levels based on context, user preferences, and task risk. The central tension: proactive agents yield 12–18% productivity gains but small increases in suggestion frequency can reduce user preference by 50% (Microsoft Research, 2024). Trust in fully autonomous agents declined from 43% to 27% YoY as organizations gained real-world experience (2025).

**Five Levels of Autonomy Framework (2025).**
- Level 0: No automation — human does everything.
- Level 1: Basic automation — human as Operator, every action pre-approved.
- Level 2: Workflow automation — human as Collaborator, checkpoints at decision points.
- Level 3: Partial autonomy — human as Consultant, consulted only for complex cases.
- Level 4: High autonomy — human as Approver, validates only critical decisions.
- Level 5: Full autonomy — human as Observer, intervenes only in emergencies.

**HITL vs HOTL.** Human-in-the-Loop (HITL): agent cannot proceed without human input at each checkpoint — use for high-risk actions and trust-building. Human-on-the-Loop (HOTL): agent proceeds autonomously while humans observe and intervene only when needed — use for mature, proven, lower-risk agents.

**Implementation patterns.**
- *User-configurable autonomy*: expose `supervised | collaborative | autonomous` settings plus per-action-type confirmation lists and auto-approve patterns.
- *Context-aware autonomy*: decision engine weighing risk level, user state (focused/idle), model confidence, and reversibility. High risk or confidence < 0.6 → ask. User focused and non-urgent → wait.
- *Progressive trust model (Trust Gradient)*: ship at 100% HITL, reduce oversight only as quantitative thresholds are met (approval rate > 90%, correction rate < 5%, safety incidents = 0). Timeline: weeks, not months. Case study: HR agent "Andy" reached 50%+ autonomous in weeks after 3,000+ reviewed tickets.
- *Proactivity tuning*: suggest immediately only when high urgency + high confidence + user idle. Max 1 proactive suggestion per 5 minutes; cooldown after rejection; suppress when confidence < 60% or recently rejected similar suggestion.

**Anti-pattern.** Starting permissive and tightening after incidents destroys trust permanently. Start conservative, earn the right to autonomy through consistent auditable performance.

**Metrics to track.** Approval rate (target > 85%), override rate (target < 10%), proactive acceptance (target > 60%), escalation rate (decreasing trend), user satisfaction (stable or improving).

Part of [[hitl]].

Related: [[approval-gates]] · [[feedback-integration]] · [[tool-security]] · [[loop-control]] · [[plan-and-execute]] · [[observability]] · [[agent-fundamentals]]
