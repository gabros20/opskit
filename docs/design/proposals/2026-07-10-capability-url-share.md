# Proposal — capability URLs for `ops share` (drop zero-knowledge, one link + `.md`)

**Status:** ACCEPTED (2026-07-10) — implemented this refactor.
**Author:** Fable (orchestrated implementation) + operator (Tamas) decision.
**Related:** `docs/DECISIONS.md` (ADR-008), `docs/backup-and-share.md` (§`ops share`),
`docs/share-agent-markdown.md`, `bin/share/worker/README.md`,
`docs/design/proposals/2026-07-10-ops-share-agent-markdown-url.md` (superseded by this proposal).

---

## 0. The bet

The operator's actual job with `ops share` is: **paste one link into any chat/coding agent and it
reads the note.** No headers, no second URL, no local tooling, no URL math. Every zero-knowledge
(ZK) variant tried against that bar failed it — not from lack of engineering effort, but because ZK
and "one server-fetchable link" are in tension at the protocol level (§2). This proposal drops ZK and
replaces it with a **capability URL**: a long unguessable token, stored plaintext, over TLS, with a
TTL — and gets the one-link contract for free.

## 1. Context — the ergonomics failure, and why it recurred

The share system was zero-knowledge: the note is encrypted locally (AES-256-GCM), only ciphertext
goes to the Cloudflare Worker + KV, and the key rides the URL `#fragment` (PrivateBin pattern). That
property is the direct cause of the ergonomics failure the operator kept hitting: **HTTP never sends
the fragment to a server**, so no single URL can be both `#`-based (for zero-knowledge) and fetchable
by a server-side agent tool. Every attempted patch produced either a two-URL contract or an
install-something contract, and each was tried and rejected in turn:

| Idea tried | What it gives agents | Why it was rejected |
|---|---|---|
| `?k=<key>` query param appended to `.md` | one URL to paste | key lands in worker access logs, proxies, and browser history if opened in a GUI browser — and once the key is on the wire to the server, ZK has already been given up in substance |
| `X-Ops-Share-Key` header | key off the URL | most generic agent fetch tools (`web_fetch`, `browse_page`, bare `curl` one-liners) can't attach custom headers — unusable as a default path |
| `agent_url` printed as a **second line** alongside the human link | technically one URL per audience | still a two-link contract — the exact problem being solved, just relabeled |
| `ops share pull '<human url>'` (local decrypt, ZK preserved) | preserves zero-knowledge | requires `ops` installed on the fetching machine — fails "any chat/coding agent," which is the actual requirement |
| Mechanical URL-math instructions (split on `#`, insert `.md`, append `?k=`) so an agent derives the fetch URL itself | one URL, in principle | fragile, an extra reasoning step, and still requires the key to leave the fragment somewhere — doesn't dodge the core constraint |
| `/<id>/md` path alias, `/open?u=<encoded url>` proxy, client-side agent page (fetch blob + `#key` in a headless browser) | minor variations on the above | same key-exposure or two-URL tradeoffs, extra routes for no new capability (surveyed in the superseded proposal §3, §11.5) |

**Don't re-litigate these.** Every research pass (industry survey of PrivateBin/ZeroBin/Firefox
Send/Bitwarden Send/1Password secure share, `docs/design/proposals/2026-07-10-ops-share-agent-markdown-url.md`
§11) reached the same conclusion: **no surveyed system offers encrypted server-side markdown with
only `path + .md` and a fragment-only key** — that combination is logically inconsistent, not an
engineering gap to close with more cleverness.

## 2. Why "just add `.md`" cannot work under E2E

| URL piece | Sent to the origin server on `GET`? |
|---|---|
| Path `/<id>` | Yes |
| Query `?k=...` | Yes |
| Fragment `#<key>` | **No** — RFC 9110 / RFC 3986: the fragment is resolved client-side only |

The human viewer decrypts in the browser using `#key`; the worker never sees it. A server-side
`GET /<id>.md` that must return **decrypted** markdown needs the key in path, query, or a header —
there is no fourth option, and all three were tried and rejected above. Once the key must be visible
to the server for *any* agent-fetchable route to exist, encryption is providing no protection beyond
what an unguessable token already provides — so we remove it and keep the one property that was
actually load-bearing: **the link is hard to guess.**

## 3. The decision — capability URL

**New security model:** the OPSX bundle (raw markdown + rendered HTML, already the publish format)
is stored **plaintext** in KV under a 24-char unguessable token (`[a-z0-9]{24}`, ~124 bits, up from
the old 10-char/~52-bit id — the URL is now the entire secret), over TLS, with native KV TTL expiry.
Same trust model as a secret gist or "anyone with the link" docs — the trust model already accepted
for the `--gist` fallback. Cloudflare can technically read shared notes; that is accepted, not
overlooked (ADR-008). `PUT /` additionally requires a matching `X-Publish-Token` header when the
`PUBLISH_TOKEN` wrangler secret is set, so a discovered endpoint can't be abused as a free anonymous
file host.

### Resulting UX (the whole point)

