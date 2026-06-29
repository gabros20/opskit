#!/usr/bin/env python3
"""
ops triage [--dry-run|--yes] — PROPOSE filing of inbox/ items into a task or a wiki note; the human
approves (§4.1, §10). Interactive by default; --dry-run shows proposals only; --yes accepts all.

Classification here is the deterministic pure-shell fallback (no agent required). When an agent is
wired (OPS_AGENT), it would improve the proposal — but the system works without it.
On an override (you pick differently than proposed), it offers to record a one-line rule in
wiki/conventions.md ## Filing rules — the plaintext learning loop.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import paths, filing, agent  # noqa: E402

# An item is a TASK when its first word is an imperative action verb (matched as a whole word,
# so "merges"/"writing" don't false-trigger), or it's an explicit todo/checkbox line.
ACTION_VERBS = {"fix", "call", "email", "send", "ask", "schedule", "review", "ping", "pay", "buy",
                "book", "draft", "update", "write", "check", "reply", "chase", "invoice", "deploy",
                "merge", "rename", "do", "make", "add", "remove", "create", "investigate", "prep",
                "prepare", "ship", "test", "refactor", "migrate", "follow"}


def parse_item(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    if t.startswith("---"):
        e = t.find("\n---", 3)
        if e != -1:
            t = t[e + 4:]
    return t.strip()


def classify(text: str) -> str:
    if not text.strip():
        return "note"
    # §6: if an agent is configured, borrow its judgment; otherwise fall through to the shell rule.
    if agent.available():
        ans = agent.run_agent(
            "Classify this captured item as exactly one word — 'task' (an action to do) or "
            f"'note' (a fact/idea to keep). Reply with only the word.\n\n{text}", scope="read")
        if ans:
            a = ans.strip().lower()
            if "task" in a and "note" not in a:
                return "task"
            if "note" in a and "task" not in a:
                return "note"
    first = text.splitlines()[0].lower()
    if first.startswith(("- [ ]", "todo", "[]")) or "follow up" in first:
        return "task"
    words = re.findall(r"[a-z]+", first)
    if words and words[0] in ACTION_VERBS:
        return "task"
    return "note"


def make_task(text: str) -> Path:
    title = text.splitlines()[0][:70] if text.strip() else "task"
    return filing.create_task(title, intent=text, source="triage")


def make_note(text: str) -> Path:
    return filing.create_note(text)


def record_rule(rule: str):
    conv = paths.WIKI / "conventions.md"
    if not conv.exists():
        return
    txt = conv.read_text(encoding="utf-8")
    if "## Filing rules" in txt:
        txt = txt.replace("## Filing rules", f"## Filing rules\n- {rule}", 1)
    else:
        txt += f"\n## Filing rules\n- {rule}\n"
    conv.write_text(txt, encoding="utf-8")


def items():
    if not paths.INBOX.exists():
        return []
    return sorted(p for p in paths.INBOX.iterdir() if p.suffix in (".md", ".txt") and p.name != ".gitkeep")


def main(argv):
    dry = "--dry-run" in argv
    yes = "--yes" in argv or "-y" in argv
    its = items()
    if not its:
        print("inbox is empty — nothing to triage.")
        return 0
    print(f"triage: {len(its)} item(s) in inbox/\n")
    for p in its:
        text = parse_item(p)
        kind = classify(text)
        title = (text.splitlines()[0] if text.strip() else p.stem)[:70]
        dest = "tasks/active/" if kind == "task" else f"wiki/notes/{paths.slugify(title)}.md"
        print(f"• {p.name}: \"{title}\"")
        print(f"    proposal: {kind.upper()} -> {dest}")
        if dry:
            continue
        choice = kind
        if not yes:
            ans = input("    [a]ccept / [t]ask / [n]ote / [s]kip ? ").strip().lower() or "a"
            choice = {"a": kind, "t": "task", "n": "note", "s": "skip"}.get(ans, kind)
        if choice == "skip":
            print("    skipped")
            continue
        new = make_task(text) if choice == "task" else make_note(text)
        p.unlink()
        paths.append_journal(f"triaged {p.name} -> {new.relative_to(paths.OPS_HOME)}")
        print(f"    filed -> {new.relative_to(paths.OPS_HOME)}")
        if (not yes) and choice != kind:  # override -> offer to learn the rule (§10)
            if input("    record a filing rule for next time? [y/N] ").strip().lower() == "y":
                record_rule(f"items like \"{title[:40]}\" -> {choice}")
                print("    rule recorded in wiki/conventions.md")
    if dry:
        print("\n(dry run — nothing changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
