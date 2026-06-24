---
type: note
title: Context Injection
status: evergreen
created: 2026-01-03
updated: 2026-06-19
tags: [dependency-injection, agent-context, testability, multi-tenancy, runtime-context, tool-design]
aliases: [AgentContext, experimental_context]
---

Tools need databases, services, and user context to operate. The naive approach — importing module-level singletons — creates tight coupling, prevents unit testing, and is unsafe in multi-tenant environments where User A could leak data to User B. Context injection solves this by passing all dependencies through an explicit, typed object at runtime via the AI SDK v6 `experimental_context` parameter.

**Core pattern:** Define an `AgentContext` interface listing every available service (`db`, `services`, `user`, `logger`, `session`). Build a `createAgentContext()` factory per request. Pass it to the agent via `experimental_context`. Inside tool `execute()` functions, cast: `const ctx = experimental_context as AgentContext`.

**Key benefits:** Testability (inject mock context in unit tests — `{ db: mockDb, user: { id: "test-user" } }`), multi-tenancy (per-request scoping prevents shared state), and environment flexibility (swap real vs mock implementations without changing tool code).

**ServiceContainer pattern:** Lazy-load services inside a container class (`getPageService()`, `getImageService()`) so only needed services are instantiated per request. This avoids overhead when a request only uses a subset of tools.

**Failure modes to avoid:** (1) Module-level service instantiation — tool captures stale state at load time; (2) Closures over request data — userId captured at tool creation rather than execution time; (3) Tests without context — `experimental_context` is `undefined` causing silent failures.

**Decision rule:** Single-user single-environment scripts may use global imports. Any multi-tenant or production deployment requires context injection — it is non-negotiable for isolation and testability.

Part of [[tools]].

Related: [[tool-definition]] · [[tool-registry]] · [[tool-security]] · [[injection-strategies]] · [[context-management]] · [[agent-fundamentals]]
