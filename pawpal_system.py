"""
PawPal+ Backend Logic
pawpal_system.py

Logic layer — all backend classes live here. No UI code.
"""

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
        pass


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

    def priority_value(self) -> int:
        """Return numeric priority for sorting (high=3, medium=2, low=1)."""
        pass

    def is_due_today(self, schedule_date: date) -> bool:
        """Return True if this task should appear in today's schedule."""
        pass

    def mark_completed(self, completed_date: Optional[date] = None):
        """Mark this task as done and record the date."""
        pass

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
        pass

    def remove_task(self, title: str):
        """Remove a task from the pool by title."""
        pass

    def detect_conflict(self, new_start: int, new_end: int, placed: list) -> Optional[ScheduledTask]:
        """Check if a proposed time slot conflicts with any exclusive placed task."""
        pass

    def generate_schedule(self) -> tuple:
        """
        Run the scheduling algorithm.
        Returns (scheduled: list[ScheduledTask], skipped: list[tuple])
        """
        pass

    def explain_schedule(self, scheduled: list, skipped: list) -> str:
        """Return a human-readable summary of the schedule and skipped tasks."""
        pass
