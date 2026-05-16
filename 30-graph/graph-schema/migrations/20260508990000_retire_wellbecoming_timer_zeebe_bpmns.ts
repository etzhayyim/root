import type { Kysely } from "kysely";

// ADR-2605080600 Phase 5: retire all wellbecoming timer-start Zeebe BPMNs.
// Each is superseded by a K8s CronJob + LangGraph StateGraph registered
// in langgraph_server_app.py.
//
// Retired (9 timer-start processes):
//   wellbecoming_process_mining       → CronJob 0 */6 * * *
//   wellbecoming_detect_bottleneck    → CronJob 0 * * * *
//   wellbecoming_proactive_connect    → CronJob 0 */2 * * *
//   wellbecoming_floor_violation_alert → CronJob */30 * * * *
//   wellbecoming_minimax_sweep        → CronJob */5 * * * *
//   wellbecoming_belief_influence_propagate → CronJob 5 * * * *
//   wellbecoming_belief_noise_inject  → CronJob 10 * * * *
//   wellbecoming_belief_restoring_capture → CronJob 15 * * * *
//   wellbecoming_trust_weight_update  → CronJob 20 * * * *
//
// NOT retired (XRPC-triggered): wellbecoming_agent_loop
const TIMER_BPMNS = [
  "wellbecoming_process_mining",
  "wellbecoming_detect_bottleneck",
  "wellbecoming_proactive_connect",
  "wellbecoming_floor_violation_alert",
  "wellbecoming_minimax_sweep",
  "wellbecoming_belief_influence_propagate",
  "wellbecoming_belief_noise_inject",
  "wellbecoming_belief_restoring_capture",
  "wellbecoming_trust_weight_update",
];

export async function up(db: Kysely<any>): Promise<void> {
  for (const id of TIMER_BPMNS) {
    await db
      .updateTable("vertex_bpmn_process_def" as any)
      .set({ status: "migrated" } as any)
      .where("bpmn_process_id" as any, "=", id)
      .execute();
  }
}
