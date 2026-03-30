from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str = ""
    notes: str = ""
    tasks: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_minutes: int = 240
    wake_time: str = "07:00"
    sleep_time: str = "22:00"
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self.pets.append(pet)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    category: str           # walk, feeding, medication, grooming, enrichment, appointment, other
    duration_minutes: int
    priority: str           # low, medium, high
    task_type: str = "exclusive"        # exclusive or parallel
    preferred_time: Optional[str] = None  # "HH:MM" — optional fixed time
    recurrence: str = "none"           # none, daily, weekly, monthly, quarterly
    recurrence_days: list = field(default_factory=list)  # e.g. ["Saturday"]
    last_completed: Optional[date] = None
    notes: str = ""
    pet: Optional["Pet"] = None         # which pet this task belongs to

    def priority_value(self) -> int:
        """Return numeric priority for sorting (high=3, medium=2, low=1)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 1)

    def is_due_today(self, schedule_date: date) -> bool:
        """Return True if this task should appear in today's schedule."""
        if self.recurrence == "none":
            return True
        if self.recurrence == "daily":
            return True
        if self.recurrence == "weekly":
            return schedule_date.strftime("%A") in self.recurrence_days
        if self.recurrence in ("monthly", "quarterly"):
            if not self.last_completed:
                return True
            months = 1 if self.recurrence == "monthly" else 3
            delta = (schedule_date.year - self.last_completed.year) * 12 + (
                schedule_date.month - self.last_completed.month
            )
            return delta >= months
        return False

    def mark_completed(self, completed_date: Optional[date] = None):
        """Mark this task as done and record the date."""
        self.last_completed = completed_date or date.today()

    def to_dict(self) -> dict:
        """Serialize task to a dictionary."""
        pass


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: Task
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"
    reason: str

    def to_dict(self) -> dict:
        """Serialize scheduled task to a dictionary."""
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, schedule_date: Optional[date] = None):
        self.owner = owner
        self.tasks: list[Task] = []
        self.schedule_date = schedule_date or date.today()

    def add_task(self, task: Task):
        """Add a task to the pool."""
        self.tasks.append(task)

    def load_tasks_from_owner(self):
        """Pull all tasks from each pet on the owner into the scheduler pool."""
        for pet in self.owner.pets:
            for task in pet.tasks:
                self.add_task(task)

    def remove_task(self, title: str):
        """Remove a task from the pool by title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def detect_conflict(self, new_start: int, new_end: int, placed: list) -> Optional[ScheduledTask]:
        """Check if a proposed time slot conflicts with any exclusive placed task."""
        for st in placed:
            if st.task.task_type != "exclusive":
                continue
            existing_start = int(st.start_time[:2]) * 60 + int(st.start_time[3:])
            existing_end = int(st.end_time[:2]) * 60 + int(st.end_time[3:])
            if new_start < existing_end and new_end > existing_start:
                return st
        return None

    def _filter_due_tasks(self) -> list:
        """Return tasks due today sorted by priority (high first)."""
        due = [t for t in self.tasks if t.is_due_today(self.schedule_date)]
        return sorted(due, key=lambda t: t.priority_value(), reverse=True)

    def _find_slot(self, task: Task, cursor: int, sleep: int, placed: list) -> Optional[int]:
        """Find the earliest valid start minute for a task."""
        def to_min(hhmm): return int(hhmm[:2]) * 60 + int(hhmm[3:])
        start = max(cursor, to_min(task.preferred_time)) if task.preferred_time else cursor
        end = start + task.duration_minutes
        while end <= sleep:
            conflict = self.detect_conflict(start, end, placed)
            if conflict is None:
                return start
            start = int(conflict.end_time[:2]) * 60 + int(conflict.end_time[3:])
            end = start + task.duration_minutes
        return None

    def generate_schedule(self) -> tuple:
        """
        Run the scheduling algorithm.
        Returns (scheduled: list[ScheduledTask], skipped: list[tuple])
        """
        def to_min(hhmm): return int(hhmm[:2]) * 60 + int(hhmm[3:])
        def to_hhmm(m): return f"{m // 60:02d}:{m % 60:02d}"

        wake = to_min(self.owner.wake_time)
        sleep = to_min(self.owner.sleep_time)
        available = min(self.owner.available_minutes, sleep - wake)

        scheduled, skipped = [], []
        cursor = wake
        minutes_used = 0

        for task in self._filter_due_tasks():
            if minutes_used + task.duration_minutes > available:
                skipped.append((task, "exceeds available time"))
                continue
            start = self._find_slot(task, cursor, sleep, scheduled)
            if start is None:
                skipped.append((task, "no available slot"))
                continue
            end = start + task.duration_minutes
            scheduled.append(ScheduledTask(task=task, start_time=to_hhmm(start), end_time=to_hhmm(end),
                                           reason=f"priority: {task.priority}"))
            minutes_used += task.duration_minutes
            if task.task_type == "exclusive":
                cursor = end

        return scheduled, skipped

    def explain_schedule(self, scheduled: list, skipped: list) -> str:
        """Return a human-readable summary of the schedule and skipped tasks."""
        pass
