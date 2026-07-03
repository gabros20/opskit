# Remote & mobile operations — driving ops from anywhere

**Status: PROPOSED (2026-07-03).** High-level design, not yet accepted.
Companion to the [v4 platform roadmap](2026-07-01-v4-platform-roadmap.md) (implemented, ADR-007).
Scope: how the system is *operated day-to-day* when the human is not sitting at the machine —
agent channels (Claude Code remote, a Telegram bridge), phone capture into `inbox/`, the
organize-aware week review, and the trust ramp for scheduled organize scans.

The design bet, stated up front: **v4 already built the hard part.** The machine contract,
guardrail, jobs registry, and MCP server mean every remote channel below is a *thin caller* of
`ops <verb>` — no channel gets its own write path, and the anti-roadmap (no daemon in ops, no
unattended transmit, git as the only sync) is preserved by construction, not by discipline.

---

## 0. The topology: where ops lives

```
                     ┌──────────────────────────────────────────────┐
                     │  ALWAYS-ON HOST (Mac Mini / dev box)          │
   phone ────────────┤  ~/ops  ~/files  ~/work                       │
   laptop ───────────┤  launchd jobs (index, consolidate, scan…)     │
   (channels below)  │  ops mcp · Claude Code · [telegram bridge]    │
                     └───────────────┬──────────────────────────────┘
                                     │ git push/pull (private remote)
                              phone-side git (Working Copy / Obsidian Git)
```

- **T1 — always-on host (the end state).** ~/ops lives on the Mini. Scheduled jobs actually run
  (a laptop that sleeps misses its 03:00 scan). Every remote channel terminates here. Reachability
  via **Tailscale** (or equivalent WireGuard mesh): no open ports, no public endpoint, the host is
  only visible to your own devices. This is the recommended deployment.
- **T2 — laptop-only, no agent.** Everything works locally today: terminal, Raycast, Obsidian.
  Mobile capture degrades to the async git path (§2.2) since the host isn't always reachable.
  Nothing in this proposal is *required* for T2; it's the fallback posture, not a design target.

One repo of truth either way. The phone never holds "the" vault — it holds a git clone or nothing.

## 1. Agent channels — three tiers, rent before build

Ordered by new code required. The recommendation is **start at C1+C2 (zero new code), build C3
only if chat proves to be the UX you actually reach for.**

### C1 — Claude Code remote (dispatch / remote sessions) — *rent, zero code*

The Mini runs Claude Code; you drive it from the phone via the Claude app / claude.ai/code
(dispatch, remote control). The session lands in `~/ops`, reads `CLAUDE.md → AGENTS.md → the
operate-ops skill`, and is thereby a fully-contracted operator: it knows the verbs, the risk
classes, and that it never invents a spelling.

- **UX:** open the Claude app → dispatch to the Mini → *"capture: call the accountant re Q2
  VAT"*, *"what needs my attention?"* (→ `ops orient`), *"triage the inbox"*, *"review the
  organize proposals and tell me which you'd accept"*. Multi-step work (triage → task add →
  start) happens in one conversation.
- **The confirm loop is the killer feature here:** a confirm-class verb exits `3` with the exact
  re-run; the agent relays "this needs your yes" into the chat; you reply in natural language;
  the agent re-runs with `--yes`. The human-consent gate survives the remote hop *because it's
  in the verb, not the client*.
- **Needs (setup, not code):** Mini enrolled in Claude Code remote; `~/ops` as the trusted
  project. Optionally register `ops mcp` in the host config so the tool surface is typed rather
  than shell-mediated — both routes converge on the dispatcher anyway.

### C2 — bare SSH over Tailscale — *rent, zero code, no agent*

For the "on my Mac without an agent" mode and as the transport under §2.1. iOS **Shortcuts** has
a native *Run Script Over SSH* action; Termius/Blink give you a real terminal. `ops orient
--line` was built for exactly this: one glanceable line over a dumb transport.

### C3 — Telegram bridge (Hermes-style) — *build, the only new surface*

A conversational always-available operator in the app you already have open. Design constraints
make this safe to even attempt:

