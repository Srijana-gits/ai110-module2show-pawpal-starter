import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import CareActivity, Owner, Pet, ScheduledEntry, Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(start="07:00", end="22:00"):
    return Owner(name="Alex", care_window_start=start, care_window_end=end)


def make_pet(name="Buddy"):
    return Pet(name=name, species="Dog", age=3)


def make_activity(title, pet, priority="normal", preferred_time="08:00",
                  duration=30, repeat="once", needs_full_attention=True, due_date=None):
    return CareActivity(
        title=title,
        pet=pet,
        care_type="walk",
        duration_minutes=duration,
        priority=priority,
        preferred_time=preferred_time,
        needs_full_attention=needs_full_attention,
        repeat=repeat,
        due_date=due_date,
    )


def make_scheduler(*activities, start="07:00", end="22:00"):
    owner = make_owner(start, end)
    s = Scheduler(owner)
    s.activities = list(activities)
    return s


# ---------------------------------------------------------------------------
# Happy Path: basic scheduling
# ---------------------------------------------------------------------------

def test_single_activity_scheduled_at_preferred_time():
    pet = make_pet()
    act = make_activity("Walk", pet, preferred_time="09:00", duration=30)
    s = make_scheduler(act)
    entries, skipped = s.generate_schedule()

    assert len(entries) == 1
    assert len(skipped) == 0
    assert entries[0].start == "09:00"
    assert entries[0].end == "09:30"


def test_no_tasks_returns_empty_schedule():
    owner = make_owner()
    s = Scheduler(owner)
    entries, skipped = s.generate_schedule()
    assert entries == []
    assert skipped == []


def test_owner_with_no_pets_returns_empty_schedule():
    owner = make_owner()
    s = Scheduler(owner)
    s.load_from_owner()
    entries, skipped = s.generate_schedule()
    assert entries == []
    assert skipped == []


# ---------------------------------------------------------------------------
# Sorting Correctness
# ---------------------------------------------------------------------------

def test_urgent_scheduled_before_normal_at_same_preferred_time():
    pet = make_pet()
    normal = make_activity("Feeding", pet, priority="normal", preferred_time="08:00", duration=20)
    urgent = make_activity("Medication", pet, priority="urgent", preferred_time="08:00", duration=20)
    s = make_scheduler(normal, urgent)
    due = s._due_activities()

    assert due[0].title == "Medication"
    assert due[1].title == "Feeding"


def test_same_priority_sorted_by_earlier_preferred_time():
    pet = make_pet()
    later  = make_activity("Groom",  pet, priority="normal", preferred_time="10:00", duration=20)
    earlier = make_activity("Walk",  pet, priority="normal", preferred_time="08:00", duration=20)
    s = make_scheduler(later, earlier)
    due = s._due_activities()

    assert due[0].title == "Walk"
    assert due[1].title == "Groom"


def test_priority_order_urgent_normal_flexible():
    pet = make_pet()
    flex    = make_activity("Play",       pet, priority="flexible", preferred_time="08:00", duration=15)
    normal  = make_activity("Feeding",    pet, priority="normal",   preferred_time="08:00", duration=15)
    urgent  = make_activity("Medication", pet, priority="urgent",   preferred_time="08:00", duration=15)
    s = make_scheduler(flex, normal, urgent)
    due = s._due_activities()

    assert [a.priority for a in due] == ["urgent", "normal", "flexible"]


def test_schedule_entries_in_chronological_order():
    pet = make_pet()
    a = make_activity("Walk",    pet, preferred_time="09:00", duration=30)
    b = make_activity("Feeding", pet, preferred_time="11:00", duration=20)
    s = make_scheduler(a, b)
    entries, _ = s.generate_schedule()

    starts = [e.start for e in entries]
    assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# Recurrence Logic
# ---------------------------------------------------------------------------

def test_mark_done_daily_creates_next_occurrence():
    pet = make_pet()
    act = make_activity("Morning Walk", pet, repeat="daily")
    today = date.today()

    next_act = act.mark_done(completed_date=today)

    assert act.done is True
    assert next_act is not None
    assert next_act.due_date == today + timedelta(days=1)
    assert next_act.repeat == "daily"
    assert next_act.done is False


def test_mark_done_weekly_creates_next_occurrence_seven_days_later():
    pet = make_pet()
    act = make_activity("Grooming", pet, repeat="weekly")
    today = date.today()

    next_act = act.mark_done(completed_date=today)

    assert next_act is not None
    assert next_act.due_date == today + timedelta(weeks=1)


def test_mark_done_once_returns_none():
    pet = make_pet()
    act = make_activity("Vet Visit", pet, repeat="once")
    result = act.mark_done()
    assert result is None


def test_mark_done_daily_appends_to_pet_tasks():
    pet = make_pet()
    act = make_activity("Walk", pet, repeat="daily")
    pet.tasks.append(act)
    initial_count = len(pet.tasks)

    act.mark_done(completed_date=date.today())

    assert len(pet.tasks) == initial_count + 1


def test_done_activity_excluded_from_due_list():
    pet = make_pet()
    act = make_activity("Walk", pet)
    act.done = True
    s = make_scheduler(act)
    assert s._due_activities() == []


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

