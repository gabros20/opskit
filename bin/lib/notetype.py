"""
notetype.py — data-driven note types (§10.1, issue #1 gap D). The type→folder registry and the
per-type body templates live as DATA under templates/wiki/ (types.json + <type>.md), so adding a
note type is config, not code — `plainkeep wiki new <type>`, completion, and `plainkeep bookmark` all read from
here. A built-in fallback (below) mirrors the shipped data, so a bare/temp vault still works even
before templates/wiki/ exists; types.json overrides/extends it.

Template placeholders: {{type}} {{title}} {{status}} {{created}} {{updated}} {{slug}} {{body}} {{url}}
Unfilled placeholders are dropped, so a template can reference a var a caller doesn't supply.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

from . import paths  # type: ignore  # (namespace sibling)

TDIR = paths.PLAINKEEP_HOME / "templates" / "wiki"

# Built-in fallback (kept in sync with templates/wiki/types.json — the JSON overrides this).
DEFAULT_TYPES = {
    "note": {"dir": "notes"}, "decision": {"dir": "notes"}, "meeting": {"dir": "notes"},
    "research": {"dir": "research"}, "prediction": {"dir": "predictions"},
    "runbook": {"dir": "runbooks"}, "skill": {"dir": "skills"}, "tool": {"dir": "tools"},
    "person": {"dir": "people"}, "client": {"dir": "clients", "hub": True},
    "project": {"dir": "projects", "hub": True}, "area": {"dir": "areas", "hub": True},
    "bookmark": {"dir": "bookmarks"},
}
_DEFAULT_TMPL = ("---\ntype: {{type}}\ntitle: {{title}}\nstatus: {{status}}\n"
                 "created: {{created}}\nupdated: {{updated}}\ntags: []\naliases: []\n---\n"
                 "# {{title}}\n\n{{body}}\n")
_HUB_TMPL = ("---\ntype: {{type}}\ntitle: {{title}}\nstatus: {{status}}\n"
             "created: {{created}}\nupdated: {{updated}}\ntags: []\naliases: []\n---\n"
             "# {{title}}\n\n{{body}}\n## Timeline\n- {{created}} created\n")
_BOOKMARK_TMPL = ("---\ntype: bookmark\ntitle: {{title}}\nstatus: {{status}}\nurl: {{url}}\n"
                  "source: {{url}}\ncreated: {{created}}\nupdated: {{updated}}\ntags: []\naliases: []\n---\n"
                  "# {{title}}\n\n{{url}}\n\n{{body}}\n")
# built-in body templates for types whose shape differs from the generic default (used when no
# templates/wiki/<type>.md exists — e.g. a bare/temp vault). templates/wiki/ overrides these.
_BUILTIN = {"bookmark": _BOOKMARK_TMPL}
_PH = re.compile(r"\{\{(\w+)\}\}")


def load_types() -> dict:
    """The type registry: built-in defaults, overlaid with templates/wiki/types.json if present."""
    types = {k: dict(v) for k, v in DEFAULT_TYPES.items()}
    f = TDIR / "types.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for k, v in data.items():
                if not k.startswith("_") and isinstance(v, dict):
                    types[k] = v
        except Exception:
            pass
    return types


def is_type(typ: str) -> bool:
    return typ in load_types()


def type_dir(typ: str) -> str:
    return (load_types().get(typ) or {}).get("dir", "notes")


def is_hub(typ: str) -> bool:
    return bool((load_types().get(typ) or {}).get("hub"))


def _template_text(typ: str) -> str:
    """Body template for a type: templates/wiki/<type>.md, else _hub.md/_default.md, else built-in."""
    for name in (f"{typ}.md", "_hub.md" if is_hub(typ) else "_default.md"):
        p = TDIR / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    if typ in _BUILTIN:
        return _BUILTIN[typ]
    return _HUB_TMPL if is_hub(typ) else _DEFAULT_TMPL


def render(typ: str, *, title: str, status: str = "active", body: str = "",
           created: str | None = None, url: str = "", slug: str = "") -> str:
    """Render a note of `typ` from its template. created/updated default to today."""
    day = created or paths.today()
    vals = {"type": typ, "title": title, "status": status, "body": body,
            "created": day, "updated": day, "url": url, "slug": slug}
    return _PH.sub(lambda m: str(vals.get(m.group(1), "")), _template_text(typ))
