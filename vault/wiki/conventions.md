---
type: note
title: Vault Conventions
status: evergreen
created: 2026-06-19
updated: 2026-06-19
tags: [meta, conventions, vault]
aliases: [Filing Rules, Vault Standards]
---

Normative conventions for every file in this vault. When in doubt, consult this note first.

---

## Required frontmatter keys

Every file **must** carry these YAML keys in this order:

| Key | Description |
|-----|-------------|
| `type` | One of the allowed types below |
| `title` | Human-readable title (sentence case) |
| `status` | `seedling` / `budding` / `evergreen` for notes; `active` / `waiting` / `done` for tasks; `active` for areas |
| `created` | ISO date of first commit (`YYYY-MM-DD`) |
| `updated` | ISO date of last meaningful edit |
| `tags` | YAML list of lowercase kebab-case tags |
| `aliases` | YAML list of alternative titles (may be empty `[]`) |

---

## Allowed types

| Type | Used for |
|------|----------|
| `index` | The vault root index (`wiki/index.md`) |
| `note` | Atomic knowledge notes in `wiki/notes/` |
| `area` | Area hub files in `wiki/areas/` |
| `task` | Task files in `tasks/active|waiting|done/` |
| `decision` | ADR entries in `wiki/decisions.md` |
| `meeting` | Meeting records |
| `runbook` | Step-by-step operational procedures |
| `skill` | Skill or capability breakdowns |
| `research` | Literature surveys or experiment logs |
| `prediction` | Falsifiable forecasts with resolution date |
| `client` | Client relationship records |
| `project` | Project root notes |
| `person` | Person / contact notes |
| `tool` | Tool or software evaluation notes |

---

## Slugs

- Slugs are the filename without extension, e.g. `hybrid-search-reranking`.
- Slugs must be **globally unique** across the entire vault.
- Use lowercase kebab-case only; no spaces, underscores, or special characters.
- Once a slug is referenced by another note, treat it as stable. Renames require a search-and-replace pass and a `decisions.md` entry.

---

## Wikilinks

- Always link by slug: `[[hybrid-search-reranking]]`
- Use heading anchors for deep links: `[[rag-architectures#Indexing pipeline]]`
- Use aliases for display text: `[[hybrid-search-reranking|Hybrid Search]]`
- Never use bare file paths or markdown `[text](path)` links inside `wiki/`.

---

## One idea per note

Each note in `wiki/notes/` captures exactly one concept. If you find yourself writing "Part 1" or needing a table of contents inside a note, split it. Area hubs (`wiki/areas/`) are the only exception — they are allowed to synthesize across many concepts.

---

## Area hubs

Area files (`wiki/areas/<slug>.md`, type `area`) must contain:

1. An introductory paragraph synthesizing the compiled truth for the area.
2. A `## Timeline` section — append-only log of when notes were added or major revisions made.
3. A `## Notes` section listing every child note as a wikilink.

Area hubs are the **only** place where compiled, cross-note synthesis lives. Individual notes state atomic facts.

---

## Filing rules