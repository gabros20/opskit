# Docs — the map

Start with the project [README](../README.md) (what this is + install). Docs here follow
[Diátaxis](https://diataxis.fr): each file serves one purpose.

| Read this… | When you want… | Mode |
|---|---|---|
| [`how-it-works.html`](how-it-works.html) | the 2-minute interactive tour (open in a browser, no install) | Tutorial |
| [`architecture.md`](architecture.md) | to understand *why* the system is shaped this way — principles, enforcement path, trade-offs | Explanation |
| [`machine-contract.md`](machine-contract.md) | exact shapes: the `--json` envelope, exit codes, `ops.json` v2, `cmd.json` | Reference |
| [`plugins.md`](plugins.md) | to add your own verbs or install/trust a pack (SDK, `plugin.json`, trust model) | How-to + Reference |
| [`backup-and-share.md`](backup-and-share.md) | the restic backup family and the encrypted `ops share` surface | How-to |
| [`mobile-and-capture.md`](mobile-and-capture.md) | capture from phone/share-sheet; read the vault on mobile (git is the only sync) | How-to |
| [`obsidian-compat.md`](obsidian-compat.md) | the normative definition of "Obsidian-compatible" (what ops emits vs tolerates) | Reference |
| [`DECISIONS.md`](DECISIONS.md) | the ADR log — every load-bearing decision, with the why | Explanation (record) |
| [`../CHANGELOG.md`](../CHANGELOG.md) | what changed and when (newest first) | Reference (record) |
| [`design/PERSONAL_OS_DESIGN.md`](design/PERSONAL_OS_DESIGN.md) | the full v3 design spec (deep background; ADRs supersede where they conflict) | Explanation |
| [`design/proposals/`](design/proposals/) | accepted/active proposals — the v4 platform roadmap lives here | Explanation |

Operating manual (how to *drive* the system, for humans and agents alike):
[`skills/operate-ops/SKILL.md`](../skills/operate-ops/SKILL.md) — paired with the agent contract
[`AGENTS.md`](../AGENTS.md). Contributing to the engine: [`CONTRIBUTING.md`](../CONTRIBUTING.md).
