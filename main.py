from pawpal_system import Pet, Owner, Task, Scheduler

# Create Owner
owner = Owner(name="Alex", available_minutes=300, wake_time="07:00", sleep_time="22:00")

# Create Pets
buddy = Pet(name="Buddy", species="Dog", age=3)
whiskers = Pet(name="Whiskers", species="Cat", age=5)
owner.add_pet(buddy)
owner.add_pet(whiskers)

# Add Tasks to Buddy
buddy.tasks.append(Task(
    title="Morning Walk",
    category="walk",
    duration_minutes=30,
    priority="high",
    task_type="parallel",
    preferred_time="07:00",
    recurrence="daily",
    pet=buddy,
))

buddy.tasks.append(Task(
    title="Vet Appointment",
    category="appointment",
    duration_minutes=60,
    priority="high",
    task_type="exclusive",
    preferred_time="10:00",
    recurrence="none",
    pet=buddy,
))

# Add Task to Whiskers
whiskers.tasks.append(Task(
    title="Feeding",
    category="feeding",
    duration_minutes=10,
    priority="high",
    task_type="exclusive",
    preferred_time="08:00",
    recurrence="daily",
    pet=whiskers,
))

# Run Scheduler
scheduler = Scheduler(owner)
scheduler.load_tasks_from_owner()

scheduled, skipped = scheduler.generate_schedule()

# Print Today's Schedule
print("========== Today's Schedule ==========")
for st in scheduled:
    pet_label = f"[{st.task.pet.name}]" if st.task.pet else ""
    print(f"  {st.start_time} - {st.end_time}  |  {st.task.title} {pet_label}  |  Priority: {st.task.priority}")

if skipped:
    print("\n--- Skipped Tasks ---")
    for task, reason in skipped:
        print(f"  {task.title}: {reason}")
