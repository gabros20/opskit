# ops share worker

A tiny Cloudflare Worker + KV store implementing zero-knowledge, expiring shares for `ops share`
(proposal Part 5.2). It stores an **opaque blob** (AES-256-GCM ciphertext, or `--plain` HTML) and
never sees the key — the key travels in the URL `#fragment` and is decrypted in the browser
(PrivateBin pattern). Modeled on SharzyL/pastebin-worker.

## API

| Method | Path    | Headers                | Body | Returns |
|--------|---------|------------------------|------|---------|
| `PUT`  | `/`     | `X-Expire-Seconds`     | blob | `{ id, admin_token }` |
| `GET`  | `/<id>` | —                      | —    | the stored blob |
| `DELETE` | `/<id>` | `X-Admin-Token`      | —    | `204` (admin only) |

Expiry is native KV `expirationTtl` (1:1 from `--expires`, so there is no cleanup code). Revoke is a
`DELETE` with the `admin_token` returned at publish time and recorded in `.share/ledger.json`.

## Deploy (once)

```sh
cd bin/share/worker
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
