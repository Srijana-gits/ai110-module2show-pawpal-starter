from pawpal_system import Pet, Owner, CareActivity, Scheduler

# Create Owner with care window
owner = Owner(name="Alex", care_window_start="07:00", care_window_end="22:00")

# Add pets with time budgets
buddy = Pet(name="Buddy", species="dog", age=3)
whiskers = Pet(name="Whiskers", species="cat", age=5)
owner.add_pet(buddy)
owner.add_pet(whiskers)

# Care activities for Buddy
buddy.tasks.append(CareActivity(
    title="Morning Walk",
    pet=buddy,
    care_type="walk",
    duration_minutes=30,
    priority="urgent",
    needs_full_attention=True,
    repeat="daily",
    preferred_time="07:00",
))

buddy.tasks.append(CareActivity(
    title="Vet Appointment",
    pet=buddy,
    care_type="vet",
    duration_minutes=60,
    priority="urgent",
    needs_full_attention=True,
    repeat="once",
    preferred_time="10:00",
))

buddy.tasks.append(CareActivity(
    title="Playtime",
    pet=buddy,
    care_type="play",
    duration_minutes=20,
    priority="flexible",
    needs_full_attention=False,
    repeat="daily",
    preferred_time="09:00",
))

# Care activities for Whiskers
whiskers.tasks.append(CareActivity(
    title="Feeding",
    pet=whiskers,
    care_type="feed",
    duration_minutes=10,
    priority="urgent",
    needs_full_attention=False,
    repeat="daily",
    preferred_time="08:00",
))

whiskers.tasks.append(CareActivity(
    title="Grooming",
    pet=whiskers,
    care_type="groom",
    duration_minutes=20,
    priority="normal",
    needs_full_attention=True,
    repeat="weekly",
    preferred_time="09:00",
))

# Run Scheduler
scheduler = Scheduler(owner)
scheduler.load_from_owner()
entries, skipped = scheduler.generate_schedule()

# Today's schedule
print("========== Today's Schedule ==========")
for e in entries:
    pet_label = f"[{e.activity.pet.name}]" if e.activity.pet else ""
    print(f"  {e.start} - {e.end}  |  {e.activity.title} {pet_label}  |  {e.activity.priority}")

# Conflict check
warnings = scheduler.check_conflicts(entries)
if warnings:
    print("\n========== Conflict Warnings ==========")
    for w in warnings:
        print(f"  {w}")
else:
    print("\n  No conflicts detected.")

if skipped:
    print("\n--- Skipped ---")
    for activity, reason in skipped:
        print(f"  {activity.title}: {reason}")

# Filter by pet
print("\n========== Buddy's Schedule ==========")
for e in scheduler.filter_by_pet(entries, "Buddy"):
    print(f"  {e.start} - {e.end}  |  {e.activity.title}")

# Mark done + auto-create next occurrence
print("\n========== Marking 'Morning Walk' Done ==========")
morning_walk = next(a for a in buddy.tasks if a.title == "Morning Walk")
next_walk = morning_walk.mark_done()
if next_walk:
    print(f"  Next '{next_walk.title}' due: {next_walk.due_date}")

# Filter by status
entries[0].done = True
print("\n========== Pending ==========")
for e in scheduler.filter_by_status(entries, done=False):
    print(f"  {e.activity.title} [{e.activity.pet.name}]")

print("\n========== Done ==========")
for e in scheduler.filter_by_status(entries, done=True):
    print(f"  {e.activity.title} [{e.activity.pet.name}]")
