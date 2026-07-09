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

## `ops share` — zero-knowledge, confirm-gated

`ops share <slug>` / `share collection <tag>` renders the note(s) to a self-contained **OPSX**
bundle (raw wiki markdown + HTML) locally (inline CSS; wikilinks resolve only within the shared set —
others degrade to plain text; images under a size cap inline as data URIs), encrypts it AES-256-GCM
with a locally-generated key, and publishes only the **ciphertext** to a vendored Cloudflare Worker
+ KV (`bin/share/worker/`). The key travels in the URL `#fragment` (PrivateBin pattern) — the
provider can never read the note in the browser path. **Agent markdown:** `/<id>.md` serves the wiki
source UTF-8 (key via `X-Ops-Share-Key` or `?k=` — see `docs/share-agent-markdown.md`).

- `cryptography` is an auto-detected optional dep. Without it only `--plain` works; E2E prints the
  install hint.
- Publishing is a transmission, so every transmitting subaction self-gates `--yes` (EXIT_CONFIRM=3).
  `--dry-run` renders + encrypts locally and stops. The verb's output is a **draft link** — the
  human sends it.
- Expiry is native KV `expirationTtl`, 1:1 from `--expires` (e.g. `7d`). `share revoke <id>` issues a
  `DELETE` with the admin token recorded in `.share/ledger.json`. `share list` shows every share.
- `--gist` is a throwaway fallback (`gh gist create`, confirm-gated). `ops share init` deploys the
  worker (prints the exact `wrangler` commands; `--yes` runs them).
- `ops sweep` warns on expired shares and on notes edited since they were shared.

See `bin/share/worker/README.md` for the worker API and deploy steps.
