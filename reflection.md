# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
The UML shows a pet care scheduling system where an Owner owns multiple Pets, manages a pool of Tasks, and a Scheduler processes those tasks into a timed daily schedule of ScheduledTasks.

- What classes did you include, and what responsibilities did you assign to each?
Pet — stores pet data (name, species, age, breed, notes)
Owner — holds owner availability and preferences; maintains the pet list
Task — defines a care task: category, duration, priority, recurrence, and completion status
ScheduledTask — pairs a Task with a specific start/end time slot and placement reason
Scheduler — builds the day's schedule by sorting tasks by priority, assigning time slots, detecting conflicts, and reporting skipped tasks

**b. Design changes**

- Did your design change during implementation?
Yes
- If yes, describe at least one change and why you made it.
Added pet field to Task — tasks now know which pet they're for
detect_conflict() — implemented; only blocks on exclusive tasks, parallel tasks overlap freely
generate_schedule() — split into _filter_due_tasks() and _find_slot() helper methods so it's not one giant method

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
Preferred Time
- How did you decide which constraints mattered most?
Overlapping time intervals

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
Overalapping times
- Why is that tradeoff reasonable for this scenario?
Sometimes, owner might have to look for two pets during same interval

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
