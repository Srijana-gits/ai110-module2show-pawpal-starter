import streamlit as st
from datetime import time as dtime
from pawpal_system import Pet, Owner, CareActivity, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session state ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "activities" not in st.session_state:
    st.session_state.activities = []
if "entries" not in st.session_state:
    st.session_state.entries = []
if "skipped" not in st.session_state:
    st.session_state.skipped = []

# --- Owner Setup ---
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value="")
with col2:
    care_start = st.time_input("Available from", value=dtime(7, 0))
with col3:
    care_end = st.time_input("Available until", value=dtime(22, 0))

if st.button("Save Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        care_window_start=care_start.strftime("%H:%M"),
        care_window_end=care_end.strftime("%H:%M"),
    )
    st.success(f"Owner '{owner_name}' saved!")

st.divider()

# --- Add a Pet ---
st.subheader("Add a Pet")
if st.session_state.owner is None:
    st.info("Save an owner first.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=30, value=1)

    if st.button("Add Pet"):
        pet = Pet(name=pet_name, species=species, age=int(age))
        st.session_state.owner.add_pet(pet)
        st.success(f"Added '{pet_name}'!")

    if st.session_state.owner.pets:
        st.write("Pets:")
        st.table([{"name": p.name, "species": p.species, "age": p.age}
                  for p in st.session_state.owner.pets])

st.divider()

# --- Add a Care Activity ---
st.subheader("Add a Care Activity")
if not st.session_state.owner or not st.session_state.owner.pets:
    st.info("Add at least one pet first.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    col1, col2, col3 = st.columns(3)
    with col1:
        activity_title = st.text_input("Activity title", value="")
    with col2:
        assigned_pet_name = st.selectbox("For pet", pet_names)
    with col3:
        care_type = st.selectbox("Type", ["walk", "feed", "groom", "vet", "play", "medicate"])

    col4, col5, col6 = st.columns(3)
    with col4:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col5:
        priority = st.selectbox("Priority", ["urgent", "normal", "flexible"])
    with col6:
        repeat = st.selectbox("Repeat", ["once", "daily", "weekly"])

    col7, col8 = st.columns(2)
    with col7:
        needs_attention = st.checkbox("Needs full attention", value=True)
    with col8:
        preferred_time = st.time_input("Preferred time", value=dtime(8, 0))

    if st.button("Add Activity"):
        assigned_pet = next(p for p in st.session_state.owner.pets if p.name == assigned_pet_name)
        activity = CareActivity(
            title=activity_title,
            pet=assigned_pet,
            care_type=care_type,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time.strftime("%H:%M"),
            needs_full_attention=needs_attention,
            repeat=repeat,
        )
        assigned_pet.tasks.append(activity)
        st.session_state.activities.append(activity)
        st.success(f"Added '{activity_title}' for {assigned_pet_name}!")

    if st.session_state.activities:
        st.write("Activities:")
        st.table([
            {"title": a.title, "pet": a.pet.name, "type": a.care_type,
             "duration": a.duration_minutes, "priority": a.priority, "repeat": a.repeat}
            for a in st.session_state.activities
        ])

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner first.")
    elif not st.session_state.activities:
        st.warning("Add at least one care activity first.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.load_from_owner()
        st.session_state.entries, st.session_state.skipped = scheduler.generate_schedule()

# --- Display schedule with Mark Done buttons ---
if st.session_state.entries:
    entries = st.session_state.entries
    scheduler = Scheduler(st.session_state.owner)

    st.success(f"Scheduled {len(entries)} activity(s)")

    header = st.columns([1, 1, 2, 1, 1, 1, 1, 1])
    for col, label in zip(header, ["Start", "End", "Activity", "Pet", "Type", "Priority", "Repeat", ""]):
        col.markdown(f"**{label}**")

    for i, e in enumerate(entries):
        cols = st.columns([1, 1, 2, 1, 1, 1, 1, 1])
        label = "~~" + e.activity.title + "~~" if e.done else e.activity.title
        cols[0].write(e.start)
        cols[1].write(e.end)
        cols[2].markdown(label)
        cols[3].write(e.activity.pet.name if e.activity.pet else "—")
        cols[4].write(e.activity.care_type)
        cols[5].write(e.activity.priority)
        cols[6].write(e.activity.repeat)
        if e.done:
            cols[7].markdown("✅ Done")
        else:
            if cols[7].button("Mark done", key=f"done_{i}"):
                e.done = True
                next_activity = e.activity.mark_done()
                if next_activity:
                    st.session_state.activities.append(next_activity)
                st.rerun()

    conflicts = scheduler.check_conflicts(entries)
    if conflicts:
        st.warning("Scheduling conflicts detected:")
        for w in conflicts:
            st.markdown(f"- {w}")

    if st.session_state.skipped:
        st.warning(f"Skipped {len(st.session_state.skipped)} activity(s):")
        st.table([
            {"Activity": a.title, "Pet": a.pet.name if a.pet else "—", "Reason": reason}
            for a, reason in st.session_state.skipped
        ])