def test_same_pet_exact_overlap_flagged_by_check_conflicts():
    pet = make_pet()
    a1 = make_activity("Walk",    pet)
    a2 = make_activity("Feeding", pet)
    entries = [
        ScheduledEntry(activity=a1, start="09:00", end="09:30"),
        ScheduledEntry(activity=a2, start="09:00", end="09:30"),
    ]
    owner = make_owner()
    s = Scheduler(owner)
    warnings = s.check_conflicts(entries)

    assert len(warnings) == 1
    assert "Same-pet conflict" in warnings[0]


def test_different_pets_overlap_flagged_as_owner_conflict():
    pet1 = make_pet("Buddy")
    pet2 = make_pet("Luna")
    a1 = make_activity("Walk",    pet1, preferred_time="09:00")
    a2 = make_activity("Feeding", pet2, preferred_time="09:00")
    entries = [
        ScheduledEntry(activity=a1, start="09:00", end="09:30"),
        ScheduledEntry(activity=a2, start="09:15", end="09:45"),
    ]
    owner = make_owner()
    s = Scheduler(owner)
    warnings = s.check_conflicts(entries)

    assert len(warnings) == 1
    assert "Owner conflict" in warnings[0]


def test_back_to_back_entries_not_flagged_as_conflict():
    """08:00–09:00 then 09:00–10:00 share only an endpoint — not an overlap."""
    pet = make_pet()
    a1 = make_activity("Walk",    pet)
    a2 = make_activity("Feeding", pet)
    entries = [
        ScheduledEntry(activity=a1, start="08:00", end="09:00"),
        ScheduledEntry(activity=a2, start="09:00", end="10:00"),
    ]
    owner = make_owner()
    s = Scheduler(owner)
    warnings = s.check_conflicts(entries)

    assert warnings == []


def test_second_task_pushed_past_first_when_same_preferred_time():
    """Scheduler should auto-push the second task, not double-book."""
    pet = make_pet()
    a = make_activity("Walk",    pet, preferred_time="08:00", duration=30)
    b = make_activity("Feeding", pet, preferred_time="08:00", duration=30)
    s = make_scheduler(a, b)
    entries, skipped = s.generate_schedule()

    assert len(entries) == 2
    assert len(skipped) == 0
    # No overlap: first ends where second starts
    assert entries[0].end == entries[1].start


def test_non_full_attention_task_does_not_block_same_slot():
    pet = make_pet()
    background = make_activity("Music", pet, preferred_time="08:00", duration=60, needs_full_attention=False)
    foreground  = make_activity("Walk",  pet, preferred_time="08:00", duration=30, needs_full_attention=True)
    owner = make_owner()
    s = Scheduler(owner)
    placed = [ScheduledEntry(activity=background, start="08:00", end="09:00")]

    conflict = s.detect_conflict(foreground, 480, 510, placed)
    assert conflict is None


# ---------------------------------------------------------------------------
# Care Window Edge Cases
# ---------------------------------------------------------------------------

def test_activity_outside_window_is_skipped():
    pet = make_pet()
    # preferred_time is fine, but duration pushes past the window end
    act = make_activity("Late Walk", pet, preferred_time="21:45", duration=60)
    s = make_scheduler(act, end="22:00")
    entries, skipped = s.generate_schedule()

    assert len(entries) == 0
    assert len(skipped) == 1
    assert skipped[0][1] == "no slot available in care window"


def test_tasks_exceeding_window_partially_skipped():
    pet = make_pet()
    # Three 4-hour tasks in a 7-hour window: only first two fit
    a = make_activity("Task A", pet, priority="urgent",   preferred_time="07:00", duration=240)
    b = make_activity("Task B", pet, priority="normal",   preferred_time="07:00", duration=240)
    c = make_activity("Task C", pet, priority="flexible", preferred_time="07:00", duration=240)
    # 3×4h = 12h total, 07:00–22:00 is a 15h window — all three should fit
    entries, _ = make_scheduler(a, b, c, start="07:00", end="22:00").generate_schedule()
    assert len(entries) == 3

    # Tighter 8h window: only two 4h tasks fit, third is skipped
    _, skipped2 = make_scheduler(a, b, c, start="07:00", end="15:00").generate_schedule()
    assert len(skipped2) >= 1


# ---------------------------------------------------------------------------
# Filter Helpers
# ---------------------------------------------------------------------------

def test_filter_by_pet_returns_only_matching_pet():
    buddy = make_pet("Buddy")
    luna  = make_pet("Luna")
    e1 = ScheduledEntry(activity=make_activity("Walk",    buddy), start="08:00", end="08:30")
    e2 = ScheduledEntry(activity=make_activity("Feeding", luna),  start="09:00", end="09:15")
    owner = make_owner()
    s = Scheduler(owner)

    result = s.filter_by_pet([e1, e2], "Buddy")
    assert len(result) == 1
    assert result[0].activity.pet.name == "Buddy"


def test_filter_by_status_pending_only():
    pet = make_pet()
    e1 = ScheduledEntry(activity=make_activity("Walk",    pet), start="08:00", end="08:30", done=False)
    e2 = ScheduledEntry(activity=make_activity("Feeding", pet), start="09:00", end="09:15", done=True)
    owner = make_owner()
    s = Scheduler(owner)

    pending = s.filter_by_status([e1, e2], done=False)
    assert len(pending) == 1
    assert pending[0].activity.title == "Walk"
