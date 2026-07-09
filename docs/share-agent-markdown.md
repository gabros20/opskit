# Agent-accessible markdown (`/{id}.md`)

Extension to **ops share** (Part 5.2) so coding agents and cloud chat tools can **fetch raw markdown** from a share link—not only the human HTML viewer.

## URL pattern

| URL | Purpose |
|-----|---------|
| `https://<worker>/<id>#<key>` | Human browser viewer (HTML, zero-knowledge fragment) |
| `https://<worker>/<id>.md` | **Agent** — same UTF-8 as the wiki file(s) on disk (no wrapper, no llms.txt header) |

`<id>` is the existing 10-character share id; `.md` is a suffix, not part of the id.

**Single note:** `GET /{id}.md` body is **byte-identical** to `read_text()` of that wiki path at publish time.

**Collection:** notes are concatenated with `\n\n---\n\n` between files (each file’s content unchanged).

## Security model

**Zero-knowledge is unchanged for humans:** the AES key stays in the URL `#fragment` for the HTML viewer (fragments are not sent to the server).

**Agents cannot use fragments:** HTTP clients do not send `#…` to the origin. The same key via:

1. **Preferred:** header `X-Ops-Share-Key: <key>` (same value as the `#fragment`, without `#`).
2. **Convenience:** query `?k=<key>` — may appear in CDN/proxy logs. Documented tradeoff.

Without a key on an **encrypted** share, `GET /{id}.md` returns **401** with a short JSON hint—not the ciphertext.

**Plain shares** (`--plain`): no key; `/{id}.md` returns markdown directly (secrecy = unguessable id + TTL).

## On-wire bundle (v1)

Publish encrypts **one** payload: **OPSX** multipart (wiki markdown + rendered HTML). Agent route returns only the **md** half, unchanged.

```text
OPSX  (4 bytes magic)
u8 version = 1
3 bytes reserved (0)
u32 md_len BE
u32 html_len BE
md bytes (UTF-8, wiki source)
html bytes (UTF-8, self-contained HTML from sharelib)
```

**Legacy** HTML-only shares still open in the browser; `/{id}.md` returns **415** until re-published.

## Operator output

After `ops share <slug> --yes`, the CLI prints the human link and `agent md:` URL + key instructions.

## Tests

- `sharelib.pack_bundle` / `unpack_bundle` round-trip
- Fake publish: decrypted payload has `OPSX` magic
- `test/run_backup_share.py`