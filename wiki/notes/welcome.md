---
type: note
title: Welcome to your ~/ops
status: active
created: 2026-06-29
updated: 2026-06-29
tags: [meta, starter]
aliases: [welcome, getting-started]
---
# Welcome to your ~/ops

This is an example note — a real one, so search, links, and backlinks work out of the box. Read it,
then delete it (or keep it). Everything here is a Markdown file you own.

A note is just frontmatter + Markdown. The system put it in the right place with a unique slug; the
content is yours to write. Link other notes with double brackets — they become a graph you can walk.

## Start here
- [[the-ops-loop]] — how a thought becomes durable knowledge (capture → triage → task/note).
- [[risk-classes]] — why it's safe to let an agent drive this.
- [[conventions]] — the shape every note follows.

## Try it
```sh
ops index                      # build the search index over these notes
ops search "capture triage"    # find this loop note
ops wiki backlinks risk-classes  # see what links to a note
ops capture "my first real thought"   # then: ops triage
```
