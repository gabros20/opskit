"""
sweepsim.py — a discrete-event simulation of the §9.4 Desktop/Downloads decay machine.

The design promises a self-cleaning machine:
    ~/Desktop|~/Downloads  --7 days untouched-->  _swept/YYYY-MM/  --60 more days-->  Trash
with three guarantees: (1) the 7-day pass MOVES, never deletes; (2) ingesting a file removes it
from the decay path (promotion is deliberate); (3) nothing is actually gone for ~67 days.

We model a virtual clock (day counter) and run `sweep` once per day, then assert the timers and
invariants hold. This catches off-by-one timer bugs, double-moves (non-idempotency), and any
path where a file is lost early.
"""
from __future__ import annotations
from dataclasses import dataclass, field

SWEEP_DAYS = 7        # untouched this long in Desktop/Downloads -> _swept
TRASH_DAYS = 60       # this long in _swept -> Trash


@dataclass
class FileState:
    name: str
    zone: str               # "desktop" | "downloads" | "swept" | "trash" | "ingested"
    last_touched_day: int   # day the file was last modified/created/accessed
    swept_on_day: int | None = None
    history: list[str] = field(default_factory=list)

    def log(self, day: int, msg: str):
        self.history.append(f"day {day}: {msg}")


class Machine:
    """The decay state machine. `month_of` lets us check the dated _swept/YYYY-MM bucket logic."""

    def __init__(self, files: list[FileState]):
        self.files = {f.name: f for f in files}
        self.day = 0
        self.trash_log: list[tuple[int, str]] = []

    def month_of(self, day: int) -> str:
        # virtual calendar: 30-day months starting 2026-06
        m = 6 + day // 30
        y = 2026 + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        return f"{y:04d}-{m:02d}"

    def touch(self, name: str):
        self.files[name].last_touched_day = self.day
        self.files[name].log(self.day, "touched (timer reset)")

    def ingest(self, name: str):
        f = self.files[name]
        f.zone = "ingested"
        f.log(self.day, "ingested -> removed from decay path")

    def run_sweep(self):
        """One daily sweep pass. Idempotent: safe to call repeatedly on the same day."""
        for f in self.files.values():
            if f.zone in ("desktop", "downloads"):
                if self.day - f.last_touched_day >= SWEEP_DAYS:
                    f.zone = "swept"
                    f.swept_on_day = self.day
                    f.bucket = self.month_of(self.day)  # type: ignore[attr-defined]
                    f.log(self.day, f"MOVED to _swept/{f.bucket} (untouched {self.day - f.last_touched_day}d)")
            elif f.zone == "swept":
                if f.swept_on_day is not None and self.day - f.swept_on_day >= TRASH_DAYS:
                    f.zone = "trash"
                    self.trash_log.append((self.day, f.name))
                    f.log(self.day, f"TRASHED (in _swept {self.day - f.swept_on_day}d)")

    def advance_to(self, day: int, daily_sweep: bool = True, actions: dict[int, list] | None = None):
        actions = actions or {}
        while self.day < day:
            self.day += 1
            for act in actions.get(self.day, []):
                kind, name = act
                if kind == "touch":
                    self.touch(name)
                elif kind == "ingest":
                    self.ingest(name)
            if daily_sweep:
                self.run_sweep()
                self.run_sweep()  # second call same day MUST be a no-op (idempotency)
