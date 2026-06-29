"""
agent.py — §6 agent indirection: the ONE swappable point where a verb borrows a model's judgment.

A verb calls run_agent(prompt, scope); whatever agent is configured via OPS_AGENT answers, or — if
none is set or it fails — the call returns None and the verb uses its deterministic shell fallback.
The verb never knows which agent (or none) ran: identical surface either way. This is how `ops triage`
/ `ops close` can be smarter WITH a model and still fully functional WITHOUT one.

Configure in your dotfiles:
    export OPS_AGENT="claude"        # or "codex", "grok", "ollama", or "none" (default)
    export OPS_AGENT_MODEL="gemma3:1b"   # for OPS_AGENT=ollama
    export OPS_AGENT_CMD="my-agent --print"   # escape hatch: any command; the prompt is appended
"""
import os
import shlex
import subprocess


def _agent() -> str:
    return (os.environ.get("OPS_AGENT", "none") or "none").strip().lower()


def available() -> bool:
    """True if some agent is configured (a verb can decide whether to even build a prompt)."""
    return bool(os.environ.get("OPS_AGENT_CMD")) or _agent() not in ("", "none")


def _command(prompt: str, scope: str):
    custom = os.environ.get("OPS_AGENT_CMD")
    if custom:                                  # escape hatch: any command, prompt appended as one arg
        return shlex.split(custom) + [prompt]
    a = _agent()
    if a == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        cmd += ["--allowedTools", "Read,Bash(ops search:*)" if scope == "read" else "Read,Write,Edit,Bash(ops:*)"]
        return cmd
    if a == "codex":
        return ["codex", "exec", prompt]
    if a == "grok":
        return ["grok", "-p", prompt]
    if a == "ollama":
        return ["ollama", "run", os.environ.get("OPS_AGENT_MODEL", "gemma3:1b"), prompt]
    return None                                 # unknown agent → no command → fallback


def run_agent(prompt: str, scope: str = "read", timeout: int = 60):
    """Return the agent's text output, or None to signal 'use your fallback'. Never raises."""
    cmd = _command(prompt, scope)
    if not cmd:
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "").strip()
        return out or None
    except Exception:
        return None
