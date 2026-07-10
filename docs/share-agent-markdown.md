# Agent access — read shared wiki notes

There is one link. Append `.md` and any agent with a fetch tool reads the exact wiki source.

## The link

`ops share <slug> --yes` prints:

```text
shared note <slug>
  https://ops-share.example.workers.dev/abc123def456ghi789jkl012
  agents / LLMs: https://ops-share.example.workers.dev/abc123def456ghi789jkl012.md   (raw markdown — paste into any chat/coding agent)
  revoke: ops share revoke abc123def456ghi789jkl012 --yes
```

- **A browser** opening the bare URL gets the rendered HTML page.
- **An agent** (Claude Code, Codex, `curl`, `web_fetch`, any fetch tool) — append `.md`, or paste
  the printed `agents / LLMs:` line as-is — gets `text/markdown; charset=utf-8`: the wiki source, YAML
  frontmatter and body, byte-identical to what was published.

No headers, no keys, no query strings, no URL math beyond "add `.md`". `agent_url` in `--json` output
and `ops share list --json` is always `url + ".md"`.

## Content negotiation (the lazy-paste bonus)

The bare URL (no `.md`) also serves markdown to anything that isn't a browser: the worker checks
`Accept` and returns HTML only when it contains `text/html`; `curl`'s default `*/*` and most agent
fetch tools get markdown straight off the bare link. `.md` stays the documented, deterministic
contract — negotiation just means pasting the plain link into an agent tends to work too.

```sh
curl https://<worker>/<token>.md      # markdown, guaranteed
curl https://<worker>/<token>         # markdown too, via negotiation (non-browser Accept)
```

## With `ops` on the machine

```bash
ops share pull 'https://<worker>/<token>'   # fetch + unpack locally, same markdown, no browser
```

`ops share pull <url> [--out file.md]` works on the bare link or the `.md` link interchangeably —
it normalizes either into the same fetch.

## Legacy links

Anything published under the previous encrypted (`#fragment` / `?k=` / `X-Ops-Share-Key`) model is
dead: every route for a legacy blob returns **HTTP 410** with a `re-publish with current ops share`
hint. There is no key to recover it with — re-run `ops share <slug> --yes` to get a current link.

## Tests

- `bin/lib/sharelib.py`: `parse_share_link`, `markdown_from_blob`, `pull_markdown_from_url`
- `test/run_backup_share.py`
