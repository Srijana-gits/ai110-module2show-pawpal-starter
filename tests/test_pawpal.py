import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from pawpal_system import Pet, Task


def test_mark_completed():
    task = Task(title="Walk", category="walk", duration_minutes=30, priority="high")
    assert task.last_completed is None
    task.mark_completed()
    assert task.last_completed == date.today()


def test_add_task_increases_pet_task_count():
    buddy = Pet(name="Buddy", species="Dog", age=3)
    assert len(buddy.tasks) == 0
    task = Task(title="Feeding", category="feeding", duration_minutes=10, priority="high")
    buddy.tasks.append(task)
    assert len(buddy.tasks) == 1
