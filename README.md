# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduler goes beyond a simple task list- it actively detects and reports conflicts so nothing slips through:

- **Conflict detection during placement** — before slotting an activity, `detect_conflict` checks whether a full-attention task for the same pet already occupies that time window. If there's a clash, the slot is pushed forward automatically.
- **Post-schedule conflict check** — after the full schedule is built, `check_conflicts` scans every pair of entries for overlaps. It distinguishes two kinds:
  - *Same-pet conflicts* — two tasks scheduled at the same time for the same pet.
  - *Owner conflicts* — tasks for different pets that overlap, since the owner can't be in two places at once.
- **Priority-first ordering** — urgent tasks are always placed before normal or flexible ones, so high-priority care (medications, vet visits) secures the best available slot first.
- **Skipped task reporting** — if no slot fits within the owner's care window, the task is recorded in a `skipped` list with a reason, rather than silently dropped.
- **Flexible filtering** — `filter_by_pet` and `filter_by_status` let the UI show a focused view (e.g. only Buddy's tasks, or only tasks still pending).

## Testing PawPal+

### How to run the tests

```bash
python -m pytest tests/
```

### What the tests check

The test suite covers three main areas:

**Sorting** — makes sure urgent tasks always get scheduled before normal or flexible ones, and that earlier preferred times come first when two tasks have the same priority.

**Recurring tasks** — confirms that marking a daily task done automatically creates the next one for tomorrow (and weekly tasks create one for 7 days later). One-time tasks just mark done and stop there.

**Conflict detection** — checks that two tasks at the exact same time get flagged, that the scheduler pushes the second task forward instead of double-booking, and that back-to-back tasks (one ends at 9:00, next starts at 9:00) are correctly treated as fine, not a conflict.

There are also smaller checks for edge cases like a pet with no tasks, activities that don't fit inside the owner's care window (they go into a "skipped" list), and filter helpers that let you view only one pet's tasks or only pending tasks.

### Confidence Level

**4 / 5 stars**

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