- **It is a frontend, not part of ops.** It lives in `frontends/telegram/`, alongside Raycast in
  spirit: a small resident process **on the host**, outside the verb surface — exactly like
  launchd, which is already blessed as the thing that *invokes* ops on a schedule. The
  anti-roadmap's "no daemon" means *ops* never becomes a server; it does not forbid a caller
  from being long-lived. The bridge holds **no state** but a chat-session map; truth stays in
  the vault.
- **Long-polling, never webhooks.** The bridge polls Telegram's API outbound; no inbound port,
  no public URL, composable with the no-open-ports posture of T1.
- **Two modes, one chokepoint:**
  - *Command mode (v1):* messages map to a tiny allowlist — plain text → `ops capture`, `/o` →
    `ops orient --line`, `/s` → `ops status`, `/t` → task list. Deterministic, no model, ~200
    lines of stdlib Python. This alone answers "send content into the inbox from my phone."
  - *Agent mode (v2):* the bridge hands the message to a headless agent session (`claude -p`,
    or a Hermes-style loop against the API) with `cwd=~/ops`; the agent operates under the same
    AGENTS.md contract and MCP surface as C1. Exit-3 confirms surface as a chat question with
    an inline **[yes] [no]**; *yes* re-runs with `--yes`. The model proposes; the verb writes.
- **Trust model:** single allowlisted `chat_id` (hard-fail anything else); bot token as an
  `op://` reference resolved by the bridge's launchd env, never printed; every call goes through
  `ops <verb>` so `.logs/` sees it; replies to *you* in your own chat are not "transmission" in
  the AGENTS.md sense — the bridge must still never message anyone else, and draft-only verbs
  stay draft-only (it can *show* you an invoice draft, never send one).
