# Search enrichment — generated meta (description + keywords) for every source

**Status: PROPOSED (2026-07-07).** Design, not yet accepted. Companion to the
[image-reading proposal](2026-07-06-image-reading.md) (implemented) and the search/index ADRs
(ADR-005 embedder, ADR-006 vectors). Closes the *findability* half of the ingestion story that
[issue #1](https://github.com/gabros20/personal-operating-system/issues/1) opened.

The bet: **a source is only as findable as the text that describes it — and right now nothing
generates that text.** We add ONE modality-agnostic stage that turns any extracted content into a
short `description` + `keywords`, written to frontmatter, feeding both keyword and semantic search.

---

## 0. The problem — searchability today is accidental

Traced through `bin/lib/indexlib.py`:
- **Keyword search (FTS5)** indexes each note's `heading + body`.
- **Semantic search** embeds `title + frontmatter + body`, capped at **2000 chars** (`_embed_text`).
- The note schema (`wiki/conventions.md`) is `type/title/status/created/updated/tags/aliases` — **no
  `description`, and `tags` ships empty.**

So a source is findable **only to the extent raw text lands in its note body**:
- An **image** shadow note (`title` + `![](path)` + file metadata) has ~no text → invisible unless
  you separately run `extract` *and* its OCR/caption happens to contain the query words.
- A **voice memo / video / PDF** is findable only via its raw transcript/markdown dump — no distilled
  description, no topical keywords.
- A **bookmark** works only because trafilatura dumps the article body in — again, no summary, no tags.

There is **no meta-generation stage**. That is the gap.

## 1. The enrich stage — one stage, every modality

Every modality already funnels to text; enrichment is modality-agnostic and slots after extraction:

```
                          ┌──────────────── the ONE new stage ────────────────┐
 source ─▶ modality extractor ─▶ TEXT (the .extract note) ─▶ summarize+tag LLM ─▶ {description, keywords} ─▶ frontmatter ─▶ index
 image    OCR + VLM caption          = the durable "working memory"                gemma4:e4b via Ollama
 voice    whisper transcript                                                       structured outputs (JSON schema)
 video    yt-dlp captions
 pdf      pymupdf4llm markdown
 link     trafilatura article text
```

**The `.extract.md` note IS the working memory / pipe.** Piping one model's output into the next is a
*file*, not a RAM buffer: the modality extractor writes text to the derived note; the enrich model
reads that file and writes `description`/`keywords` back into the note's frontmatter. Durable,
resumable, inspectable, no daemon — the ops way. For images, OCR text *and* the VLM caption both land
in the note, then the summarizer condenses both.

## 2. The model matrix (all local, on-demand, cross-arch)

The modality extractors already ship; the **text summarize+tag model is the only new piece**.

| Stage | Model | Runtime |
|---|---|---|
| image → text | Qwen3-VL (caption) + GLM-OCR/DeepSeek-OCR (text) | mlx-vlm / Ollama |
| voice/audio → text | whisper (mlx-whisper / parakeet / faster-whisper) | shipped |
| video/YouTube → text | yt-dlp captions | shipped |
| pdf → text | pymupdf4llm / docling | shipped |
| link → text | trafilatura | shipped |
| **text → {description, keywords}** | **`gemma4:e4b`** (default) | **Ollama, structured outputs** |

**Why Gemma 4 E4B for the enrich model (EN + Hungarian).** Gemma 4 (Apr 2026) ships edge-tuned
"effective-parameter" variants — `e4b` is ~5 GB in 4-bit, 128K context, 140+ languages with **good
Hungarian** — ideal for a spin-up-per-note model. Ollama's native **structured outputs** enforce a
JSON schema (`{"description": str, "keywords": [str]}`), so a 4–5B model emits valid meta without
parsing gymnastics. It's a clear upgrade over Gemma 3 for this role.

- **`OPS_ENRICH_MODEL=gemma4:e4b`** — default; strong at both English and Hungarian in one model.
- **`jobautomation/OpenEuroLLM-Hungarian`** — a Gemma-3 fine-tune specialized for authentic Hungarian;
  documented as the drop-in HU-max override (at some cost to English/general strength).
- **`gemma4:e2b`** (~1.5 GB) — low-RAM fallback (weaker on HU + multi-step).

**Lifecycle — sequential, peak = one model.** Run stages in order and unload between: the modality
extractor loads → text → unloads (`keep_alive:0` / process exit) → the enrich model loads → writes
meta → unloads. Peak RAM ≈ the larger single model (~5–6 GB), never the sum — the same discipline as
the image design. `OPS_ENRICH_KEEP_ALIVE=0` by default.

### 2.1 Swappable by construction — one provider, uniform config, `ops models`

Model choice must be **env config, not code** — so you can A/B any Ollama-compatible model, retrofit a
new speech-to-text engine, or add a runtime without touching a verb. Today that's only half-true
(OCR/VLM/embed have env knobs, but the **audio/STT tier hardcodes** `mlx-community/parakeet-tdt-0.6b-v2`
with no override, the env names are ad-hoc, and there is no download/offload surface). This proposal
therefore lands on a small model-layer foundation (build package **E0**):

- **One provider — `bin/lib/models.py`.** Every model-backed stage (`stt`, `ocr`, `vlm`, `enrich`,
  `embed`, `rerank`) resolves `(model, runtime, keep_alive, fallback)` from env and calls
  `models.generate(stage, …)`. Runtimes are pluggable: `ollama` (HTTP, `keep_alive`), `mlx`
  (mlx-vlm / mlx-whisper), `builtin` (paddle, faster-whisper, deterministic tools). `imagelib`,
  `enrichlib`, and the audio tier become thin callers. **Adding a model = an env var; adding a runtime
  = one provider extension; nothing else changes.**
- **Uniform env contract.** `OPS_<STAGE>_MODEL`, `OPS_<STAGE>_MODEL_FALLBACK`, `OPS_<STAGE>_RUNTIME`
  (else `OPS_MLX=auto` decides), and a global `OPS_MODEL_KEEP_ALIVE` (default `0`). Existing names
  (`OPS_VLM`, `OPS_OCR`, `OPS_EMBED_MODEL`, `OPS_RERANK_MODEL`, `OPS_AGENT_MODEL`) keep working as
  back-compat aliases. **STT joins the contract:** `OPS_STT_MODEL`/`OPS_STT_RUNTIME` retrofit the audio
  tier, so whisper/parakeet — or a different ASR entirely — swap by setting one variable.
- **`ops models` — the download / offload / test surface (the "script" you want, as a verb):**
  - `ops models list` — per stage: configured model · runtime · pulled? · resident?
  - `ops models pull [--stage <s> | --all]` — `ollama pull` the configured models (the *download*).
  - `ops models stop [--all]` — `ollama stop` (the *offload* / wind-down); `status` → `ollama ps`.
  - `ops models test <stage> [--model <m>] [--input <file>]` — pull if needed, run the stage on a
    sample (or your file), print output + timing. **This is "test a new model on demand"**: A/B a
    candidate against the current default with zero wiring, then adopt it by setting its env var.
  A `builtin`/`OPS_MODELS_FAKE` seam keeps the offline suite green with nothing pulled.

The rest of this proposal (enrich stage, schema, fallback) sits on top of this layer: the enrich model
is just `OPS_ENRICH_MODEL` resolved through the same provider as every other stage.

## 3. Schema + index changes (so the meta is actually searched)

- Add **`description`** (1–2 sentences) and **`keywords`** (5–10 topical terms) to `wiki/conventions.md`.
- **Embed:** `_embed_text` should lead with `description` so it survives the 2000-char cap; frontmatter
  is already included in the embed, so populated `keywords` help retrieval immediately.
- **FTS:** index `description` + `keywords` into the searchable `body` column (prepend them, or add
  columns) so keyword search matches them, not just the raw dump.
- Backfill: a one-time `ops index --reembed` after enriching existing notes.

## 4. Deterministic fallback (never model-only)

With no enrich model available, a **pure-Python keyword extractor (YAKE or RAKE, stdlib-ish)** still
populates `keywords` from the extracted text, and the first sentences become a crude `description`. So
search improves **even offline / with no model pulled** — matching the deterministic-first rule the
whole system holds. The LLM is an accelerator, not a dependency.

## 5. The verb and wiring

- A new **`ops enrich <slug>`** stage (sibling to `distill`): reads a note's derived text → generates
  `description`/`keywords` → writes frontmatter. Idempotent (skip if present + source unchanged;
  `--reenrich` forces). Risk `safe_write`.
- **Wire into the flow:** `ops files extract` and `ops bookmark` gain an enrich step (or auto-run
  `enrich` as a follow-on), so every ingested source gets meta without a manual step.
- **Env knobs** mirror the rest: `OPS_ENRICH_MODEL` (default `gemma4:e4b`), `OPS_ENRICH=auto|off`,
  `OPS_ENRICH_KEEP_ALIVE`, and an `OPS_ENRICH_FAKE` seam so the offline suite tests the wiring with no
  model (as `OPS_IMAGE_FAKE`/`OPS_SHARE_FAKE` do).

## 6. Adjacent gap (found while documenting the surface): no verb reaches URL extraction

`ops files extract`'s video/URL tier (yt-dlp captions) **has no verb-based entry for a bare URL**:
`ops files ingest` rejects URLs, and `ops bookmark` writes a different note shape (`type: bookmark`
with `url:`, not a `wiki/files/<slug>.md` shadow with `path:`). So a YouTube/video link can't be
transcribed today. Fix options (adjacent, small): teach `ops files ingest <url>` to write a URL-path
shadow note, or bridge `ops bookmark --extract <url>` → run the video/URL tier on the fetched URL.
Enrichment then applies to the resulting transcript like any other source.

## 7. What this deliberately does not add

No cloud model (Ollama/mlx-vlm only) · no daemon (files are the pipe; models load per-note and unload)
· no model-only dependency (deterministic keyword fallback) · no new sync/transport · no auto-publish
of generated meta beyond the note's own frontmatter (it's descriptive, revertible git text).

