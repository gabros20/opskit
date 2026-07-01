# Obsidian Flavored Markdown — the normative compatibility reference

This is the **checkable** definition of what "Obsidian-compatible" means for ops (proposal Part 3.1).
Obsidian is Frontend Zero: it renders, edits, graphs, and mobile-syncs the vault for the cost of a
config pack (`templates/obsidian/`). ops therefore emits a deliberately narrow subset of Obsidian
Flavored Markdown (OFM) and tolerates the rest on read. The rule of thumb: **ops emits the plain,
portable form; Obsidian is free to render richer forms a human types by hand, and ops must not choke
on them or rewrite them.**

Distilled from the OFM feature set (kepano/obsidian-skills, help.obsidian.md, jsoncanvas.org,
Obsidian Bases docs). Where a form is destructive to portability it is listed under "ops avoids".

---

## 1. Wikilinks

| Form | Meaning | ops |
|---|---|---|
| `[[slug]]` | link by note basename | **emits** |
| `[[slug#Heading]]` | link to a heading | tolerates (read) |
| `[[slug#^blockid]]` | link to a block | tolerates (read) |
| `[[slug\|Display text]]` | aliased link | tolerates (read) |
| `[[folder/slug]]` | path-qualified link | tolerates; ops never emits (slugs are globally unique, so the basename form always resolves) |

- ops resolves links by **basename** (`bin/lib/paths.py:link_targets` strips `#heading` and
  `|alias`). Slugs are globally unique across folders (`wiki/conventions.md`), so `[[bare-slug]]`
  is unambiguous — this is why `newLinkFormat: shortest` + `useMarkdownLinks: false` are set in
  `templates/obsidian/app.json`. Obsidian will then also write the shortest form on auto-link.
- **Wikilinks belong in the note body, never in frontmatter.** Obsidian's Properties editor does not
  render `[[…]]` inside YAML; `ops doctor` lints for wikilinks that appear inside a frontmatter block.

## 2. Embeds / transclusion

| Form | Meaning | ops |
|---|---|---|
| `![[slug]]` | embed a whole note | tolerates (read) |
| `![[slug#Heading]]` | embed a section | tolerates (read) |
| `![[image.png]]` | embed an attachment | tolerates (read) |
| `![alt](path)` | standard Markdown image | **emits** (shadow notes for `~/files` assets use this) |

- Binaries never enter `wiki/` (plaintext-only, enforced by `ops doctor`). Images live in `~/files`
  behind a **shadow note** that references them with standard `![alt](path)` so an editor that
  resolves the path previews inline; the terminal renderer shows a `🖼` reference.
- New attachments a human drags into Obsidian are routed to `inbox/attachments/`
  (`attachmentFolderPath` in `app.json`) — **outside `wiki/`** — so the plaintext wall holds.

## 3. Tags

| Form | ops |
|---|---|
| `#tag` inline in body | tolerates (read) |
| `tags:` frontmatter (flow `[a, b]` or block `- a`) | **emits** the flow form; tolerates both on read |

- Tags are **lowercase, hyphenated** (`agentic-engineering`, not `AgenticEngineering` or `agentic_eng`).
  `ops doctor` lints frontmatter tags for this; Obsidian treats `#Tag` and `#tag` as distinct, so
  case drift silently fragments the tag graph.
- ops writes `tags: [meta, index]` (flow). Obsidian's Properties normalizer rewrites this to a block
  list on save. That is a **read-tolerated** change, never fought (see §6).

## 4. Callouts

Obsidian callouts are blockquotes with a `[!type]` marker:

```markdown
> [!note] Optional title
> Body text.
```

- ops **tolerates** callouts on read (they are valid CommonMark blockquotes — a non-Obsidian renderer
  degrades gracefully to a quote). ops verbs do not emit callouts, to keep generated notes portable to
  plain-Markdown tools. Types: `note tip warning danger info success question quote example`.

## 5. Frontmatter / Properties

- Every note opens with a YAML frontmatter block delimited by `---` … `---` on their own lines.
- Canonical keys (`wiki/conventions.md`): `type title status created updated tags aliases`
  (+ per-type extras such as `url`, `source`, `derived_from`, `id`).
- **Property types Obsidian infers:** `tags` and `aliases` → list; `created`/`updated`/`date` → date;
  everything else → text. ops emits ISO dates (`YYYY-MM-DD`) and flow lists, which Obsidian accepts.
- A note's `title` is duplicated as the first `# H1` so the note reads correctly in tools that ignore
  frontmatter; `showInlineTitle` is on so Obsidian doesn't double it visually.

## 6. What Obsidian's Properties normalizer changes — and why ops never fights it

On save/edit Obsidian may, without asking:
- **reorder** frontmatter keys into its own canonical order;
- convert a **flow list** `tags: [a, b]` into a **block list** (`tags:\n  - a\n  - b`);
- normalize quoting and spacing.

The frontmatter reader (`bin/lib/paths.py`: `fm_field`, `fm_list`, `frontmatter`) is **position- and
shape-independent**: it reads a scalar by key regardless of order, and reads a list whether flow or
block. ops therefore **tolerates on read and never rewrites a user's file to undo the normalizer**
(anti-roadmap #12). Re-normalization happens only inside the disposable search index, never on disk.
`ops doctor` *warns* (never fails) on notes whose frontmatter Obsidian would churn, so the human — not
an agent — decides whether to let Obsidian rewrite them.

## 7. Block references

- `^blockid` at the end of a line marks a block; `[[slug#^blockid]]` links to it. ops **tolerates**
  block ids on read and does not strip them, but does not emit them.

## 8. JSON Canvas

- ops emits deterministic `.canvas` files (JSON Canvas 1.0, `jsoncanvas.org`) via `ops wiki canvas`.
  Nodes are `{id, type:"file", file, x, y, width, height}`; edges are `{id, fromNode, toNode}`.
  Layout is a slug-ordered ring/grid so re-runs are **byte-identical** (no server, no Obsidian needed
  to produce them). Obsidian renders them natively; a `.canvas` is plain JSON, so it survives export.

## 9. Bases

- ops ships starter `.base` files (`templates/obsidian/bases/`) — saved queries over the same
  frontmatter fields (`type`, `status`, `updated`, `tags`). A `.base` is YAML with `filters`
  (`and`/`or` of expressions like `type == "project"`, `file.hasTag("x")`) and `views` (table/cards
  with `order`/`sort`). Both `.canvas` and `.base` are open, git-versioned, plaintext view layers ops
  generates and Obsidian renders.

## 10. URIs open, never write

- `ops wiki open <slug> --obsidian` (or `OPS_OPEN=obsidian`) computes
  `obsidian://open?vault=<name>&file=<relpath>` and, on macOS, hands it to `open`. This is **local
  IPC to open a note, not a network call and never a write.** Obsidian's Advanced-URI *write* mode
  bypasses the guardrail and is **forbidden** — all writes go through `ops` verbs (anti-roadmap #12).

---

## Compatibility checklist (what `ops doctor` and tests enforce)

- [ ] frontmatter tags are lowercase-hyphenated
- [ ] no `[[wikilinks]]` inside a frontmatter block (body only)
- [ ] frontmatter round-trips (no shape Obsidian's normalizer would churn) — WARN, never rewritten
- [ ] `wiki/` stays plaintext (`.md`/`.canvas` only); binaries live in `~/files`
- [ ] emitted `.canvas` is valid JSON Canvas 1.0 and byte-deterministic
- [ ] `.obsidian/` is user-owned (never listed in `script/engine.txt`); `workspace*.json`, `cache`,
      `.trash/`, `.smart-env/` are gitignored