```
ops share <slug> --yes
  → https://<worker>/<24-char-token>          ← the ONE link
      browser opens it            → rendered HTML page
      append .md (agents)         → raw wiki markdown, text/markdown
      curl / web_fetch bare URL   → raw markdown too (content negotiation)
```

Paste `<url>.md` into Claude/Codex/any chat agent with a fetch tool → it reads the exact wiki source.
No headers, no keys, no local tooling, no URL math beyond "add `.md`".

## 4. URL pattern decision

- **`/<token>.md` is the canonical agent form.** The token alphabet `[a-z0-9]` contains no dots, so
  suffix parsing is unambiguous; `.md` reads as "fetch this document" to every tool; it's the
  emerging docs-site convention (the llms.txt ecosystem serves per-page `.md`). Rejected: a `/md`
  path alias (a second route for zero gain over the suffix), `/llms.txt` (that convention names a
  site index, not a single document).
- **Content negotiation on the bare URL is a bonus, not the contract.** `Accept` containing
  `text/html` → HTML page; anything else (curl's `*/*`, most fetch tools) → markdown. `.md` stays the
  deterministic, documented contract; negotiation just makes the lazy paste work too.
- **Token: 24 chars `[a-z0-9]` (~124 bits)**, generated by the worker — because the URL is now the
  entire secret, it needs the entropy budget the AES key used to carry. The admin token (revoke)
  stays 24 chars, unchanged.

## 5. What changes, file by file

- **`bin/share/worker/worker.js`** (rewrite, ~120 lines down from 246) — delete the `VIEWER` HTML/JS
  blob, `decryptBytes`, `b64uDec`, `shareKeyFromRequest`, the `?k=`/`X-Ops-Share-Key` handling, and
  the decrypt branch of markdown resolution. Keep `unpackBundle` (OPSX v1 parse), `randId`, the `json`
  helper, the KV `blob:`/`admin:` key scheme, and `expirationTtl`. New routes: `PUT /` (plaintext body,
  `X-Expire-Seconds`, 24MB cap, `X-Publish-Token` gate); `GET /<id>.md` (markdown half); `GET /<id>`
  (content-negotiated html-vs-markdown, plus `?raw=1` for the whole blob); `DELETE /<id>` (unchanged,
  admin token); a legacy (non-`OPSX`) blob on any GET → `410`. The id regex accepts both 10-char
  (legacy) and 24-char ids so old entries still resolve to the 410 hint until they expire.
- **`bin/lib/sharelib.py`** (shrink) — delete the entire encryption section (`AESGCM` import,
  `HAVE_CRYPTO`, `CRYPTO_HINT`, `have_crypto`, `encrypt`, `decrypt`, `_b64u*`), `agent_fetch_url`, and
  the decrypt branch of markdown resolution. Keep the markdown→HTML renderer, `render_bundle`,
  `render_markdown_bundle`, `pack_bundle`/`unpack_bundle`, `parse_expires`, `data_uri`. `cryptography`
  leaves `requirements.txt` once nothing else imports it.
- **`bin/share/run.py`** (simplify publish) — drop `--plain` (plaintext is now the only mode), the
  `have_crypto` gate, `url_key`, `keynote`. Body is the OPSX blob directly. Print block becomes the
  one link plus the printed `.md` agents line plus revoke. `cmd_init` gains the publish-token setup
  (`secrets.token_urlsafe(24)`, `wrangler secret put PUBLISH_TOKEN`, write to `.share/config.json`).
- **`bin/share/cmd.json` + regenerated `ops.json`** — new `summary`/`usage` (no `--plain`), rewritten
  `hints` stating the trust model change explicitly.
- **Docs** — `docs/backup-and-share.md`, `docs/share-agent-markdown.md`, `bin/share/worker/README.md`,
  `docs/DECISIONS.md` (ADR-008), this proposal, `CHANGELOG.md`, and a Status update on the superseded
  proposal.
- **`test/run_backup_share.py`** — delete the Node Web-Crypto KAT block and encrypt/decrypt round-trip
  checks; update publish tests for the new print/ledger shape; add a Node worker-route test (stub KV,
  stub `env`) covering the publish-token gate, content negotiation, `.md`, legacy → 410, and the admin
  DELETE path.

## 6. Verification

1. **Offline suite:** `python3 test/run_backup_share.py` (`OPS_SHARE_FAKE=1`; the Node worker-route
   test needs only `node`).
2. **Grep gates:** no remaining references to `encrypt`, `HAVE_CRYPTO`, `X-Ops-Share-Key`, `?k=`,
   `agent_fetch_url`, `--plain` outside CHANGELOG/ADR/proposal history.
3. **Manual end-to-end** (human-gated, after `wrangler deploy`): publish → open in a browser (HTML);
   `curl <url>.md` and bare `curl <url>` both return the exact wiki markdown; paste `<url>.md` into a
   chat agent with a fetch tool and confirm it reads the note; `ops share pull <url>` matches; `ops
   share revoke <id> --yes` 404s both forms; `curl -X PUT <endpoint>` without `X-Publish-Token`
   returns `401` once the secret is set.
