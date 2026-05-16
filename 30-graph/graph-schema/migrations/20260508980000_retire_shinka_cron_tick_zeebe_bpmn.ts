import type { Kysely } from "kysely";

// ADR-2605080600 Phase 5: retire shinka_cron_tick Zeebe timer-start BPMN.
// All 3 versions (v1, v2, v3) are superseded by the K8s CronJob
// `shinka-cron-tick` (schedule */15 * * * *) + LangGraph StateGraph
// `shinka_cron_tick` registered in langgraph_server_app.py.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "=", "shinka_cron_tick")
    .execute();
}
