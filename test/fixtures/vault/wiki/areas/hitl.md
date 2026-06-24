---
type: area
title: Hitl
status: active
created: 2026-06-19
updated: 2026-06-19
tags: [human-in-the-loop, agent-safety, alignment, autonomy, oversight, feedback]
---

Human-in-the-loop (HITL) patterns keep humans meaningfully in control of autonomous agents. The three core concerns are: where to pause and require confirmation (approval gates), how to capture and use human feedback to improve agent behavior over time (feedback integration), and how to calibrate the degree of agent independence to context and user trust (adaptive autonomy). Together they form the operational layer that makes production AI agents both safe and continually improving.

Approval gates are not a temporary workaround — they are a long-term trust infrastructure. Risk-tiering (autonomous → approval-required → prohibited) reduces reviewer fatigue while enforcing hard stops on destructive, irreversible, or compliance-governed actions. Native framework support via AI SDK v6 `needsApproval` and LangGraph `interrupt()` makes reliable checkpointing straightforward; the harder problem is writing approval UIs that show human-readable context, not raw JSON parameters.

Feedback integration closes the loop between deployment and improvement. Explicit feedback (thumbs, ratings, corrections) arrives at only 3–4% of interactions; passive behavioral signals (regenerations, abandonment, dwell time, return rate) cover 100% of interactions. The right training choice depends on resources: DPO for speed and cost, full RLHF for nuanced multi-objective alignment, RLTHF when human annotation budget is constrained (6–7% targeted effort achieves full quality). The cardinal rule is never auto-train on raw feedback — always validate and curate before it enters training data.

Adaptive autonomy recognizes that the right level of agent independence varies by user, task risk, and demonstrated track record. The Five Levels of Autonomy framework (0–5) and the Trust Gradient pattern (start at 100% HITL, reduce oversight as quantitative thresholds are met) are the dominant 2025 approaches. Proactivity yields real productivity gains but has a sharp annoyance cliff — small increases in suggestion frequency can halve user preference — so frequency limits, cooldowns, and opt-in controls are essential.

## Timeline

- 2026-06-19 Imported 3 notes from the source KB.

## Notes

- [[approval-gates]]
- [[feedback-integration]]
- [[adaptive-autonomy]]
