# Proposal — zero-config agent markdown URLs for ops share

**Status:** PROPOSED (2026-07-10)  
**Author:** Hermes (vault operator request) + design pass for personal-operating-system  
**Related:** `docs/share-agent-markdown.md`, `wiki/research/ops-share-architecture.md` (vault), Part 5.2 share worker

---

## 1. Problem

Operators publish a **human** link:

```text
https://<worker>/<id>#<key>
```

Coding agents (Claude Code, Hermes, Cursor, raw `curl`) need the **same wiki markdown** that was encrypted into the share, with **no extra setup** — no custom headers, no separate “agent API key” story.

**User intent (verbatim):** append `.md` or use `/md` on the share URL and get markdown. **Not** “configure `X-Ops-Share-Key`.”

**What shipped today:** `GET /<id>.md` returns UTF-8 wiki source from the OPSX bundle, but **encrypted** shares require the AES key on the wire via:

- header `X-Ops-Share-Key`, or
- query `?k=<key>`

That is correct cryptographically but **fails the ergonomics bar** the operator stated.

---

## 2. Why “just add `.md` to the human URL” is not enough (E2E)

| Piece | Sent to origin on `GET`? |
|-------|---------------------------|
| Path `/abc123xyz` | Yes |
| Query `?foo=bar` | Yes |
| Fragment `#secretKey` | **No** (browser / RFC 9110 — fragment is for the user agent only) |

The human viewer **decrypts in the browser** using `#key`. The worker never sees the key.  
A server-side `GET /<id>.md` **must** receive the key in **path or query** (or header) so the Worker can AES-GCM decrypt before returning markdown.

**Implication:** Zero-config cannot mean “literally only change `.md`” on the same URL string **unless** we **relocate** the key from fragment to a visible part of the URL for the agent link (query or path). The human link can stay fragment-based.

---

## 3. URL pattern comparison

Assume `<id>` = 10-char `[a-z0-9]`, `<key>` = base64url AES key (no `#`).

| Pattern | Example | Agent ergonomics | Header needed? | Log / referrer risk | Notes |
|---------|---------|------------------|----------------|---------------------|-------|
| **A. Suffix `.md` + query** | `/<id>.md?k=<key>` | **One paste** from CLI | No | `k` in access logs, Referer | **Recommended primary** |
| **B. Path `/md` + query** | `/<id>/md?k=<key>` | One paste; reads like “route” | No | Same as A | Slightly more REST-y; extra route in worker |
| **C. Suffix `.md` only** | `/<id>.md` | Perfect if E2E | No | Low | **401** on encrypted shares (current) |
| **D. Path key** | `/<id>/<key>.md` or `/<id>/<key>/md` | One paste; ugly long URL | No | **High** — key in path logs | Avoid |
| **E. Header only** | `/<id>.md` + `X-Ops-Share-Key` | Bad for generic agents | **Yes** | Low | Current “preferred” in docs — **deprecate for operators** |
| **F. Plain share** | `/<id>.md` | Perfect | No | Low | No key; secrecy = id + TTL |

**`.md` vs `/md`**

| | `/<id>.md` | `/<id>/md` |
|---|------------|------------|
| Familiarity | Looks like a **file**; tools default to “fetch this document” | Looks like a **sub-resource** |
| Routing | Suffix parse: strip `.md`, remainder is id | Extra path segment; must not collide with id charset |
| CDN / caches | Treat as distinct object from `/<id>` | Same |
| Collision | Ids have no dots today | Safe |

**Recommendation:** Keep **`/<id>.md`** as the canonical agent resource. Add **`/<id>/md`** as an **alias** (same handler) for operators who prefer path style. Both accept the **same** query key (see §4).

---

## 4. Recommended contract (zero-config for agents)

### 4.1 Two links at publish time (unchanged human, explicit agent)

| Audience | URL | Key location |
|----------|-----|--------------|
| Human | `https://<worker>/<id>#<key>` | Fragment (ZK for HTML viewer) |
| Agent | `https://<worker>/<id>.md?k=<key>` | Query (required for E2E server decrypt) |

`ops share … --yes` prints **both** on two lines:

```text
share:  https://<worker>/<id>#<key>
agent:  https://<worker>/<id>.md?k=<key>
```

Operator copies **one line** for agents — **no headers**.

### 4.2 Optional convenience transforms (documentation + CLI helper)

Document a mechanical rule agents can apply if the operator only has the human link:

```text
human:  https://<worker>/<id>#<key>
agent:  https://<worker>/<id>.md?k=<key>
```

Steps: split on `#` → base + key; insert `.md` before `?` or after id; set `?k=<key>`.

Future verb: `ops share agent-url <slug-or-url>` prints the agent line from ledger or from pasted human URL (no network).

### 4.3 Security note on `?k=`

Query keys may appear in Worker analytics, corporate proxies, and browser history if someone opens the agent URL in a GUI browser. Tradeoff is **accepted** for agent ergonomics; document alongside header option for paranoid environments.

**Plain shares:** `https://<worker>/<id>.md` with **no** `k` — unchanged.

---

## 5. Worker changes (high level)

1. **Routing**
   - `GET /<id>.md` — existing.
   - `GET /<id>/md` — alias to same handler (normalize id, reject malformed).

2. **Key resolution order** (encrypted blob)
   1. Query `k` (and alias `key` for compatibility)
   2. Header `X-Ops-Share-Key` (keep for backward compat)
   3. Else **401** JSON hint: *use `/<id>.md?k=` from `ops share` agent line*

3. **Do not** read fragment (impossible on server anyway).

4. **OPSX / legacy** behavior unchanged.

---

## 6. CLI / sharelib changes (high level)

