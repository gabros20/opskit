"""
wiki.py — parse a fixture wiki and check the §10 conventions.

Models the rules an `ops wiki`/`ops doctor`/`ops consolidate` pass would enforce:
  - every note has YAML frontmatter with the required keys,
  - `type` is in the allowed taxonomy,
  - every [[wikilink]] resolves to an existing note (broken links are findings),
  - backlinks are derivable deterministically (the auto-backlink index),
  - orphans = valid notes with no inbound AND no outbound links,
  - stale = notes whose `updated` is older than the threshold,
  - client/project hubs carry a two-zone `## Timeline` section (compiled-truth + timeline).

Wikilinks use bare slugs ([[designatives]]) resolved against each note key's basename — the
design's "stable, human-readable slug" filenames.
"""
from __future__ import annotations
import re
from datetime import date

ALLOWED_TYPES = {"client", "project", "area", "person", "tool", "note", "runbook",
                 "skill", "decision", "meeting", "research", "prediction"}
REQUIRED_KEYS = {"type", "title", "status", "created", "updated", "tags"}
HUB_TYPES = {"client", "project"}
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def parse_note(text: str) -> dict | None:
    """Return {frontmatter, body, links} or None if there is no frontmatter block."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_block = text[3:end].strip("\n")
    body = text[end + 4:]
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        fm[k] = v
    links = LINK_RE.findall(body) + LINK_RE.findall(fm_block)
    return {"frontmatter": fm, "body": body, "links": links}


def _basename(key: str) -> str:
    return key.split("/")[-1]


def check_wiki(corpus: dict) -> dict:
    notes = corpus["notes"]
    today = date.fromisoformat(corpus["today"])
    stale_days = corpus.get("stale_days", 365)

    parsed: dict[str, dict] = {}
    issues = {"missing_frontmatter": [], "missing_keys": [], "bad_type": [],
              "broken_links": [], "orphans": [], "stale": [], "hub_missing_timeline": []}

    for key, text in notes.items():
        p = parse_note(text)
        if p is None:
            issues["missing_frontmatter"].append(key)
            continue
        parsed[key] = p

    # basename -> key resolution map (only for notes that exist)
    base_to_key: dict[str, str] = {_basename(k): k for k in notes}

    # forward + inbound link graph (broken links counted as outbound attempts)
    outbound: dict[str, list[str]] = {}
    inbound: dict[str, set[str]] = {k: set() for k in notes}
    for key, p in parsed.items():
        outs = []
        for target in p["links"]:
            outs.append(target)
            tk = base_to_key.get(target)
            if tk is None:
                issues["broken_links"].append([key, target])
            else:
                inbound[tk].add(key)
        outbound[key] = outs

    for key, p in parsed.items():
        fm = p["frontmatter"]
        # required keys
        missing = REQUIRED_KEYS - set(fm.keys())
        if missing:
            issues["missing_keys"].append(key)
        # type taxonomy
        if fm.get("type") and fm["type"] not in ALLOWED_TYPES:
            issues["bad_type"].append(key)
        # orphan: no inbound AND no outbound
        if not inbound[key] and not outbound.get(key):
            issues["orphans"].append(key)
        # stale
        upd = fm.get("updated")
        if isinstance(upd, str) and re.match(r"\d{4}-\d{2}-\d{2}", upd):
            if (today - date.fromisoformat(upd)).days > stale_days:
                issues["stale"].append(key)
        # hub two-zone structure
        if fm.get("type") in HUB_TYPES and "## Timeline" not in p["body"]:
            issues["hub_missing_timeline"].append(key)

    backlinks = {k: sorted(v) for k, v in inbound.items()}
    return {"issues": issues, "backlinks": backlinks, "parsed": list(parsed.keys())}
