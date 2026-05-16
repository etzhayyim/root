/**
 * Phase 5 (ADR-2605080600): retire shosha_market_intelligence_ingest Zeebe timer-start.
 *
 * The K8s CronJob (0 * * * *) now owns this hourly trigger via LangGraph Server /runs.
 * Setting status='migrated' prevents the bpmn-dispatcher F5 watcher from redeploying
 * the Zeebe timer-start process, eliminating double-firing.
 */
import type { Kysely } from "kysely";
import type { Database } from "../src/database.js";

export async function up(db: Kysely<Database>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "migrated" } as any)
    .where("bpmn_process_id" as any, "=", "shosha_market_intelligence_ingest")
    .execute();
}

export async function down(db: Kysely<Database>): Promise<void> {
  await db
    .updateTable("vertex_bpmn_process_def" as any)
    .set({ status: "active" } as any)
    .where("bpmn_process_id" as any, "=", "shosha_market_intelligence_ingest")
    .execute();
}