- **Honest cost:** a resident process to babysit, a third-party message path (Telegram sees
  message plaintext — don't paste secrets), and a second agent runtime to keep updated. Hence:
  build only after C1/C2 have proven insufficient. If Telegram-the-transport is unacceptable,
  the same bridge shape works over Signal (signal-cli) or a self-hosted ntfy/Matrix.

## 2. Mobile capture, end-to-end

Two paths, complementary — one synchronous, one offline-capable. Both end in `inbox/` and both
were *almost* finished by v4; what's missing is one small verb and the recipes.

### 2.1 Online path: share sheet → SSH → `ops capture` (recommended primary)

```
 iPhone share sheet / hotkey
   └─ Shortcut "Ops Capture"
        └─ Run Script Over SSH (Tailscale, key auth)
             └─ ops capture "<text>"        ← guardrail, .logs/, journal — as if typed locally
```

One Shortcut, zero new code, works from any app's share sheet (text, URLs), and the capture is
*instantly* in the real inbox — no sync lag, no second clone. Failure mode: host unreachable →
Shortcut errors → you fall back to 2.2. A `bookmark` variant is the same recipe pointed at
`ops bookmark <url>`.

### 2.2 Offline path: Working Copy → git push → **`ops sync`** (the missing verb)

The documented Working Copy flow ([mobile-and-capture.md](../../mobile-and-capture.md)) writes
`inbox/cap-*.md` on-device and pushes. Today the file then **sits on the remote until a human
pulls** — capture round-trip is unbounded. The fix is one small engine verb:

- **`ops sync`** — `git pull --ff-only` on `~/ops` + `ops index --changed`. Risk: `safe_write`
  (fast-forward only: refuses on divergence with a teach-the-fix message; never merges, never
  rebases, never pushes). Schedulable: add `"sync": { "command": "ops sync", "schedule":
  { "interval_minutes": 15 } }` to the jobs registry. Phone-captured notes now appear in the
  live inbox within 15 minutes, and `orient`/`status` count them.
- **Push stays human.** AGENTS.md rule 3 names `push` as transmission, so the scheduled job is
  pull-only by design. `ops sync --push` exists but is **confirm-class** (`--yes`), for the
  human closing the loop so the phone sees desktop state. This asymmetry is deliberate: inbound
  is safe to automate, outbound never is.

### 2.3 Capture UX matrix (what to reach for when)

| Situation | Path | Latency to inbox |
|---|---|---|
| Phone, online, quick thought / shared URL | Shortcut → SSH → `capture`/`bookmark` (2.1) | instant |
| Phone, offline / host down | Working Copy push → `ops sync` job (2.2) | ≤ sync interval |
| Phone, conversational ("capture this, and also what's urgent?") | C1 dispatch or C3 bridge | instant |
| Mac, no agent | ⌥Space Raycast *Ops Capture* / hotkey Shortcut (already built) | instant |
| Voice, hands-free | iOS dictation into the 2.1 Shortcut (later: voice note → local whisper → capture, via C3) | instant |

## 3. `ops week` reads the organize ledger

The organize pipeline writes an append-only ledger (`inbox/organize/<date>.jsonl`, status lines,
latest-wins replay). `orient` already counts pending files; the week review should close the
loop — **the weekly ritual is where organize proposals get decided**, otherwise they rot.

- `ops week` gains an **Organize** section, computed by replaying the ledgers (read-only, same
  replay code `bin/organize/run.py` already has): ops proposed / accepted / rejected / deferred /
  applied this week; pending count with the oldest proposal's age; the exact next command
  (`ops organize review`) when pending > 0.
- Lands in the weekly journal note (existing write path) and in `--json` as
  `organize: {proposed, accepted, rejected, deferred, applied, pending, oldest_pending_days}`.
- Deliberately **not** interactive: week reports and points at `organize review`; it never
  accepts/rejects itself. One verb, one job.

Effort: small — a read-only fold over existing ledger replay + a render block + envelope fields
+ tests.

## 4. Scheduled organize scan — the trust ramp

The registry entry already exists (`organize_scan`, Sun 03:00, safe_write — it only writes
proposals to `inbox/organize/`). What's designed here is the **ramp**, because the failure mode
isn't technical, it's trust:

1. **Stage 0 (now):** manual `ops organize scan` when you feel entropy. Human-paced.
2. **Stage 1:** `ops job apply` + `launchctl load` → weekly scan runs on the host. Proposals
   accumulate; `orient` shows the count. *Nothing changes in the vault.*
3. **Stage 2 (with §3):** the week review digests the ledger — Sunday's scan meets Monday's
   review. Accept/reject in one sitting; `apply --yes` stays a typed human act.
4. **Never a stage 3.** Auto-apply is anti-roadmap (model-driven writes without review). If
   months of history show ~100% acceptance for some op type, the correct move is a *rule* in
   the scanner (deterministic), not auto-accepting model output.

The jobs registry's own rule enforces the ceiling: only read/safe_write may be scheduled, and
`doctor` checks it — `organize apply` (confirm) is structurally unschedulable.

## 5. What this deliberately does not add

No inbound ports or public webhook (Tailscale + long-poll only) · no capture app (Shortcuts +
Working Copy are rented) · no scheduled `git push` (pull-only automation; push is human) · no
second sync transport (git remains the only one; no CRDT, no file-sync) · no bridge-side state
or truth (chat map only) · no auto-applied organize ops, ever · no daemon *inside* ops — the
bridge and launchd are callers, the dispatcher stays the sole door.

## 6. Build order

| Pkg | What | New code | Depends on |
|---|---|---|---|
| R1 | Recipes: SSH-capture Shortcut, Tailscale setup, C1 dispatch walkthrough → extend `docs/mobile-and-capture.md` + new `docs/remote-operations.md` | none (docs) | Mini + Tailscale (human setup) |
| R2 | `ops sync` verb (pull-only, ff-only, `--push --yes` confirm) + registry entry + tests | small | — |
| R3 | `ops week` organize digest (§3) | small | — |
| R4 | Jobs live on the host: `ops job apply`, load plists, verify `.logs/jobs/` | none (ops + human) | T1 |
| R5 | *(optional, deferred)* `frontends/telegram/` bridge — command mode first, agent mode behind a flag | medium | R1–R4 proven insufficient |

R1–R4 are a weekend; R5 is the only real project, and the explicit recommendation is to live
with C1+C2 for a few weeks first — if you never miss the chat bridge, it never gets built.
