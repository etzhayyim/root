import type { Kysely } from "kysely";

// Retire animeka_autopilot Zeebe timer-start process def replaced
// by K8s CronJob + LangGraph StateGraph (ADR-2605080600 Phase 5).
// Schedule: */15 * * * * (every 15 min). Full 8-node pipeline:
// scene text → storyboard (+retry) → layout → keyframe → background → post → audit.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "=", "animeka_autopilot")
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "=", "animeka_autopilot")
    .execute();
}
