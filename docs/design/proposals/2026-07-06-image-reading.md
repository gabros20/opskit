# Cross-architecture image reading — metadata, OCR, and VLM understanding

**Status: PROPOSED (2026-07-06).** High-level design, not yet accepted.
Closes the image-understanding half of
[issue #1](https://github.com/gabros20/personal-operating-system/issues/1) ("how does artefacts like
images... get stored and associated with a note?"). The storage/association half — ingest, the shadow
note, dedup by sha256 — already shipped in v4 (`ops files ingest`); this proposal is what happens when
`ops files extract` meets an image instead of a PDF or an audio file.

The design bet, stated up front: **the audio tier already proved the shape.** `_tier_audio` in
`bin/files/run.py` walks a cascade of auto-detected optional backends (`parakeet-mlx` → `mlx-whisper` →
`faster-whisper` → a system binary → a one-line install hint) and never crashes on a missing dep. Image
reading needs the same cascade, twice — once for OCR, once for VLM understanding — plus one thing audio
never had to worry about: it must work **identically well on Apple Silicon and Intel**, because both
architectures are in play (a Mac Mini running scheduled jobs is not guaranteed to be Apple Silicon).

---

## 0. The three layers

Reading an image is not one operation — it's three, escalating in cost and each independently gate-able:

| Layer | What | Cost | Always runs? |
|---|---|---|---|
| **1 — Metadata** | format, dimensions, EXIF (capture date, camera, orientation) | ~0ms, stdlib | Yes — zero-model, always on |
| **2 — OCR** | text embedded in the image (screenshots, scanned docs, photographed whiteboards) | seconds, small model | On request (`--extract`), quality-first |
| **3 — VLM understanding** | caption / description / structured "what is this" | seconds–tens of seconds, larger model | Opt-in (`--describe`), same shape as audio's `--describe` flag |

Each layer degrades independently and never blocks the one below it: no `Pillow` means Layer 1 falls
back to stdlib basics (format + dimensions only, no EXIF); no OCR backend means Layer 2 emits the same
kind of one-line install hint `_tier_audio`/`_tier_image` already use today; no VLM backend means Layer
3 is silently skipped, not a hard failure. **GPS/location EXIF is deliberately dropped at Layer 1** —
this is a personal vault that syncs by git and may be shared later (`ops share`); embedding a home
address in every photo's derived note is a privacy leak the extraction step should never introduce.

## 1. Layer 1 — metadata (always on, zero-model)

- **With `Pillow` present:** format, width × height, EXIF capture date, camera make/model, orientation.
  Read-only (`Image.open` + `.getexif()`); the source bytes in `~/files` are never touched.
- **Without `Pillow`:** format and dimensions only, via stdlib (`imghdr`-equivalent header sniffing +
  the image's own header for dimensions where the format allows it cheaply). No EXIF, no crash.
- Output shape matches the existing extract note contract (Part 4.1): a derived sibling note
  (`wiki/files/<slug>.extract.md`) with `type: extract`, `derived_from`, `source_sha256`, `tool:
  Pillow <version>` or `tool: stdlib-image-meta 1.0`.

## 2. Layer 2 — OCR (quality-first, cross-architecture)

Two model options, both run through **two different runtimes** depending on the host's architecture —
the same split the audio tier draws between `parakeet-mlx` (Apple-Silicon-only, MLX) and
`mlx-whisper`/`faster-whisper`/`whisper.cpp` (portable):

| Model | Quality | Size | Apple Silicon runtime | Intel / any runtime |
|---|---|---|---|---|
| **GLM-OCR** (0.9B) | OmniDocBench 94.6 | ~2–3GB | `mlx-vlm` | Ollama |
| **DeepSeek-OCR** | higher, slower | ~5GB | `mlx-vlm` | Ollama |
| *(fallback)* `ocrmac` | good, Apple Vision | negligible | Apple Vision framework | — |
| *(fallback)* `tesseract` | baseline | negligible | system binary | system binary |

Cascade order (mirrors `_tier_audio`'s auto-detect-then-degrade shape in `bin/files/run.py`), gated by
the **single `OPS_MLX` switch that also governs Layer 3** (see §3 — one runtime per host, not a
per-layer choice):

1. `mlx_vlm` importable **and** on Apple Silicon **and** `OPS_MLX` != off → GLM-OCR (default) or
   DeepSeek-OCR (`OPS_OCR=deepseek-ocr`), run via `mlx-vlm`.
2. `ollama` on PATH (any architecture, including Apple Silicon when `OPS_MLX=off` or `mlx_vlm` isn't
   installed) → same two models, pulled as GGUFs (`ollama pull <model>`), run via the Ollama HTTP API.
3. `ocrmac` importable (Apple Silicon or Intel — Apple Vision ships on both) → deterministic, no model
   download, matches what `_tier_image` already does for the non-VLM OCR case today.
4. `tesseract` on PATH → baseline, works everywhere, zero model weights.
5. None present → no-op with a one-line install hint, same contract as every other tier.

`OPS_OCR` (`auto` | `glm-ocr` | `deepseek-ocr` | `apple` | `tesseract` | `none`) pins a specific model
tier instead of walking the cascade — the same override idiom `OPS_AGENT`/`OPS_RERANK_MODEL` already
use. It selects the *model*; `OPS_MLX` selects the *runtime*, and applies identically to Layer 3.

## 3. Layer 3 — VLM understanding (opt-in, `--describe`)

**One runtime per host, not a per-layer choice.** Layer 3 follows the *exact same* `OPS_MLX`-gated
cascade as Layer 2 (§2) — whichever runtime Layer 2 resolved to (`mlx-vlm` or Ollama) is the runtime
Layer 3 uses too, on that host, for that run. A single Apple Silicon machine never runs `mlx-vlm` for
OCR and Ollama for VLM side by side: that would mean two model runtimes resident at once, which cuts
against §5's peak-memory discipline and doubles the surface to keep working. One switch, one decision:

| Model | Size (Q4) | Apple Silicon (`OPS_MLX` != off, `mlx_vlm` present) | Otherwise (`OPS_MLX=off`, Intel, or no `mlx_vlm`) |
|---|---|---|---|
| **Qwen3-VL 4B** (primary) | ~6GB | `mlx-vlm` | Ollama |
| **moondream** (fallback) | <4GB | `mlx-vlm` | Ollama |
| *(no model)* | — | skip, note the description as unavailable | skip |

Ollama's v0.19+ MLX acceleration means the two runtimes are close enough in practice on Apple Silicon
that trading them for simplicity is a good deal — it is *not* a reason to split Layer 2 and Layer 3
across runtimes on the same host. `OPS_VLM` (default `qwen3-vl:4b`) and `OPS_VLM_FALLBACK` (default
`moondream`) select the model; `OPS_MLX` (`auto` by default, meaning "prefer `mlx-vlm` when available on
Apple Silicon") is the one switch that picks the runtime for both Layer 2 and Layer 3 together.

## 4. On-demand load/unload — no daemon, no idle memory

Consistent with the anti-roadmap's **no daemon, ever** verdict (v4 roadmap, ADR-007): nothing in this
proposal runs as a resident process.

- **Ollama** already loads a model into memory on first request and keeps it warm for a configurable
  window. `OPS_VLM_KEEP_ALIVE` (default `0`) is passed as Ollama's `keep_alive` parameter — `0` unloads
  the model **immediately** after the response, so a Qwen3-VL 4B load doesn't sit in RAM between calls.
  `ollama ps` / `ollama stop <model>` are the manual escape hatches doctor can point at if a model gets
  stuck loaded.
- **`mlx-vlm`** has no daemon to unload from in the first place — it runs in-process inside the
  `python3` that `ops files extract` already spawns per verb call (the same "no daemon" property every
  other extraction tier has today), and the model's memory is freed when that process exits.

## 5. Sequential-run peak-memory discipline

`ops files extract` processes one file per invocation today, which already caps peak memory at "one
model's worth" — but a batch caller (e.g. `ops files extract` looped over an inbox of screenshots, or a
future `--all` flag) must not let Layer 2 and Layer 3 models overlap in memory. Peak footprint by model:
GLM-OCR ~2–3GB, DeepSeek-OCR ~5GB, Qwen3-VL 4B ~6GB, moondream <4GB, `ocrmac`/`tesseract` negligible.
Worst case (DeepSeek-OCR + Qwen3-VL held concurrently) is ~11GB, which is unnecessary and avoidable:

- **Run tiers sequentially per file, never concurrently.** OCR completes (and, for Ollama, unloads via
  `keep_alive:0`) before the VLM call begins. `mlx-vlm`'s per-process lifetime already enforces this
  for free — the OCR subprocess exits before the VLM subprocess starts.
- **A batch loop processes one file fully before starting the next.** No pre-fetching, no pipelining
  across files. This trades wall-clock time for a flat, predictable memory ceiling — the right trade for
  a personal vault running on a laptop or a shared Mac Mini, not a throughput-optimized pipeline.

## 6. Env knobs

Mirrors the existing `OPS_AGENT`/`OPS_VECTORS`/`OPS_RERANK` idiom (string envs, `auto`/model-name/`none`
values, always soft-degrading):

| Knob | Values | Default | Effect |
|---|---|---|---|
| `OPS_OCR` | `auto`, `glm-ocr`, `deepseek-ocr`, `apple`, `tesseract`, `none` | `auto` | Pins or disables the Layer 2 cascade |
| `OPS_VLM` | a model tag, or `none` | `qwen3-vl:4b` | Layer 3 primary model; `none` skips `--describe` entirely |
| `OPS_VLM_FALLBACK` | a model tag | `moondream` | Used when the primary model isn't pulled/available |
| `OPS_MLX` | `auto`, `1`/`0` | `auto` | Single runtime switch for **both** Layer 2 and Layer 3 — whether `mlx-vlm` is preferred over Ollama on Apple Silicon (never split per-layer) |
| `OPS_VLM_KEEP_ALIVE` | Ollama `keep_alive` value | `0` | `0` unloads immediately; a duration (e.g. `5m`) keeps warm for a batch run |
| `OPS_IMAGE_FAKE` | unset, or a canned response path/string | unset | Test seam — see §7 |

## 7. The `OPS_IMAGE_FAKE` test seam

Every model-backed tier in this codebase needs a way to be tested without downloading gigabytes of
weights or running on a specific architecture. `OPS_IMAGE_FAKE` follows the same shape as the existing
deterministic-mode env vars used elsewhere in the test suite: when set, `bin/lib/imagelib.py`'s OCR and
VLM entry points short-circuit to a canned, deterministic response (read from the path `OPS_IMAGE_FAKE`
points at, or a fixed string if it's a sentinel value) instead of touching `mlx_vlm`/Ollama/`ocrmac`. CI
and the local test suite can then exercise the full extract → derived-note → provenance-frontmatter
pipeline on every architecture, with no optional deps installed and no network/model calls, the same way
the share suite's Node cross-check (CHANGELOG, Unreleased) verifies byte-level behavior without needing
`cryptography` installed.

## 8. What this deliberately does not add

No daemon (Ollama's own server is opt-in and already the sanctioned pattern; `mlx-vlm` stays
per-process) · no cloud OCR/VLM API (local-only, matches every other extraction tier) · no new storage
plane (Layer 1–3 output is just another `wiki/files/<slug>.extract.md` derived note, same contract as
PDF/audio/video extraction) · no GPS/location persisted anywhere (dropped at Layer 1, not merely
unused) · no concurrent multi-model residency (§5's sequential discipline) · no batch/pipelining flag in
this proposal — that's a separate, later `--all` design once single-file extraction is proven.

## 9. Build order

| Pkg | What | New code | Depends on |
|---|---|---|---|
| I1 | `bin/lib/imagelib.py`: Layer 1 metadata (Pillow → stdlib fallback) | small | — |
| I2 | `_tier_image` upgrade in `bin/files/run.py`: OCR cascade (GLM-OCR/DeepSeek-OCR via `mlx-vlm`/Ollama → `ocrmac` → `tesseract`), `OPS_OCR` | medium | I1 |
| I3 | `--describe` flag: Layer 3 VLM cascade (Qwen3-VL → moondream → skip), `OPS_VLM`/`OPS_VLM_FALLBACK`/`OPS_MLX`/`OPS_VLM_KEEP_ALIVE` | medium | I2 |
| I4 | `OPS_IMAGE_FAKE` test seam + fixtures, exercised on both architectures in CI | small | I1–I3 |
| I5 | `ops doctor` probes for the new optional deps + pointed `OPS_VLM`-without-a-runtime warning (this proposal's companion change) | small | — |

I1–I3 are the core extraction path and roughly a weekend each; I4 and I5 can land alongside I1 since
they don't depend on the runtime cascades being complete.
