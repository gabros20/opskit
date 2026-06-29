---
name: Feature / verb proposal
about: Propose a new verb or capability
title: "[idea] "
labels: enhancement
---

**The need**
What workflow is awkward or missing today?

**Proposed shape**
If it's a verb, sketch the surface (stay flat — one verb, shallow subactions):
```sh
ops <verb> <action> ...
```

**Which root(s) does it touch?**
`~/ops` / `~/work` / `~/files` — and what risk class (`read` / `safe_write` / `draft_only` / `confirm`)?

**Why a verb and not a one-off script?**
(See the "no verb sprawl" rule in the design §4.)
