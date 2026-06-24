---
type: note
title: Code Generation Agents
status: evergreen
created: 2026-01-05
updated: 2026-06-19
tags: [code-agents, swe-bench, sandboxed-execution, code-test-fix, aider, autonomous-engineering]
aliases: [software engineering agents, code agents]
---

Code generation agents go beyond autocomplete to autonomously write, test, and fix code in iterative loops. The leap from raw LLMs (~3.8% on SWE-Bench) to tool-equipped agents (26%+) comes entirely from tooling and iteration, not model size.

**The Code-Test-Fix loop:** Plan → Code → Test → Fix → repeat until tests pass or budget exhausted. Successful solutions average 3–7 iterations. Tests are the oracle — never trust the LLM's claim of completion.

**Key benchmarks (2025):**
- Claude 3.5 Sonnet + Tools: 49% on SWE-Bench Verified
- SWE-Agent + GPT-4: 26.3% on SWE-Bench Lite
- OpenHands (open-source): 25%
- Aider + GPT-4: 21.4% (diff-based)
- Raw GPT-4 (no tools): 3.8%

**SWE-Agent ACI (Agent-Computer Interface)** replaces raw bash with purpose-built commands (`open`, `edit 15:20 "..."`, `search_dir`) that reduce LLM parsing errors. Structured output over raw shell dramatically cuts mistakes.

**Aider diff format** uses `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` blocks — the same as git diff. Token-efficient, human-readable, achieves 72% on Exercism exercises.

**Multi-file orchestration** topologically sorts edits by dependency (types → impl → tests) and validates incrementally (TypeScript compile after each file) to catch errors early.

**Sandboxed execution** is non-negotiable. Providers: E2B (Firecracker, ~200ms cold start), Modal (gVisor, ~500ms, GPU support), Docker (1–2s, self-hosted), Fly.io (Firecracker, ~300ms). Always destroy sandbox after use.

**Production limits:** `maxSteps: 20`, `maxAttempts: 5`, `maxTokens: 100,000`, `timeout: 5 min`. Without caps, failing tasks burn budget unboundedly. Force context-gathering before editing: search all usages, read related tests, check type definitions. Estimated 55% cost saving vs. all-human workflow at scale.

Avoid for architectural decisions, security-critical code, or untested codebases (no oracle to verify correctness).

Part of [[advanced]].

Related: [[react-pattern]] · [[tool-definition]] · [[tool-validation]] · [[self-improving-agents]] · [[resilience-patterns]] · [[optimization]] · [[loop-control]]
