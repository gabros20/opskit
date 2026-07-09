# Agent access — human link + `ops share pull`

Coding agents (Hermes, Claude Code, MCP) read shared wiki notes using the **same URL** you send humans. No `.md` suffix, no `?k=`, no `X-Ops-Share-Key`.

## URL (one link for everyone)

```text
https://<worker>/<id>#<key>
```

| Who | How |
|-----|-----|
| **Human** | Open in browser — viewer fetches `?raw=1`, decrypts with `#key` in JS, shows HTML |
| **Agent** | `ops share pull '<full url>'` — fetches `?raw=1`, decrypts locally, prints wiki markdown |

The worker **never** receives the AES key on either path.

## CLI

```bash
ops share pull 'https://ops-share.example.workers.dev/abc123xyz#b64urlKey…'
ops share pull 'https://…' --out /tmp/note.md
ops share pull 'https://…' --json   # markdown in data.markdown
```

After `ops share <slug> --yes`, the CLI prints the human link and:

```text
agents: ops share pull '<url>'
```

## Plain shares (`--plain`)

URL has **no** `#key`. Pull still works: blob is an OPSX bundle in the clear.

## On-wire bundle (v1)

Publish encrypts one OPSX payload (wiki markdown + rendered HTML). Pull returns only the **md** half, byte-identical to the wiki file(s) at publish time (collections joined with `\n\n---\n\n`).

## Legacy

HTML-only shares (pre-OPSX) fail pull with a re-publish hint.

## Deprecated (do not use for agents)

`GET /<id>.md` with header or `?k=` still exists on the worker for backward compatibility but is **not** the operator or agent contract. Prefer **pull**.

## Tests

- `sharelib.parse_share_link`, `markdown_from_blob`
- `test/run_backup_share.py` (pull round-trip via local HTTP stub)