- After publish, print `agent:` URL with `?k=` embedded (same key material as `#fragment`).
- Update `docs/share-agent-markdown.md` to list **query URL as primary**, header as optional.
- Stamp optional frontmatter field `share_agent:` (or second line in `share:` block) — **vault convention**, not required in engine.

---

## 7. Migration & backward compatibility

| Case | Behavior |
|------|----------|
| Existing clients using header | Keep working |
| Existing docs saying “preferred header” | Deprecate wording; no break |
| Old shares (HTML-only blob) | `415` on `.md` until re-share |
| Human `#` links | Unchanged |

No KV format change.

---

## 8. What we explicitly reject

- **Server-side `#key`** — impossible.
- **Only** `/<id>.md` with no key on encrypted shares — returns 401 forever (unless we break ZK and store key server-side — **no**).
- **Requiring** custom headers for default agent fetch — rejected per operator.

---

## 9. Open questions

1. Should `ops share` default expiry print agent URL in Telegram-safe plain text (key visible) — same as human link today?
2. Rate-limit `?k=` brute force separately from id guessing?
3. Should Hermes `browse_page` / `web_extract` auto-detect human share URLs and rewrite to `?k=` agent form when user asks for markdown?
4. Collection shares: one `agent` URL returns concatenated md — is `?k=` still one line? **Yes.**

---

## 10. Implementation checklist (when ACCEPTED)

- [ ] Worker: `/<id>/md` alias; document `key` query alias
- [ ] `bin/share/run.py`: print `agent:` line with `?k=`
- [ ] `docs/share-agent-markdown.md`: primary = query URL
- [ ] Tests: fake worker handler or unit tests for URL builder
- [ ] Vault wiki architecture §4.3 update

**Effort:** S (worker routes + CLI strings + docs); **no** bundle format change.

---

## 11. Research — how others solve “human link” vs “agent fetch” (2026-07-10)

### 11.1 Zero-knowledge pastebins (PrivateBin, ZeroBin, PasteRef, textdrop.sh)

**Pattern:** ciphertext on server; **decryption key only in `#fragment`**. Browsers never send `#` to origin (MDN URI fragment; RFC 3986).

**Agent story:** There is **no** standard “append `.md`” server route. Programmatic access is either:

- **Browser-only:** fetch ciphertext `GET /?pasteid=…`, decrypt in JS with key from `location.hash` (same as human).
- **API wrappers** (e.g. PrivateBinAPI): client holds key; not “one URL = markdown.”

**Lesson for ops:** Human ZK **requires** fragment. Any **server-returned plaintext** (our `/<id>.md`) **cannot** use fragment-only keys — industry accepts that split.

### 11.2 Firefox Send / MEGA-style file links (historical pattern)

Key in fragment; server stores encrypted blob. **No** first-class “curl this markdown” URL without moving the secret to query/path or decrypting client-side.

### 11.3 Jina Reader (`r.jina.ai/<url>`)

**Different problem:** public HTML → cleaned markdown. Prefix URL; no E2E. **Not comparable** to encrypted shares (they fetch what the server can already see).

**Relevant UX idea:** **one mechanical transform** on a URL string (prefix/suffix) — operators love that. Our analog: **human link → agent link** as a **published second line**, not mental crypto.

### 11.4 Bitwarden Send / 1Password secure share

Often **separate retrieval tokens** or **authenticated API** — convenience trades away pure “link-only ZK” for machine consumers.

### 11.5 Realistic convenience tiers (ranked)

| Tier | Operator gives agent | ZK vs server | Fits ops today? |
|------|----------------------|--------------|-----------------|
| **A** | Human link only | ZK if **local** `ops share pull '<url>'` decrypts | **Best UX; not built** |
| **B** | One URL `/<id>.md?k=` from CLI | Key in query (logged) | **Proposed default** |
| **C** | `/<id>.md` + header | Key off URL | Shipped; rejected by operator |
| **D** | `/<id>.md` only | N/A for E2E | Impossible without server key |
| **E** | `--plain` `/<id>.md` | No E2E | Works; weaker secrecy |
| **F** | Proxy `GET /open?u=<encoded human URL>` | Key inside `u` | One paste; ugly; same log risk |
| **G** | Client-side agent page | Fetch blob + `#key` in headless browser | Heavy; fragile |

**No surveyed system** offers **encrypted server-side markdown** with **only** `path + .md` and **fragment key** — that combination is **logically inconsistent** (fragment not on wire).

### 11.6 Recommendation after research

1. **Stop positioning headers** as the happy path.
2. **Ship Tier B** (`agent:` line at publish) — matches “one string to paste.”
3. **Ship Tier A** (`ops share pull` / MCP) so operator can **always paste the human link**; tool parses `#` and talks to worker — **true** “I only have the browser URL.”
4. Optional **Tier F** only if query strings feel ugly; security equivalent to `?k=`.

### 11.7 References (web)

- MDN: URI fragment not sent on request  
- PrivateBin: key in URL fragment  
- Jina Reader: `r.jina.ai` URL prefix pattern  
- OWASP / common guidance: secrets in query strings logged (accepted tradeoff for agent tier)

---

## Executive summary

1. **You cannot** serve E2E markdown with **only** `/<id>.md` and the human `#key` — HTTP never sends the fragment to the server.  
2. **Zero-config for agents** means a **single full URL** with `?k=<key>`, not headers.  
3. **Canonical:** `https://<worker>/<id>.md?k=<key>`; **alias:** `/<id>/md?k=<key>`.  
4. Human link stays `/#key` for browser ZK; CLI prints a separate **agent** line at publish.  
5. Headers remain supported but are **not** the operator-facing default.  
6. **Research:** No E2E product offers server markdown with fragment-only key; **human link + local pull** or **`?k=` agent URL** are the realistic max-convenience options.