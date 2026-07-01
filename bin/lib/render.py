"""
render.py — how a note looks when you read it in the terminal (Tier-1 ergonomics).

Zero-dependency baseline, auto-upgrading: if `glow` or `bat` is installed we hand the file to it;
otherwise a tiny built-in ANSI renderer makes Markdown legible (bold headings, dim frontmatter,
accented [[wikilinks]]). When stdout is NOT a TTY (piped, captured by a test, redirected to a file)
or OPS_RENDER=raw, we print the raw Markdown untouched — piping should always yield plain text.

  OPS_RENDER=raw   force raw Markdown (also the default when stdout is not a terminal)
  OPS_RENDER=plain force the built-in renderer (never shell out to glow/bat)
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ANSI
B, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
ACCENT = "\033[38;5;173m"   # muted terracotta — matches the docs palette
LINK = "\033[36m"
CODE = "\033[38;5;108m"

_H = re.compile(r"^(#{1,6})\s+(.*)$")
_LINK = re.compile(r"\[\[([^\]]+)\]\]")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ICODE = re.compile(r"`([^`]+)`")


def _tty() -> bool:
    return sys.stdout.isatty() and os.environ.get("OPS_RENDER") != "raw"


def render_markdown(text: str) -> str:
    """Minimal, dependency-free ANSI rendering of a Markdown note."""
    out, lines, i = [], text.splitlines(), 0
    # dim a leading YAML frontmatter block
    if lines and lines[0].strip() == "---":
        out.append(f"{DIM}---{RESET}")
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            out.append(f"{DIM}{lines[i]}{RESET}")
            i += 1
        if i < len(lines):
            out.append(f"{DIM}---{RESET}")
            i += 1
    fence = False
    for line in lines[i:]:
        if line.startswith("```"):
            fence = not fence
            out.append(f"{DIM}{line}{RESET}")
            continue
        if fence:
            out.append(f"{CODE}{line}{RESET}")
            continue
        m = _H.match(line)
        if m:
            level, txt = len(m.group(1)), m.group(2)
            style = f"{B}{ACCENT}" if level <= 2 else B
            out.append(f"{style}{txt}{RESET}")
            continue
        line = _LINK.sub(lambda x: f"{LINK}[[{x.group(1)}]]{RESET}", line)
        line = _BOLD.sub(lambda x: f"{B}{x.group(1)}{RESET}", line)
        line = _ICODE.sub(lambda x: f"{CODE}{x.group(1)}{RESET}", line)
        out.append(line)
    return "\n".join(out) + "\n"


def open_note(path: Path) -> None:
    """Show a note the best way available; raw Markdown when piped/redirected."""
    text = path.read_text(encoding="utf-8")
    if not _tty():
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        return
    if os.environ.get("OPS_RENDER") != "plain":
        if shutil.which("glow"):
            subprocess.run(["glow", "-p", str(path)]); return
        if shutil.which("bat"):
            subprocess.run(["bat", "--style=plain", "-l", "md", "--paging=auto", str(path)]); return
    sys.stdout.write(render_markdown(text))
