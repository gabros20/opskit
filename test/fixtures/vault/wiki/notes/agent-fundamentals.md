---
type: note
title: Agent Fundamentals
status: evergreen
created: 2026-01-27
updated: 2026-06-19
tags: [agents, autonomous-systems, coala, cognitive-architecture, perception-action-loop, multi-agent]
aliases: [AI agents, agent architecture]
---

An AI agent is a software system that combines LLM reasoning with tool execution in a **Perception → Reasoning → Acting → Memory** loop, solving multi-step tasks dynamically without explicit workflow programming.

## Why Single LLM Calls Fall Short

Static LLM calls cannot access external systems, manage intermediate state, or adapt to feedback. Tasks like "create a page, look up its ID, then add a section" require sequential tool calls where each step depends on prior results.

## Core Architecture

An agent has three subsystems: **Brain** (LLM for reasoning/planning/deciding), **Tools** (search, DB, APIs, CMS), and **Memory** (working, episodic, long-term via vector DB). The execution cycle: observe context → reason about next action → act via tool → observe result → repeat.

## CoALA Framework

The Cognitive Architectures for Language Agents (CoALA, Sumers et al. 2024) organises agents along three dimensions:

- **Memory**: Working (scratchpad), Episodic (RAG/logs), Semantic (knowledge bases/vectors), Procedural (weights/prompts)
- **Action space**: External (environments, APIs) + Internal (retrieval, reasoning, learning)
- **Decision cycle**: retrieve → plan → execute → observe

GPT-3.5 improved from 48% to 95% on coding benchmarks when enhanced with CoALA-style tools and reflection.

## When to Use Agents

Anthropic's complexity spectrum: single LLM call → augmented LLM → workflow → agent. Use agents only when tasks are open-ended, step count is unpredictable, or environmental feedback is required. Agents cost ~12× more per task than single calls (ReAct agent: ~$0.12 vs $0.01).

## Key Patterns

- **ReAct**: Thought → Action → Observation (most common, 92% success)
- **Plan-and-Execute**: Upfront planning then execution; 40% fewer dead-end failures
- **CodeAct** (Wang et al. 2024): Python code instead of JSON tool calls; +20% success, −31% interactions (M3ToolEval)
- **12 Factor Agents**: "Agent = Prompt + Switch + Context + Loop"; small focused agents (<100 tools, <20 steps) outperform monolithic ones

## Anti-Patterns

Environment garbage (stale files/processes) causes non-deterministic failures — use fresh ephemeral environments per run. Session coupling kills autonomous agents; run them remotely. Over-specification degrades performance: define *what*, not *how*.

Part of [[agents]].

## Related

- [[react-pattern]] — Core execution loop implementation
- [[tool-calling]] — Tool design and schema best practices
- [[loop-control]] — Preventing runaway execution
- [[plan-and-execute]] — Planning-first agent architecture
- [[memory-systems-working-memory]] — Memory subsystem detail
- [[prompting-techniques]] — System prompt design for agents
- [[orchestration-patterns]] — Multi-agent coordination
