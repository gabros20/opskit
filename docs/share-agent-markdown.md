# Agent access — read shared wiki notes

## The constraint (why two URLs exist)

E2E encryption puts the AES key in the URL **`#fragment`**. Browsers send that to JavaScript; **`curl`, Claude `web_fetch`, Codex fetch, and most agents never receive `#…` on HTTP GET.**

So:

| Audience | URL | What happens |
|----------|-----|----------------|
| **People (browser)** | `https://<worker>/<id>#<key>` | Viewer decrypts in the page; key stays off server logs |
| **Agents without ops** | `https://<worker>/<id>.md?k=<key>` | Worker decrypts once, returns **wiki markdown** (key on wire over TLS) |

You do **not** construct the agent URL yourself. **`ops share … --yes` prints it** as `agent_url` in `--json` and in the yellow **agents** line.

## Claude Code / Codex / any fetch tool (no ops)

Paste the **agent** line from publish (or `agent_url` from `ops share list --json`):

```text
https://ops-share.example.workers.dev/abc123xyz.md?k=b64urlKey…
```

Then: `curl`, `web_fetch`, `browse_page` — you get raw markdown (YAML frontmatter + body).

**Do not** paste only the browser link (`…/id#key`) into fetch tools — they will get the HTML shell or an error, not the note.

If you only have the human link, derive the fetch URL (same key, no manual editing):

```python
# sharelib.agent_fetch_url — also: ops share pull for local decrypt without ?k= on wire
from lib import sharelib
fetch_url = sharelib.agent_fetch_url("https://worker/id#key")
```

## With `ops` on the machine

```bash
ops share pull 'https://<worker>/<id>#<key>'   # decrypt locally; key never sent to worker
```

## Plain shares (`--plain`)

Agent URL is `https://<worker>/<id>.md` (no `?k=`).

## On-wire bundle (v1)

Markdown is the wiki **md** half of the OPSX bundle at publish time (collections joined with `\n\n---\n\n`).

## Legacy

HTML-only shares return HTTP 415 on `.md` — re-publish.

## Tests

- `sharelib.agent_fetch_url`, `pull_markdown_from_url`
- `test/run_backup_share.py`