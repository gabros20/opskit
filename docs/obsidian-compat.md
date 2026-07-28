# Obsidian Flavored Markdown — the normative compatibility reference

This is the **checkable** definition of what "Obsidian-compatible" means for plainkeep (proposal Part 3.1):
what plainkeep **emits**, and what it merely **tolerates** on read. Read it before changing a verb that
writes notes, or when auditing compatibility.

Obsidian is Frontend Zero. For the cost of a config pack (`templates/obsidian/`) it renders, edits,
graphs, and mobile-syncs the vault. So plainkeep emits a deliberately narrow subset of Obsidian Flavored
Markdown (OFM) and tolerates the rest on read.

**The rule of thumb:**

> plainkeep emits the plain, portable form. Obsidian is free to render richer forms a human types by hand.
> plainkeep must not choke on those forms or rewrite them.

Distilled from the OFM feature set (kepano/obsidian-skills, help.obsidian.md, jsoncanvas.org, Obsidian
Bases docs). Forms that are destructive to portability are listed under "plainkeep avoids".

---

## 1. Wikilinks

| Form | Meaning | plainkeep |
|---|---|---|
| `[[slug]]` | link by note basename | **emits** |
| `[[slug#Heading]]` | link to a heading | tolerates (read) |
| `[[slug#^blockid]]` | link to a block | tolerates (read) |
| `[[slug\|Display text]]` | aliased link | tolerates (read) |
| `[[folder/slug]]` | path-qualified link | tolerates; plainkeep never emits it |

**Resolution.** plainkeep resolves links by **basename**. `bin/lib/paths.py:link_targets` strips `#heading`
and `|alias` first. Slugs are globally unique across folders (`wiki/conventions.md`), so `[[bare-slug]]`
is unambiguous. That is why `templates/obsidian/app.json` sets `newLinkFormat: shortest` and
`useMarkdownLinks: false`. Obsidian then also writes the shortest form on auto-link, and the
path-qualified form is never needed.

**Placement.** Wikilinks belong in the note body, never in frontmatter. Obsidian's Properties editor
does not render `[[…]]` inside YAML. `plainkeep doctor` lints for wikilinks that appear inside a frontmatter
block.

## 2. Embeds / transclusion

| Form | Meaning | plainkeep |
|---|---|---|
| `![[slug]]` | embed a whole note | tolerates (read) |
| `![[slug#Heading]]` | embed a section | tolerates (read) |
| `![[image.png]]` | embed an attachment | tolerates (read) |
| `![alt](path)` | standard Markdown image | **emits** (used by shadow notes for `~/files` assets) |

**No binaries in `wiki/`.** `wiki/` is plaintext-only, enforced by `plainkeep doctor`. Images live in
`~/files` behind a **shadow note** that references them with standard `![alt](path)`. An editor that
resolves the path previews inline; the terminal renderer shows a `🖼` reference.

**Dragged-in attachments.** New attachments a human drags into Obsidian are routed to
`inbox/attachments/` (`attachmentFolderPath` in `app.json`), which is **outside `wiki/`**, so the
plaintext wall holds.

## 3. Tags

| Form | plainkeep |
|---|---|
| `#tag` inline in body | tolerates (read) |
| `tags:` frontmatter (flow `[a, b]` or block `- a`) | **emits** the flow form; tolerates both on read |

**Case.** Tags are **lowercase, hyphenated** (`agentic-engineering`, not `AgenticEngineering` or
`agentic_eng`). `plainkeep doctor` lints frontmatter tags for this. Obsidian treats `#Tag` and `#tag` as
distinct, so case drift silently fragments the tag graph.

**Flow vs block.** plainkeep writes `tags: [meta, index]` (flow). Obsidian's Properties normalizer rewrites
this to a block list on save. That is a **read-tolerated** change, never fought (see §6).

## 4. Callouts

Obsidian callouts are blockquotes with a `[!type]` marker:

```markdown
> [!note] Optional title
> Body text.
```

- plainkeep **tolerates** callouts on read. They are valid CommonMark blockquotes, so a non-Obsidian
  renderer degrades gracefully to a quote.
