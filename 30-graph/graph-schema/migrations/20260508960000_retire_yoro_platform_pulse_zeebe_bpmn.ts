import type { Kysely } from "kysely";

// Retire yoro_platform_pulse Zeebe timer-start process def (v1 + v2) replaced
// by K8s CronJob + LangGraph StateGraph (ADR-2605080600 Phase 5).
// Both versions are set to 'migrated' to prevent the bpmn-dispatcher F5 watcher
// from redeploying them to Zeebe alongside the new CronJob.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "=", "yoro_platform_pulse")
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "=", "yoro_platform_pulse")
    .execute();
}
