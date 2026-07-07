# Search enrichment — generated meta for every source

**How-to.** Set up the model behind `ops enrich` (and the auto-enrich wired into `ops files extract` /
`ops bookmark`), and know what you get with none installed at all. Full design:
`docs/design/proposals/2026-07-07-search-enrichment-pipeline.md`.

## What it does

A source is only as findable as the text that describes it. `ops enrich` reads a note's derived text
— the `.extract.md` buffer for a file, or the note's own body for a bookmark/wiki note — and writes a
short `description` + `keywords` into that note's frontmatter via a small local LLM. Frontmatter is
already the top FTS chunk and leads the file within the embed window, so this makes the source both
keyword- and semantically-searchable with no new index code.

`ops files extract` and `ops bookmark` call this automatically after writing their own note (unless
`OPS_ENRICH=off`) — best-effort and non-fatal, so a model hiccup never fails the extract/save.

## Prerequisites & install

> [!IMPORTANT]
> Install the model into **the same Ollama that `ops` actually talks to** — not some other host or
> profile. This is the same "same interpreter/daemon `ops` runs" trap as vector search; see
> [`docs/agent-terminal-search.md`](agent-terminal-search.md) if enrichment works in your shell but
> not from an agent terminal.

```bash
ollama pull gemma4:e4b              # default — EN + Hungarian (140+ languages), ~5 GB
```

Alternatives (set via `OPS_ENRICH_MODEL`):

| Model | When |
|---|---|
| `gemma4:e4b` (default) | general EN + Hungarian use |
| `OpenEuroLLM-Hungarian` | Hungarian-max quality override |
| `gemma4:e2b` | low-RAM hosts |

No model pulled, and no Ollama running at all? Enrichment still runs — see **Degradation** below.

## Env knobs

| Knob | Values | Default | Effect |
|---|---|---|---|
| `OPS_ENRICH` | `auto`, `off` | `auto` | `off` disables enrichment entirely (no model call, no floor) |
| `OPS_ENRICH_MODEL` | an Ollama model tag | `gemma4:e4b` | Model used for `description`/`keywords` generation |
| `OPS_ENRICH_KEEP_ALIVE` | Ollama `keep_alive` value | `0` | `0` unloads the model after each call; `ops enrich --all` raises this to `5m` for the batch so a multi-GB model isn't reloaded per note |
| `OPS_STT_MODEL` | a model id for whichever ASR backend runs | backend's hardcoded default | Overrides the transcription model in `ops files extract`'s audio tier |
| `OPS_STT_RUNTIME` | `parakeet`, `mlx-whisper`, `faster-whisper`, `whisper-cli`, `auto` | `auto` | Pins one ASR backend instead of cascading through all installed ones |

## Usage

```bash
ops enrich <slug>              # enrich one note (idempotent — no-op if the text hasn't changed)
ops enrich <slug> --reenrich   # force past the idempotency key
ops enrich --all               # sweep every note lacking a current key, sequentially, one warm model load
```

`ops files extract` and `ops bookmark` call the same path automatically once they've written their
note — nothing to opt into beyond having a model reachable (or accepting the floor).

## `ops models` — see and swap what each stage uses

`ops models` is the management surface for every model-backed stage (`stt`, `ocr`, `vlm`, `enrich`,
`embed`, `rerank`), not just enrichment:

```bash
ops models list                        # per stage: configured model, runtime, pulled/available?
ops models status                      # ollama ps — resident (loaded) models
ops models stop [--all] [<model>]      # unload a resident model (reloads on next use, no data loss)
ops models pull --stage enrich --yes   # ollama pull the configured model for one stage (or --all)
ops models test enrich --yes           # run the stage's configured model on a sample, print output + timing
```

`pull` and `test` self-gate behind `--yes` — both can pull gigabytes. `test` is how you A/B a
candidate model before adopting it: run it with `--model <candidate>`, compare the output, then set
the stage's env var (e.g. `OPS_ENRICH_MODEL`) to make it permanent.

## Verify

```bash
ops doctor
```

`ops doctor` probes the configured enrich model against the local Ollama daemon (unless
`OPS_ENRICH=off`) and prints one of:
- `enrich model reachable (gemma4:e4b via Ollama)`
- `enrich model/Ollama not reachable — files extract/bookmark auto-enrich will fall back to the
  stdlib keyword floor (no description, no LLM keywords). Fix: run ollama and pull the configured
  OPS_ENRICH_MODEL; or set OPS_ENRICH=off.`

## Degradation

Enrichment never crashes an extract/save and never hallucinates on garbage input:

| Condition | Result |
|---|---|
| No model reachable | `description` falls back to the leading sentence(s) of the source text; `keywords` fall back to a deterministic stdlib frequency+stopword extractor (`keyword_floor`) — no pip deps, works with nothing installed |
| Text shorter than ~40 chars, empty, or the `_(no text extracted)_` sentinel | Skipped entirely — no model call, no floor description (an empty `description`, floor `keywords` if any text at all) |
| `OPS_ENRICH=off` | No enrichment at all — `files extract`/`bookmark` skip the call |
| Model reachable | Full `{description, keywords}` from `OPS_ENRICH_MODEL`, deterministic (temperature 0, fixed seed) so a re-run on unchanged text is a true no-op |

The floor keeps search improving even with zero models installed; a reachable model just makes the
`description` prose and the `keywords` sharper.
