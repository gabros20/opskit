# ops share worker

A tiny Cloudflare Worker + KV store implementing zero-knowledge, expiring shares for `ops share`
(proposal Part 5.2). It stores an **opaque blob** (AES-256-GCM ciphertext, or `--plain` HTML) and
never sees the key — the key travels in the URL `#fragment` and is decrypted in the browser
(PrivateBin pattern). Modeled on SharzyL/pastebin-worker.

## API

| Method | Path         | Headers            | Body | Returns |
|--------|--------------|--------------------|------|---------|
| `PUT`  | `/`          | `X-Expire-Seconds` | blob | `{ id, admin_token }` |
| `GET`  | `/<id>`      | `Accept: text/html` (browser) | — | the **viewer** page (decrypts client-side) |
| `GET`  | `/<id>?raw=1` | —                 | —    | the raw stored blob (what the viewer fetches) |
| `GET`  | `/<id>.md`   | `X-Ops-Share-Key` or `?k=` (E2E) | — | **UTF-8 wiki markdown** for agents (OPSX v1, 1:1 source) |
| `GET`  | `/<id>`      | any other `Accept` (curl) | — | the raw stored blob |
| `DELETE` | `/<id>`    | `X-Admin-Token`    | —    | `204` (admin only) |

**The viewer.** A browser opening `/<id>#<key>` gets a small self-contained page that fetches the
raw ciphertext (`?raw=1`) and decrypts it in-page with Web Crypto using the key from the URL
`#fragment` — byte-compatible with `bin/lib/sharelib.py` (`nonce[12] ‖ ct ‖ tag[16]`, base64url).
The decrypted note renders inside a **scriptless sandboxed iframe** (it can never read the key).
`--plain` shares (no `#fragment`) render their HTML directly. Without the viewer the browser would
just download opaque ciphertext.

**Agent markdown.** Publish bundles **OPSX** (raw wiki markdown + HTML). Fetch `/<id>.md` for the
**exact wiki source** (single note) or collection join. Pass the key via `X-Ops-Share-Key` or `?k=`.
See `docs/share-agent-markdown.md`.

Expiry is native KV `expirationTtl` (1:1 from `--expires`, so there is no cleanup code). Revoke is a
`DELETE` with the `admin_token` returned at publish time and recorded in `.share/ledger.json`.

## Deploy (once)

`wrangler.toml` is **per-vault** (gitignored). The engine ships `wrangler.toml.example` only — `script/update` never overwrites your KV namespace id.

```sh
cd bin/share/worker
cp wrangler.toml.example wrangler.toml
wrangler kv namespace create OPS_SHARE     # paste the id into wrangler.toml
wrangler deploy
ops share init --endpoint https://ops-share.<subdomain>.workers.dev
```

Free tier: 100k requests/day, 1k KV writes/day — a collection coalesces into ONE KV entry.

## Security notes

- The worker is untrusted infrastructure: it only ever holds ciphertext. Losing the URL `#fragment`
  means the note is unrecoverable — that is the point.
- `ops share` publishes only; it is confirm-class (`--yes`) because a PUT is a transmission. The
  human sends the resulting link.
- The worker is vendored inside the engine boundary (`bin/share/worker/`) so fixes distribute via
  `script/update`.
- Cloudflare bot-management **403s the default `Python-urllib/x.y` User-Agent** (a `PUT` that works
  from `curl` fails from stdlib `urllib` for this reason alone). `ops share` sends
  `User-Agent: ops-share/1.0` so the edge lets it through; keep that header if you customize the
  client. When forwarding a link (e.g. over Telegram), send it **whole** — the `#…` tail is the
  decryption key, and a truncated link cannot be opened.
