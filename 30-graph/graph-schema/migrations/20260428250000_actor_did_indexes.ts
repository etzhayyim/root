// ADR-0095 P3 — actor_did indexes for key Tier 1 domain tables.
//
// Uses SET BACKGROUND_DDL = true so large tables don't block the cluster.
// vertex_repo_record + vertex_ipaddress_access_log already indexed in 20260428230000.
// Applied out-of-band via direct psql (ADR-2604241342 pattern); kysely_migration
// row inserted manually after apply.

import type { Kysely } from "kysely";
import { sql } from "kysely";

const INDEX_TABLES = [
  // agent runtime
  "vertex_agent_runtime_artifact",
  "vertex_agent_runtime_checkpoint",
  "vertex_agent_runtime_receipt",
  // BPMN
  "vertex_bpmn_activity_event",
  "vertex_bpmn_instance",
  "vertex_bpmn_lexicon_binding",
  "vertex_bpmn_process",
  "vertex_bpmn_process_def",
  "vertex_bpmn_signal_log",
  // gmail / gmeet
  "vertex_gmail_account",
  "vertex_gmail_contact",
  "vertex_gmail_email",
  "vertex_gmail_outbound_email",
  "vertex_gmail_phishing_alert",
  "vertex_gmail_sync_job",
  "vertex_gmail_thread",
  "vertex_gmeet_account",
  "vertex_gmeet_conference",
  "vertex_gmeet_participant",
  "vertex_gmeet_recording",
  // satellite / maps
  "vertex_satellite_analysis",
  "vertex_satellite_scene",
  "vertex_maps_coverage_target",
  // yabai
  "vertex_yabai_alert",
  "vertex_yabai_enforcement",
  "vertex_yabai_entity",
  "vertex_yabai_evidence",
  "vertex_yabai_flag",
  "vertex_yabai_infra_track",
  "vertex_yabai_intel_access_log",
  "vertex_yabai_registration_ban",
  "vertex_yabai_risk",
  // legal
  "vertex_legal_aid_case",
  "vertex_legal_aid_office",
  "vertex_legal_corpus_document",
  // langgraph
  "vertex_langgraph_checkpoint",
  "vertex_langgraph_state",
  // livecam
  "vertex_livecam_anomaly",
  "vertex_livecam_detection_event",
  "vertex_livecam_summary",
  // nokyo
  "vertex_nokyo_farm",
  "vertex_nokyo_member",
  "vertex_nokyo_purchase_order",
  "vertex_nokyo_sale_lot",
  // oshinobi
  "vertex_oshinobi_creator",
  "vertex_oshinobi_entitlement",
  "vertex_oshinobi_payout_ledger",
  "vertex_oshinobi_post",
  "vertex_oshinobi_subscription",
  // natural person
  "vertex_natural_person_cohort_person",
  "vertex_natural_person_identified_person",
  "vertex_natural_person_person_enrichment",
  // arb
  "vertex_arb_proposal",
  "vertex_arb_publication",
  "vertex_arb_quote",
  "vertex_arb_score",
  // m365
  "vertex_m365_sync_state",
  "vertex_m365_user",
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`SET BACKGROUND_DDL = true`.execute(db);
  for (const table of INDEX_TABLES) {
    const idxName = `idx_${table}_actor_did`;
    await sql`CREATE INDEX IF NOT EXISTS ${sql.raw(idxName)} ON ${sql.table(table)} (actor_did)`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const table of [...INDEX_TABLES].reverse()) {
    const idxName = `idx_${table}_actor_did`;
    await sql`DROP INDEX IF EXISTS ${sql.raw(idxName)}`.execute(db);
  }
}
