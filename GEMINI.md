# Etz Hayyim Project Guidelines

## Task Management Workflow
This project uses the Gemini CLI Task Tracker to manage work and track progress across its multiple epics and modules.

- **Session Start / Next Steps:** At the beginning of a session, or whenever the user asks "what's next?" or "how should we proceed?", ALWAYS use the `tracker_list_tasks` tool to check the current state of the tracker.
- **Prioritization:** Identify tasks that are `open` or `in_progress` and are NOT blocked by other dependencies. Present these as the immediate next steps.
- **Task Updates:** When a logical unit of work is completed and verified, ask the user if the corresponding task should be marked as `closed`, or update it directly if explicitly instructed.
- **Decomposition:** When taking on a new complex feature, create new tasks and link them to the appropriate parent Epic.
