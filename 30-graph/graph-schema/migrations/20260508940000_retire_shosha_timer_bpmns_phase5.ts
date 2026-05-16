import type { Kysely } from "kysely";

// Retire remaining shosha Zeebe timer-start process defs replaced
// by K8s CronJobs + LangGraph StateGraphs (ADR-2605080600 Phase 5).
// Complements 20260508930000 which retired trade_book_recompute + react_to_upstream.
export async function up(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "in", [
      "shosha_trade_idea_synthesize",
      "shosha_daily_report",
    ])
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "in", [
      "shosha_trade_idea_synthesize",
      "shosha_daily_report",
    ])
    .execute();
}
