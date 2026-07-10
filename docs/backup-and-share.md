# Backup & share — the durability floor and the sharing surface

Two verbs give ops its durability and its reach: `ops backup` (Part 5.1) makes the system
trustworthy; `ops share` (Part 5.2) makes it delightful. Backup comes first — `~/files` is the one
root where loss is physically irreversible.

## `ops backup` — the restic family

Bare `ops backup` is unchanged: a read-only nag that verifies `~/ops` is committed + pushed and
exits 1 if at risk. It never transmits. The subcommands add a real durability floor. restic is
auto-detected (`shutil.which`); every restic path degrades with an install hint when it is absent.

| Subcommand | Class | What it does |
|---|---|---|
| `backup init` | confirm (`--yes`) | Human-run once. Writes `.backup/config.json` with the local external-SSD repo + B2 bucket as **`op://` references** (never resolved), renders `com.ops.backup.cloud.plist`, and prints the `cp` / `launchctl load` lines. It never installs a launch agent for you. |
| `backup status` | read | Snapshot age per target; exit 1 if any target is stale over 48h, unconfigured, or unverifiable. Works without restic. |
| `backup run [--target local\|cloud]` | safe_write; **cloud is confirm** | `restic backup` of `~/files`, `~/dotfiles`, and the working trees of `~/ops` + `~/work`, then `restic check`. |
| `backup drill` | confirm (`--yes`) | Restore the latest snapshot to a temp dir and diff. A backup that has never been restored is a hypothesis. |
| `backup bundle` | safe_write | Rotated `git bundle --all` of `~/ops` + every `~/work` repo into `~/files/backups/bundles/` (keep last N, `OPS_BUNDLE_KEEP`). Closes the "remote-less repo has one copy in the world" hole; captured by restic. |

### The append-only cloud push runs OUTSIDE the verb surface

The scheduled cloud backup is **launchd invoking restic directly** with a dedicated append-only
(no-delete / no-prune) B2 key, resolved at runtime from `op://` via `op read`. This resolves the
never-transmit tension honestly: the human consents once at `init --yes`; thereafter it is machine
infrastructure like Time Machine, and even a fully compromised laptop or agent can only ADD to
history, never erase it. Pruning is manual only, with a separate privileged key. The rendered plist
carries exactly this command; `ops` itself never performs the cloud push.

`.backup/config.json` and the rendered plist are user-owned (per-vault) and are not in
`script/engine.txt`.

## `ops share` — capability URL, confirm-gated

`ops share <slug>` / `share collection <tag>` renders the note(s) to a self-contained **OPSX**
bundle (raw wiki markdown + rendered HTML) locally — inline CSS; wikilinks resolve only within the
shared set, others degrade to plain text; images under a size cap inline as data URIs — and PUTs the
bundle **as plaintext** to a vendored Cloudflare Worker + KV (`bin/share/worker/`) under a 24-char
unguessable token (`[a-z0-9]{24}`, ~124 bits). That token IS the secret; there is no encryption and
no key to lose.

**One link, two ways to read it:**

| You open | You get |
|---|---|
| `https://<worker>/<token>` in a browser | the rendered HTML page |
| `https://<worker>/<token>.md` | raw wiki markdown, `text/markdown` — paste into any chat/coding agent with a fetch tool |
| `https://<worker>/<token>` from `curl`/`web_fetch` (non-browser `Accept`) | raw markdown too — content negotiation serves the same thing the `.md` suffix does |

There is no second "agent URL" to construct and no header to set — append `.md` (or hand the printed
`agents / LLMs:` line straight to the agent) and it reads the exact wiki source. See
`docs/share-agent-markdown.md`.

- Publishing is still a transmission, so every transmitting subaction self-gates `--yes`
  (EXIT_CONFIRM=3). `--dry-run` renders locally and stops before the PUT. The verb's output is a
  **draft link** — the human sends it.
- `PUT /` requires a matching `X-Publish-Token` header when the `PUBLISH_TOKEN` wrangler secret is
  set (`ops share init` provisions it), so a discovered endpoint can't be abused as a free file host.
- Expiry is native KV `expirationTtl`, 1:1 from `--expires` (e.g. `7d`). `share revoke <id>` issues a
  `DELETE` with the admin token recorded in `.share/ledger.json`. `share list` shows every share.
  Links published under the previous encrypted model return **410** on every route — re-publish.
- `--gist` is a throwaway fallback (`gh gist create`, confirm-gated) — same trust model as this
  capability-URL scheme, just hosted by GitHub instead of the vendored worker.
- `ops sweep` warns on expired shares and on notes edited since they were shared.

**Threat model — what changed, and why.** The worker (Cloudflare, an infrastructure provider we
already trust for DNS/edge) can technically read anything published through it — that's the
tradeoff, made explicit and accepted. The property given up is zero-knowledge: previously the
decryption key rode the URL `#fragment`, which HTTP never sends to a server, so the provider held
only ciphertext. That design cannot also satisfy the operator's actual requirement — one URL that a
browser renders AND a headless agent can fetch — because a `#fragment`-only key is, by construction,
never on the wire for a server-side fetch to use. Every variant that tried to bridge the two
(`?k=` query key, an `X-Ops-Share-Key` header, a second `agent_url`, client-side `ops share pull`
math) produced either a two-link contract or a "install something first" step, both rejected on
ergonomics. Once the key has to be visible to the server for *any* agent-fetchable route to work, ZK
buys nothing over a plain unguessable token — so we drop it and get the one-link contract for free.
The remaining exposure (secrecy = link + TTL, holder-of-URL can read) is exactly the trust model
already accepted for `--gist`: a secret gist. Full writeup, alternatives tried, and the URL-pattern
decision: `docs/design/proposals/2026-07-10-capability-url-share.md`; ADR: `docs/DECISIONS.md`
(ADR-008).

See `bin/share/worker/README.md` for the worker API and deploy steps.
