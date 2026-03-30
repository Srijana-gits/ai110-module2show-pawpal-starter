from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    care_window_start: str       # "07:00" — when owner starts pet care
    care_window_end: str         # "22:00" — when owner ends pet care
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self.pets.append(pet)


# ---------------------------------------------------------------------------
# CareActivity
# ---------------------------------------------------------------------------

@dataclass
class CareActivity:
    title: str
    pet: Pet
    care_type: str               # walk, feed, groom, vet, play, medicate
    duration_minutes: int
    priority: str                # urgent, normal, flexible
    preferred_time: str              # "HH:MM" — required
    needs_full_attention: bool = True   # True = blocks other tasks, False = can overlap
    repeat: str = "once"         # once, daily, weekly
    due_date: Optional[date] = None
    done: bool = False

    def priority_value(self) -> int:
        return {"urgent": 3, "normal": 2, "flexible": 1}.get(self.priority, 1)

    def preferred_time_minutes(self) -> int:
        from datetime import datetime
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                t = datetime.strptime(self.preferred_time.strip(), fmt)
                return t.hour * 60 + t.minute
            except ValueError:
                continue
        return 0

    def is_due_today(self, schedule_date: date) -> bool:
        if self.done:
            return False
        if self.repeat == "once":
            return True
        if self.repeat in ("daily", "weekly"):
            return self.due_date is None or self.due_date <= schedule_date
        return False

    def mark_done(self, completed_date: Optional[date] = None) -> Optional["CareActivity"]:
        """
        Mark activity done. For daily/weekly, creates and returns the next
        occurrence using timedelta. Returns None for one-time activities.
        """
        today = completed_date or date.today()
        self.done = True

        if self.repeat == "daily":
            next_due = today + timedelta(days=1)
        elif self.repeat == "weekly":
            next_due = today + timedelta(weeks=1)
        else:
            return None

        next_activity = CareActivity(
            title=self.title,
            pet=self.pet,
            care_type=self.care_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            needs_full_attention=self.needs_full_attention,
            repeat=self.repeat,
            preferred_time=self.preferred_time,
            due_date=next_due,
        )
        if self.pet is not None:
            self.pet.tasks.append(next_activity)
        return next_activity


# ---------------------------------------------------------------------------
# ScheduledEntry
# ---------------------------------------------------------------------------

@dataclass
class ScheduledEntry:
    activity: CareActivity
    start: str    # "HH:MM"
    end: str      # "HH:MM"
    done: bool = False


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, schedule_date: Optional[date] = None):
        self.owner = owner
        self.activities: list[CareActivity] = []
        self.schedule_date = schedule_date or date.today()

    def load_from_owner(self):
        for pet in self.owner.pets:
            for activity in pet.tasks:
                self.activities.append(activity)

    def detect_conflict(self, new_activity: CareActivity, new_start: int, new_end: int, placed: list) -> Optional[ScheduledEntry]:
        """Only flag conflicts between full-attention activities for the same pet."""
        for entry in placed:
            if not entry.activity.needs_full_attention:
                continue
            if entry.activity.pet != new_activity.pet:
                continue
            existing_start = int(entry.start.split(":")[0]) * 60 + int(entry.start.split(":")[1])
            existing_end = int(entry.end.split(":")[0]) * 60 + int(entry.end.split(":")[1])
            if new_start < existing_end and new_end > existing_start:
                return entry
        return None

    def _due_activities(self) -> list:
        """Sort by priority (urgent first), then preferred time (earlier first)."""
        due = [a for a in self.activities if a.is_due_today(self.schedule_date)]
        return sorted(due, key=lambda a: (-a.priority_value(), a.preferred_time_minutes()))

    def check_conflicts(self, entries: list) -> list[str]:
        """
        Lightweight post-schedule conflict check.
        Returns a list of warning strings for any overlapping entries —
        same pet or different pets (owner can't be in two places at once).
        Never crashes — only warns.
        """
        warnings = []
        def to_min(hhmm): return int(hhmm[:2]) * 60 + int(hhmm[3:])

        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                a_start, a_end = to_min(a.start), to_min(a.end)
                b_start, b_end = to_min(b.start), to_min(b.end)
                if a_start < b_end and a_end > b_start:
                    if a.activity.pet == b.activity.pet:
                        warnings.append(
                            f"⚠ Same-pet conflict: '{a.activity.title}' and '{b.activity.title}' "
                            f"overlap for {a.activity.pet.name} ({a.start}–{a.end} vs {b.start}–{b.end})"
                        )
                    else:
                        warnings.append(
                            f"⚠ Owner conflict: '{a.activity.title}' [{a.activity.pet.name}] and "
                            f"'{b.activity.title}' [{b.activity.pet.name}] overlap "
                            f"({a.start}–{a.end} vs {b.start}–{b.end})"
                        )
        return warnings

    def filter_by_pet(self, entries: list, pet_name: str) -> list:
        return [e for e in entries if e.activity.pet and e.activity.pet.name == pet_name]

    def filter_by_status(self, entries: list, done: bool) -> list:
        return [e for e in entries if e.done == done]

    def _find_slot(self, activity: CareActivity, cursor: int, end_boundary: int, placed: list) -> Optional[int]:
        def to_min(hhmm):
            from datetime import datetime
            for fmt in ("%I:%M %p", "%H:%M"):
                try:
                    t = datetime.strptime(hhmm.strip(), fmt)
                    return t.hour * 60 + t.minute
                except ValueError:
                    continue
            raise ValueError(f"Unrecognized time format: {hhmm}")
        start = max(cursor, to_min(activity.preferred_time))
        end = start + activity.duration_minutes
        while end <= end_boundary:
            conflict = self.detect_conflict(activity, start, end, placed)
            if conflict is None:
                return start
            start = int(conflict.end.split(":")[0]) * 60 + int(conflict.end.split(":")[1])
            end = start + activity.duration_minutes
        return None

    def generate_schedule(self) -> tuple:
        """Returns (entries: list[ScheduledEntry], skipped: list[tuple])"""
        def to_min(hhmm):
            from datetime import datetime
            for fmt in ("%I:%M %p", "%H:%M"):
                try:
                    t = datetime.strptime(hhmm.strip(), fmt)
                    return t.hour * 60 + t.minute
                except ValueError:
                    continue
            raise ValueError(f"Unrecognized time format: {hhmm}")
        def to_hhmm(m): return f"{m // 60:02d}:{m % 60:02d}"

        window_start = to_min(self.owner.care_window_start)
        window_end = to_min(self.owner.care_window_end)
        entries, skipped = [], []

        for activity in self._due_activities():
            start = self._find_slot(activity, window_start, window_end, entries)
            if start is None:
                skipped.append((activity, "no slot available in care window"))
                continue
            end = start + activity.duration_minutes
            entries.append(ScheduledEntry(activity=activity, start=to_hhmm(start), end=to_hhmm(end)))

        return entries, skipped
