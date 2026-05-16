import type { Kysely } from "kysely";

// Retire two shosha Zeebe timer-start process defs that have been replaced
// by K8s CronJobs + LangGraph StateGraphs (ADR-2605080600 Phase 5).
// Setting status='migrated' stops the bpmn-dispatcher F5 watcher from
// redeploying these to Zeebe and prevents double-firing.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "in", [
      "shosha_trade_book_recompute",
      "shosha_react_to_upstream",
    ])
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "in", [
      "shosha_trade_book_recompute",
      "shosha_react_to_upstream",
    ])
    .execute();
}
