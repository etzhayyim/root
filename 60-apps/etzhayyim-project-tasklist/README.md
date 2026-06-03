# etzhayyim-project-tasklist

Human-in-the-loop task approval UI for scheduler-generated tasks.

- Frontend host: `https://tasklist.etzhayyim.com`
- Approval backend (MCP): `https://q2m4f8kd.etzhayyim.com/api/mcp`
- Primary flow:
  1. Scheduler creates/updates automation with `human_in_loop.enabled=true`.
  2. When a task is due, scheduler creates an approval request in `etzhayyim-project-approvals`.
  3. Human approvers decide (`approved` / `denied`) from tasklist UI.
  4. Scheduler executes target only after approval status becomes `approved`.
