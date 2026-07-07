# Search enrichment — generated meta (description + keywords) for every source

**Status: PROPOSED (2026-07-07, revised after an Opus QA pass).** Design, not yet accepted. Companion
to the [image-reading proposal](2026-07-06-image-reading.md) (implemented) and the search/index ADRs
(ADR-005 embedder, ADR-006 vectors). Closes the *findability* half of the ingestion story that
[issue #1](https://github.com/gabros20/personal-operating-system/issues/1) opened.

The bet: **a source is only as findable as the text that describes it — and right now nothing
generates that text.** We add ONE modality-agnostic stage that turns any extracted content into a
short `description` + `keywords`, written to frontmatter, feeding both keyword and semantic search.

---

## 0. The problem — searchability today is accidental

Traced through `bin/lib/indexlib.py`: keyword FTS indexes each note's `heading + body`; the vector
embed is `title + frontmatter + body` capped at **2000 chars** (`_embed_text`, `:151`). The note
schema (`wiki/conventions.md`) has **no `description`, and `tags` ships empty.** So a source is
findable only to the extent raw text lands in its note body — an image shadow note (`title` +
`![](path)`) is ~invisible; a voice memo / video / PDF is findable only via its raw transcript dump.
**There is no meta-generation stage.** That is the gap.

## 1. The enrich stage — one stage, every modality

```
                          ┌──────────────── the ONE new stage ────────────────┐
 source ─▶ modality extractor ─▶ TEXT (the .extract note) ─▶ summarize+tag LLM ─▶ {description, keywords} ─▶ SHADOW note frontmatter ─▶ index
 image    OCR + VLM caption          = the durable "working memory"                gemma4:e4b (Ollama, urllib + structured format)
 voice    whisper transcript
 video    yt-dlp captions
 pdf      pymupdf4llm markdown
 link     trafilatura article text
```

**The `.extract.md` note is the working-memory buffer; the meta lands on the SHADOW note.** (QA R2/R8:
`_write_extract` rewrites the extract note from a fixed template every run, so `--reextract` would
*clobber* meta written there; and meta on a `type: extract` note is excluded by `search --author
human`. The shadow note `wiki/files/<slug>.md` survives re-extract, is the node `ops files list` and
the graph surface, and is the right home for descriptive meta.) Bookmarks enrich their own note.

## 2. The model layer — swappable, but sequenced to avoid regressing shipped code

Model choice should be **env config, not code**. Today that's half-true (OCR/VLM/embed have env knobs;
the **audio/STT tier hardcodes** `parakeet-tdt-0.6b-v2` at `files/run.py:113` and `WhisperModel("base")`
at `:125`, with no override). We deliver modularity **incrementally and safely** rather than as one
big refactor:

- **The one real gap first — `OPS_STT_MODEL` / `OPS_STT_RUNTIME`** retrofits only `_tier_audio`, so you
  can experiment with another ASR by setting one variable. High value, one function, low risk.
- **New model calls use Ollama over stdlib `urllib`** (like `embed.py:16`), with the `format` JSON-schema
  param — **not `import ollama`**. This is also the fix for a latent bug the QA found: `imagelib`
  probes the ollama *CLI* (`_has_ollama`, `:63`) but its runners `import ollama` (a pip package not in
  `requirements.txt`), so that path can pass its probe then `ImportError`. Route ollama through urllib
  everywhere.
- **Keep the shipped surface as-is.** `OPS_MLX` stays a **single per-host runtime switch** (the accepted
  image design forbade per-stage runtime splits for memory reasons); do **not** add per-stage
  `_RUNTIME` to OCR/VLM, and do **not** alias `OPS_OCR` (which names a *backend* like `apple`/`tesseract`,
  not a model) into a `_MODEL` var — that abstraction is leaky (QA §4). A uniform `OPS_<STAGE>_MODEL`
  applies cleanly to the *new/clean* stages (`stt`, `enrich`, `embed`); OCR/VLM/agent keep their
  existing, already-shipped semantics.
- **`bin/lib/models.py` (optional, later):** a thin urllib-Ollama helper the new stages share
  (resolve model from env → `generate(prompt, format=…, keep_alive=…)` → validate → fall back). A full
  retrofit of the shipped OCR/VLM onto it is deferred until there's a second runtime that needs it —
  refactoring `# pragma: no cover` model code right after shipping is the highest-regression move, not
  the lowest (QA §4).

### 2.1 `ops models` — download / offload / on-demand test surface

- `ops models list` — per stage: configured model · runtime · pulled? · resident? *(read)*
- `ops models status` — `ollama ps` *(read)* · `ops models stop [--all]` — `ollama stop` *(safe_write)*
- `ops models pull [--stage <s>|--all] --yes` — `ollama pull` (downloads GB, writes Ollama's store
  outside `~/ops`); **confirm-class** (`--yes`), never silent (QA §4).
- `ops models test <stage> [--model <m>] [--input <file>] --yes` — pull-if-needed (also confirm), run
  the stage on a sample, print output + timing → **A/B a candidate with zero wiring**, then adopt it by
  setting its env var.

**Enrich model — Gemma 4 E4B for EN + Hungarian.** `OPS_ENRICH_MODEL=gemma4:e4b` (~5 GB, 140+ languages
incl. good Hungarian, structured outputs), `OpenEuroLLM-Hungarian` as the HU-max override, `gemma4:e2b`
low-RAM. **Structured output:** attempt with a `format` schema and *validate*; on invalid/absent
support, fall back to the tolerant `_parse_json_array` parser that already exists (`files/run.py:561`) —
don't try to detect support a priori (QA §4).

## 3. Schema + index (smaller than first drafted)

