"""
statemodel.py — models of the consistency invariants the design relies on.

Four areas that quietly break reliable systems:
  1. Task status conflict — the folder is the status; frontmatter is a mirror. §7.2: "folder
     wins on conflict." A drift between them must be detectable (consolidate/doctor reports it).
  2. System-of-record — the index/cache is DERIVED from files; it must rebuild to exactly match
     the files, discarding any DB-only drift (§10.2: "rm -rf .index && plainkeep index").
  3. Journal append — the journal is shared cross-driver memory (§8). Writes must be atomic
     appends; a read-modify-write loses entries when two drivers run concurrently.
  4. Restore order — §14.2: auth must exist before any private clone/restore; the ordered
     sequence has real dependencies.
"""
from __future__ import annotations
import hashlib

TASK_STATUSES = ("inbox", "active", "waiting", "done")


# --- 1. task status: folder wins ---
def effective_status(folder: str, frontmatter_status: str) -> str:
    return folder  # the folder is the source of truth (§7.2)


def status_drift(folder: str, frontmatter_status: str) -> bool:
    return folder != frontmatter_status


# --- 2. system-of-record: index is derived, rebuild == files ---
def derive_index(files: dict[str, str]) -> dict[str, str]:
    return {slug: hashlib.sha1(content.encode()).hexdigest() for slug, content in files.items()}


def rebuild_index(files: dict[str, str], old_index: dict[str, str]) -> dict[str, str]:
    # the old index is discarded entirely and recomputed from files (the only truth)
    return derive_index(files)


# --- 3. journal append ---
def atomic_append(base: str, lines: list[str]) -> str:
    """O_APPEND-style: each driver appends to the live file; all entries survive."""
    c = base
    for ln in lines:
        c = c + ln + "\n"
    return c


def read_modify_write(base: str, lines: list[str]) -> str:
    """The hazard: each driver reads the SAME base, then writes its version; last write wins."""
    writes = [base + ln + "\n" for ln in lines]
    return writes[-1]


def line_count(content: str) -> int:
    return len([ln for ln in content.splitlines() if ln.strip()])


# --- 4. restore order (§14.2) ---
# each step depends on these earlier steps having run
RESTORE_DEPS = {
    "toolchain": set(),
    "auth": {"toolchain"},               # 1Password / SSH key (Brewfile installed it)
    "clone_plainkeep": {"auth"},         # private remote needs auth
    "doctor_init": {"clone_plainkeep"},  # creates ~/work + ~/files skeleton
    "clone_work": {"auth", "clone_plainkeep"}, # registry lives in plainkeep
    "restic_restore": {"auth", "doctor_init"},  # bucket key in 1Password; ~/files skeleton exists
}


def validate_restore_order(seq: list[str]) -> list[str]:
    """Return a list of dependency violations for the given ordering."""
    seen: set[str] = set()
    violations = []
    for step in seq:
        for dep in RESTORE_DEPS.get(step, set()):
            if dep not in seen:
                violations.append(f"'{step}' runs before its dependency '{dep}'")
        seen.add(step)
    return violations
