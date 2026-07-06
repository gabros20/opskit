# Changelog

Notable changes to the ops platform, newest first. Format follows
[Keep a Changelog](https://keepachangelog.com). The *why* behind load-bearing decisions lives in the
ADR log ([`docs/DECISIONS.md`](docs/DECISIONS.md)); this file records *what changed*.

## [Unreleased]

### Fixed
- **`ops share` end-to-end ([#2](https://github.com/gabros20/personal-operating-system/issues/2)).**
  Dogfooding the share surface on live Cloudflare Workers surfaced three defects, all fixed:
  - **Publish 403.** Stdlib `urllib`'s default `Python-urllib/x.y` User-Agent is blocked by
    Cloudflare bot-management (a `PUT` that works from `curl` failed from the client). The client now
    sends `User-Agent: ops-share/1.0` on every `PUT`/`DELETE` (`bin/share/run.py`).
  - **Encrypted link downloaded ciphertext instead of rendering.** The worker always returned
    `application/octet-stream`, and no in-browser viewer existed. The worker now serves a
    self-contained **decrypt viewer** on browser navigation (`Accept: text/html`): it fetches the raw
    blob (`?raw=1`) and decrypts in-page with Web Crypto using the key from the URL `#fragment`,
    then renders into a **scriptless sandboxed iframe** (the note can never read the key) and strips
    the `#fragment` from the address bar (`bin/share/worker/worker.js`). `--plain` shares render
    directly; `curl`/programmatic GETs still receive the raw blob.
  - **Silent failure on truncated links.** A forwarded link that lost its `#…` tail now shows a clear
    "this encrypted link is missing its key" message in the viewer, and `ops share` reminds you to
    send the full link (the `#…` is the decryption key).

### Changed
- **Shared-note reading experience redesigned** (`bin/lib/sharelib.py`). The recipient view was
  cramped and, worse, wide code lines blew out the page width — breaking the whole mobile layout so
  body text scrolled off-screen. The new self-contained stylesheet is a Flexoki-palette,
  kepano-minimal reading layout: system type scale, generous spacing, safe-area padding, automatic
  light/dark via `prefers-color-scheme` (pure CSS — the note renders in a scriptless sandboxed
  iframe), and **code blocks that scroll horizontally inside a bordered panel** instead of forcing
  the page wide. The Markdown renderer now also emits real **lists** (`-`/`*`/`+`, `1.`) and
  **blockquotes** (`>`) rather than dumping them as literal-prefixed paragraphs.
- The viewer no longer strips the `#key` fragment from the URL after decrypting. Doing so left the
  in-app browser (e.g. Telegram) on a keyless URL, so "Open in Safari" / reload / copy-link failed
  with "missing key". The key now stays in the fragment (the zero-knowledge model — fragments are
  never sent to the server), keeping the link reloadable and portable across browsers.
- **Mobile-browser hardening** for the share pages (`bin/share/worker/worker.js` viewer +
  `sharelib.py` bundle): `viewport-fit=cover`, per-scheme `theme-color`, `color-scheme`, and the
  iOS 26 "Liquid Glass" edge-strip + matching-background pattern so the iPhone status/URL bar blends
  with the note instead of showing a white/dark band; the viewer's iframe is pinned to the visual
  viewport (`position:fixed; inset:0`) to avoid the `100vh` address-bar jump; and note padding now
  respects `env(safe-area-inset-*)` so text clears the notch/home indicator.
- Documented the viewer, the `?raw=1` route, the content-negotiated `GET`, and the Cloudflare
  User-Agent gotcha in `bin/share/worker/README.md`.

### Added
- Committed known-answer crypto fixture (`test/fixtures/share_kat.json`) plus a **Node Web Crypto
  cross-check** in the share suite that pins byte-compatibility between `sharelib.py`'s AES-256-GCM
  output (`nonce ‖ ct ‖ tag`, base64url) and the browser viewer. Runs in CI — it needs only `node`,
  not the optional `cryptography` package.
- A real-transport **User-Agent assertion** in the share suite (a one-shot local HTTP server captures
  the actual `PUT` and checks the header), so the 403 fix can't silently regress.

---

History before this changelog is in `git log` and the ADR record ([`docs/DECISIONS.md`](docs/DECISIONS.md),
ADR-001 … ADR-007, which covers the v4 platform).
