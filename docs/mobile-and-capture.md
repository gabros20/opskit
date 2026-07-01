# Mobile & capture — the documented (not-an-app) surface

**Mobile-lite is documentation, not code** (proposal Part 3.4). ops has no server, no daemon, no
account. The vault is plaintext + git; the ONLY sync transport is `git push`/`pull` over your own
private remote. Everything below rides on that one fact. Nothing here bypasses the `ops` dispatcher
or the guardrail.

The golden rule, restated: **URIs and share-sheets OPEN and CAPTURE; all writes still go through a
verb.** Capture drops a file into `inbox/`; you `ops triage` it later on a real machine. Nothing on
mobile edits the wiki or tasks directly.

---

## 1. Desktop global-hotkey capture — Apple Shortcut → `ops capture`

The fastest capture path on macOS: an [Apple Shortcut](https://support.apple.com/guide/shortcuts-mac/welcome/mac)
bound to a global hotkey or the share sheet.

1. Shortcuts.app → **＋** → name it *Ops Capture*.
2. Add **Receive Text** as input (also tick *Show in Share Sheet* so it accepts selected text /
   URLs from any app).
3. Add **Run Shell Script**:
   - Shell: `/bin/zsh`  (or bash)
   - Pass input: **as arguments**
   - Script:
     ```bash
     export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
     OPS="$(command -v ops || echo "$HOME/ops/ops")"
     "$OPS" capture "$*"
     ```
4. Assign a keyboard shortcut in *Shortcuts → Settings → keyboard*, or invoke it from Raycast /
   the share sheet.

Because it shells to `ops capture`, the guardrail and `.logs/` apply — the Shortcut is just another
unprivileged caller. Pair it with the Raycast **Ops Capture** command
([`frontends/raycast`](../frontends/raycast/README.md)) for a Spotlight-style capture box.

---

## 2. iOS capture — a Shortcut that appends into `inbox/`

On iPhone/iPad there is no shell, so the Shortcut writes a file into the vault and **git carries it
home**. Two workable shapes:

### 2a. Working Copy (recommended — real git on iOS)
[Working Copy](https://workingcopy.app) clones your private `~/ops` remote on-device and exposes a
*Write File* / *Append* Shortcut action.

1. Clone the ops remote into Working Copy once.
2. Shortcut *Ops Capture* → **Receive Text/URL from Share Sheet** → **Text** (timestamp + body) →
   Working Copy **Write File** into `inbox/cap-<timestamp>.md` (append or new file).
3. End the Shortcut with Working Copy **Commit** + **Push**.
4. Next time you're at a machine: `git pull` then `ops triage`.

Keep the file shape trivial so triage handles it — a plain markdown file with your text is enough;
`ops triage` classifies and routes it.

### 2b. a-Shell / iSH (a POSIX shell on iOS)
If you run [a-Shell](https://holzschu.github.io/a-Shell_iOS/) you can `git clone` the remote and run
a cut-down capture (write to `inbox/`, `git commit`, `git push`). Heavier to set up; Working Copy is
the lower-friction path for most.

> Never point iCloud/Dropbox/Syncthing at the `.git` directory to "sync" the vault — see
> anti-roadmap #9 and `ops doctor` (it fails if `~/ops` resolves under a sync-wall). git push/pull is
> the transport; a file-sync tool corrupts the repo.

---

## 3. Read & edit on mobile — Obsidian mobile or GitJournal

The vault is Obsidian-compatible (see [`docs/obsidian-compat.md`](obsidian-compat.md)); on mobile you
rent an existing app rather than building one.

- **Obsidian mobile** over a git remote: use the
  [Obsidian Git](https://github.com/Vinzent03/obsidian-git) plugin (or Working Copy's repository as
  the vault folder on iOS via the Files provider) to pull/commit/push. Native wikilinks, backlinks,
  graph, and Properties — the same notes you edit on desktop.
- **[GitJournal](https://gitjournal.io)**: a git-native notes app that speaks markdown frontmatter
  and `[[wikilinks]]` directly, cloning your private remote. Lighter than Obsidian for pure
  capture/edit.

Either way the sync is **git over your private remote via Working Copy / the app's own git**. Edits
you make on mobile land as commits; you pull them on desktop. Re-index after pulling:
`ops index --changed` picks up externally-edited notes (it never rewrites your files).

---

## 4. The one sync transport

```
 phone (Working Copy / Obsidian Git / GitJournal)
        │  git push / pull
        ▼
 private remote (your own git host — GitHub private repo, a self-hosted bare repo, …)
        ▲
        │  git push / pull
 desktop (~/ops, the ops verbs, the index)
```

No provider ever sees plaintext beyond your chosen git host, and no piece here transmits on its own:
you push, you pull. Capture is additive (`inbox/`), triage is deliberate, and the guardrail sits on
every write on the desktop side.