- plainkeep verbs **do not emit** callouts, keeping generated notes portable to plain-Markdown tools.
- Types: `note tip warning danger info success question quote example`.

## 5. Frontmatter / Properties

- Every note opens with a YAML frontmatter block delimited by `---` … `---`, each on its own line.
- Canonical keys (`wiki/conventions.md`): `type title status created updated tags aliases`, plus
  per-type extras such as `url`, `source`, `derived_from`, `id`.
- A note's `title` is duplicated as the first `# H1`, so the note reads correctly in tools that ignore
  frontmatter. `showInlineTitle` is on so Obsidian doesn't double it visually.

**Property types Obsidian infers:**

| Key | Inferred type | What plainkeep emits |
|---|---|---|
| `tags`, `aliases` | list | flow lists (Obsidian accepts) |
| `created`, `updated`, `date` | date | ISO dates `YYYY-MM-DD` (Obsidian accepts) |
| everything else | text | text |

## 6. What Obsidian's Properties normalizer changes — and why plainkeep never fights it

On save or edit, Obsidian may, without asking:

- **reorder** frontmatter keys into its own canonical order;
- convert a **flow list** `tags: [a, b]` into a **block list** (`tags:\n  - a\n  - b`);
- normalize quoting and spacing.

plainkeep absorbs all of this. The frontmatter reader (`bin/lib/paths.py`: `fm_field`, `fm_list`,
`frontmatter`) is **position- and shape-independent**: it reads a scalar by key regardless of order,
and reads a list whether flow or block.

So plainkeep **tolerates on read and never rewrites a user's file to undo the normalizer** (anti-roadmap
#12). Re-normalization happens only inside the disposable search index, never on disk. `plainkeep doctor`
**warns** (never fails) on notes whose frontmatter Obsidian would churn, so the human — not an agent —
decides whether to let Obsidian rewrite them.

## 7. Block references

- `^blockid` at the end of a line marks a block; `[[slug#^blockid]]` links to it.
- plainkeep **tolerates** block ids on read and does not strip them. plainkeep does not emit them.

## 8. JSON Canvas

- plainkeep emits deterministic `.canvas` files (JSON Canvas 1.0, `jsoncanvas.org`) via `plainkeep wiki canvas`.
- Nodes are `{id, type:"file", file, x, y, width, height}`; edges are `{id, fromNode, toNode}`.
- Layout is a slug-ordered ring/grid, so re-runs are **byte-identical** (no server, no Obsidian needed
  to produce them).
- Obsidian renders them natively. A `.canvas` is plain JSON, so it survives export.

## 9. Bases

- plainkeep ships starter `.base` files (`templates/obsidian/bases/`): saved queries over the same
  frontmatter fields (`type`, `status`, `updated`, `tags`).
- A `.base` is YAML with `filters` (`and`/`or` of expressions like `type == "project"`,
  `file.hasTag("x")`) and `views` (table/cards with `order`/`sort`).
- Both `.canvas` and `.base` are open, git-versioned, plaintext view layers plainkeep generates and Obsidian
  renders.

## 10. URIs open, never write

- `plainkeep wiki open <slug> --obsidian` (or `PLAINKEEP_OPEN=obsidian`) computes
  `obsidian://open?vault=<name>&file=<relpath>` and, on macOS, hands it to `open`.
- This is **local IPC to open a note. It is not a network call and never a write.**
- Obsidian's Advanced-URI *write* mode bypasses the guardrail and is **forbidden**. All writes go
  through `plainkeep` verbs (anti-roadmap #12).

---

## Compatibility checklist (what `plainkeep doctor` and tests enforce)

- [ ] frontmatter tags are lowercase-hyphenated
- [ ] no `[[wikilinks]]` inside a frontmatter block (body only)
- [ ] frontmatter round-trips (no shape Obsidian's normalizer would churn) — WARN, never rewritten
- [ ] `wiki/` stays plaintext (`.md`/`.canvas` only); binaries live in `~/files`
- [ ] emitted `.canvas` is valid JSON Canvas 1.0 and byte-deterministic
- [ ] `.obsidian/` is user-owned (never listed in `script/engine.txt`); `workspace*.json`, `cache`,
      `.trash/`, `.smart-env/` are gitignored