- Add **`description`** (single line — `fm_field`-readable) and **`keywords`** as a **block list** to
  `wiki/conventions.md`. A block list is mandatory: an inline `keywords: [a, b]` is exactly what the
  `ops doctor` churn check flags (`_fm_churn`, `doctor/run.py:73`), so auto-enrich would regress a green
  check on every note (QA R1). Read `keywords` via `_fm_block` (`paths.py:88`), not `fm_field`.
- **No new index code needed.** Frontmatter is already the `(top)` FTS chunk (`_chunks`, `:110`) so
  `description`/`keywords` become keyword-searchable for free, and frontmatter already leads the file so
  it's inside the 2000-char embed window. **No `--reembed` flag:** any frontmatter write changes the
  file hash, so the next `ops index` re-chunks + re-embeds automatically (`:207`). The schema addition
  alone delivers most of the index win (QA §5).

## 4. Determinism, guards, and an honest fallback

- **Determinism (QA R5):** an LLM writing git-tracked frontmatter must not churn. Pin Ollama
  `options:{temperature:0, seed:N}`, and store an **idempotency key** (`enrich_model` + the extract's
  content-hash) in frontmatter so a plain re-run is a true no-op; `--reenrich` forces.
- **Empty-extraction guard (QA R4):** below N chars of real text, or on the `_(no text extracted)_`
  sentinel (`files/run.py:219`), **skip enrich** — never feed empty/garbage to the model (hallucinated
  keywords) or to the extractor (noise). Leave `description` empty.
- **Bounded input (QA R7):** cap the model's input like `distill` does (`body[:8000]`, head + sampled
  headings, `files/run.py:580`); document the head-bias truncation. "Distill 100K tokens to two
  sentences" is neither cheap nor good.
- **Honest deterministic floor (QA R3):** YAKE/RAKE are **pip deps** (RAKE pulls NLTK), and surface-form
  extraction fragments **agglutinative Hungarian** (szerződést/szerződések = distinct terms). So the
  *true* floor is a tiny **stdlib frequency + stopword** extractor (works with no model AND no dep);
  YAKE is an **auto-detected optional upgrade** like every other tier. Don't claim HU quality the floor
  can't deliver.

## 5. The verb and wiring

- **`ops enrich <slug>`** (sibling to `distill`, risk `safe_write`): reads the derived text → generates
  meta → writes it to the **shadow** note's frontmatter. Idempotent via the R5 key; `--reenrich` forces.
- **`ops enrich --all`** batch path: process sequentially under **one warm load** (raise `keep_alive`
  for the run, then unload) — avoids reloading a 5 GB model per note when `ingest` loops an inbox
  (QA R6). Auto-wiring enrich into `files extract`/`bookmark` uses this batch discipline.
- **Env:** `OPS_ENRICH_MODEL` (default `gemma4:e4b`), `OPS_ENRICH=auto|off`, `OPS_ENRICH_KEEP_ALIVE`, and
  a per-stage **`OPS_ENRICH_FAKE`** seam (one seam per stage — no global `OPS_MODELS_FAKE`, which would
  collide with `OPS_IMAGE_FAKE`; QA §4). Tests assert *wiring* (frontmatter written, index picks it up),
  never the non-deterministic output text.
- `ops doctor` gains a probe for the configured enrich model / runtime.

## 6. Adjacent gap: no verb reaches URL extraction (E4)

`_extract_one` already handles `is_url` and `_select_tier` already routes URL→`_tier_video`
(`files/run.py:243,186`) — the only gap is that **no verb writes a URL-path shadow note**. Fix as a
**parallel mini-flow in `ops files ingest <url>`** (write `wiki/files/<slug>.md` with `path: <url>` and
`derived_from` provenance) — *not* `bookmark --extract`, whose `type: bookmark` note lacks the
provenance the extract chain expects (QA "genuinely fine"). Note this is its own small flow: the local
`ingest` path sha256s + moves a file and inlines images, none of which apply to a URL.

## 7. What this deliberately does not add

No cloud model (Ollama/mlx only) · no daemon (files are the pipe; models load per-note/run and unload)
· no model-only dependency (stdlib keyword floor) · no big-bang refactor of shipped model code · no
per-stage runtime split · no auto-publish of generated meta beyond the note's own git-tracked frontmatter.

## 8. Build order (re-sequenced per QA — value first, refactor last)

| Pkg | What | Risk | Depends on |
|---|---|---|---|
| **E1** | `description`/`keywords` **block-list** schema in `conventions.md` (no index code, no `--reembed`) | low | — |
| **E2** | `bin/lib/enrichlib.py`: urllib→Ollama `generate(format=…)` + validate/`_parse_json_array` fallback; **stdlib** keyword floor (+ optional YAKE); determinism pin + idempotency key; empty-extraction guard; bounded input; `OPS_ENRICH_FAKE` seam + tests | med | E1 |
| **E3** | `ops enrich <slug>` + `--all` warm-batch, writing the **shadow** note; wire into `files extract`/`bookmark`; `doctor` probe | small | E2 |
| **S1** | `OPS_STT_MODEL`/`OPS_STT_RUNTIME` retrofit of `_tier_audio` only (the one real hardcoding) | low | — |
| **M1** | `ops models` verb (list/pull[`--yes`]/stop/status/test); route imagelib's ollama path through urllib (fixes the probe/runtime mismatch) | small | — |
| **E4** | `ops files ingest <url>` URL-path shadow → unblocks the video/URL tier | small | — |

**E1→E3 (the enrichment value) ship first** on the existing `agent.py`/`embed.py` patterns — no
dependency on any refactor. S1, M1, E4 are independent and can land in any order. A full model-provider
unification is deferred until a second runtime actually needs it. Every package stays behind its
per-stage `OPS_*_FAKE` seam so the offline suite is green with nothing pulled.
