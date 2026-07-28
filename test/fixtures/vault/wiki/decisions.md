---
type: decision
title: Decision Log
status: evergreen
created: 2026-06-19
updated: 2026-06-19
tags: [meta, decisions, adr]
aliases: [ADR Log, Architecture Decisions]
---

Append-only log of significant decisions about the vault, its structure, tooling, and methodology. Each entry is an Architectural Decision Record (ADR). Never edit past entries — only append.

Format per entry:

```
## ADR-NNN — Title
- **Date:** YYYY-MM-DD
- **Status:** proposed | accepted | superseded
- **Context:** Why this decision was needed.
- **Decision:** What was decided.
- **Consequences:** What changes as a result.
```

---

## ADR-001 — Adopt this knowledge base as the vault seed

- **Date:** 2026-06-19
- **Status:** accepted
- **Context:** The personal-operating-system project needed a structured, queryable knowledge base covering LLM and agent engineering concepts. A hand-curated KB of 58 notes across 13 areas had been authored as part of the plainkeep-search spike (see commits `a8ea421`, `c034ec6`). Rather than starting from scratch inside Obsidian, we elected to import this KB directly as the vault's `wiki/` layer.
- **Decision:** Import all 58 notes into `vault/wiki/notes/` and all 13 area hubs into `vault/wiki/areas/`, using the existing slugs as filenames. Add `wiki/index.md`, `wiki/conventions.md`, and `wiki/decisions.md` as meta-layer files. Establish `tasks/` and `journal/` directories alongside `wiki/` to complete the plainkeep-shaped vault.
- **Consequences:** Slug namespace is now seeded with 58 globally unique identifiers. All future notes must check for slug collisions before filing. The conventions established in `wiki/conventions.md` apply retroactively to all imported notes (they already conform). The KB becomes the single source of truth for LLM/agent engineering in this vault; duplicate notes in other systems should be deprecated in favour of links here.
