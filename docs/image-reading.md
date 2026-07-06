# Reading images — metadata, OCR, and VLM description

**How-to.** Set up the model backends behind `ops files extract` on images, and know what you get
with none installed at all. Full design: `docs/design/proposals/2026-07-06-image-reading.md`.

## What it does

`ops files ingest <img>` and `ops files extract <slug>` read an image in up to three independent
layers, each gated by its own optional dependency and each degrading gracefully — none of them ever
crash the run:

1. **Metadata** (always on) — format, dimensions, EXIF capture date and camera. Written straight
   into the shadow note's frontmatter on `ops files ingest`. GPS/location EXIF is deliberately
   dropped; this is a vault that may later be shared.
2. **OCR** (`ops files extract <slug>`) — pulls text out of screenshots, scans, and photographed
   whiteboards, using a quality model first and a deterministic fallback if none is installed.
3. **VLM description** (`ops files extract <slug> --describe`) — an opt-in scene caption/description,
   the same shape as audio's `--describe`, written into the derived `.extract.md`.

## Prerequisites & install, per host

> [!IMPORTANT]
> Install every package below into **the same `python3` (and the same `ollama`) that `ops` actually
> runs** — not some other venv or shell. `ops` dispatches via bare `python3` on `PATH`, so a package
> installed elsewhere is invisible to it, and this bites agent terminals hardest since they often
> don't source your interactive shell's env. See
> [`docs/agent-terminal-search.md`](agent-terminal-search.md) for the venv/PATH setup and how to
> verify from inside an agent's own terminal.

| Layer | Apple Silicon (native, fast) | Intel / any host | Deterministic fallback (no model) |
|---|---|---|---|
| 1 — Metadata | `pip install Pillow` | `pip install Pillow` | stdlib only: format + bytes, no dimensions/EXIF |
| 2 — OCR | `pip install mlx-vlm` (runs GLM-OCR / DeepSeek-OCR) | running Ollama + `ollama pull glm-ocr` (or `ollama pull deepseek-ocr`) | `pip install ocrmac` (Apple Vision), then `brew install tesseract` |
| 3 — VLM describe | `pip install mlx-vlm` (runs Qwen3-VL / moondream) | running Ollama + `ollama pull qwen3-vl:4b` + `ollama pull moondream` | none — `--describe` is silently skipped |

Notes:
- `mlx-vlm` is the one package that covers **both** Layer 2 and Layer 3 on Apple Silicon — it's the
  same runtime for the OCR model and the VLM model, never two at once (see the design doc §3–5 for
  why). It's an `arm64`-only wheel; Intel and any host without it fall through to Ollama.
- On Intel or any host without `mlx-vlm`, Layer 2 and Layer 3 both run through Ollama — pull the
  models you intend to use with `ollama pull <model>`.
- If neither `mlx-vlm` nor Ollama is present, Layer 2 falls back to `ocrmac` (Apple Vision, Apple
  Silicon or Intel) then `tesseract` (any platform, zero model weights) — same fallback chain
  `ops files extract` already used for images before this feature shipped.
- Exact commands are also kept in `requirements.txt` under "Image reading" — treat that file as the
  source of truth if the two ever drift.

## Env knobs

| Knob | Values | Default | Effect |
|---|---|---|---|
| `OPS_OCR` | `auto`, `glm-ocr`, `deepseek-ocr`, `apple`, `tesseract`, `none` | `auto` | Pins or disables the Layer 2 cascade |
| `OPS_VLM` | a model tag, or `none` | `qwen3-vl:4b` | Layer 3 primary model; `none` skips `--describe` entirely |
| `OPS_VLM_FALLBACK` | a model tag | `moondream` | Used when the primary model isn't pulled/available |
| `OPS_MLX` | `auto`, `1`/`0` | `auto` | Single runtime switch for **both** Layer 2 and Layer 3 — prefer `mlx-vlm` over Ollama on Apple Silicon; `off` forces Ollama everywhere |
| `OPS_VLM_KEEP_ALIVE` | Ollama `keep_alive` value | `0` | `0` unloads the model immediately after each call; a duration (e.g. `5m`) keeps it warm across a batch |

## Verify

```bash
ops doctor                                  # probes every optional dep below and warns on mismatches
ops files ingest screenshot.png --extract --describe
```

`ops doctor` prints one line per probe:
- `optional: PIL present (image metadata (Pillow))` / `optional: PIL not installed (...)`
- `optional: mlx_vlm present (Apple-Silicon OCR/VLM runtime)` / not installed
- `optional: ocrmac present (Apple Vision OCR fallback)` / not installed
- `optional: ollama present (OCR/VLM runtime)` / not on PATH
- `optional: tesseract present (OCR fallback)` / not on PATH

If `OPS_VLM` is set but neither `mlx-vlm` nor `ollama` is reachable, `ops doctor` calls it out
explicitly: `OPS_VLM=<model> but neither mlx-vlm nor ollama is available — ops files extract
--describe will skip Layer 3 entirely`, with the same fix pointer as above.

A successful `ingest --extract --describe` on an image:
- Writes `format`/`width`/`height`/`taken`/`camera` frontmatter onto the shadow note (only the keys
  that were actually resolved — Pillow absent means only `format`/`bytes`).
- Writes the OCR'd text into `wiki/files/<slug>.extract.md` (`type: extract`, `tool: <backend used>`).
- With `--describe` and a VLM backend available, also adds a `## Description` section, `vlm_caption`
  frontmatter, and `vlm_backend` recording which model answered.

## What degrades to what

Nothing here ever throws — each layer either succeeds with the best available backend or hands back
a one-line install hint and moves on:

| Missing | Result |
|---|---|
| No `Pillow` | Layer 1 is format + byte size only; no width/height/EXIF; ingest still succeeds |
| No `mlx-vlm`, no Ollama | Layer 2 falls to `ocrmac`, then `tesseract`; `extract` still produces text |
| No `mlx-vlm`, no Ollama, no `ocrmac`, no `tesseract` | Layer 2 no-ops with an install hint; no OCR text |
| `--describe` with no VLM backend reachable | Layer 3 is skipped with a warning; the OCR result (if any) is still written |
| `OPS_OCR=none` / `OPS_VLM=none` | The corresponding layer is explicitly disabled, no probing attempted |
