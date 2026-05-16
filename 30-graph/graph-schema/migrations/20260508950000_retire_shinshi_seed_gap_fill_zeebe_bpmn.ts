import type { Kysely } from "kysely";

// Retire shinshi_seed_gap_fill Zeebe timer-start process def replaced
// by K8s CronJob + LangGraph StateGraph (ADR-2605080600 Phase 5).
// Setting status='migrated' stops the bpmn-dispatcher F5 watcher from
// redeploying this to Zeebe and prevents double-firing alongside the CronJob.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "=", "shinshi_seed_gap_fill")
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "=", "shinshi_seed_gap_fill")
    .execute();
}