## 8. Build order

| Pkg | What | New code | Depends on |
|---|---|---|---|
| **E0** | **`bin/lib/models.py` provider** (ollama/mlx/builtin runtimes) + uniform `OPS_<STAGE>_MODEL` env with back-compat aliases + **`ops models` verb** (list/pull/stop/status/test) + retrofit OCR/VLM/**STT**/embed to route through it | med | — |
| E1 | `description`/`keywords` schema (`conventions.md`) + index support (embed lead + FTS) + `--reembed` | small | — |
| E2 | `bin/lib/enrichlib.py`: the summarize+tag call (structured outputs via the provider) + YAKE/RAKE deterministic fallback + `OPS_ENRICH_FAKE` seam + unit tests | small–med | E0, E1 |
| E3 | `ops enrich <slug>` verb + wire into `files extract` / `bookmark`; `ops doctor` probe for the enrich model | small | E2 |
| E4 | *(adjacent)* URL entry for the video tier (`ingest <url>` or `bookmark --extract`) | small | — |

**E0 is the modularity foundation** — do it first; it makes every stage's model swappable by env and
adds the download/offload/test surface, and can ship on its own (it's pure refactor + a new management
verb, backward-compatible). E1–E3 are the enrichment pipeline on top; E4 unblocks YouTube/video
transcription. Each package ships behind the `OPS_*_FAKE` seam so the offline suite stays green with
no model pulled.
