import type { Kysely } from "kysely";
import { sql } from "kysely";

// P7: Activate the 7 dormant AI-org role agents.
// Timer-start BPMNs: R/PT24H (5 agents) + R/PT4H (2 eng agents).
// F5 watcher in dispatcher_main.py detects status='active' + deployed_zeebe_key IS NULL
// and auto-deploys to Zeebe within 30s. No further manual steps required.

const AGENTS = [
  "kaisya_ceo_daily_briefing",
  "kaisya_coo_ops_monitor",
  "kaisya_clo_case_sweep",
  "kaisya_eng_deploy_health_check",
  "kaisya_eng_infra_monitor",
  "kaisya_brand_content_briefing",
  "kaisya_creative_asset_pipeline",
] as const;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const processId of AGENTS) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'active'
      WHERE bpmn_process_id = ${processId}
        AND status = 'inactive'
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const processId of AGENTS) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'inactive'
      WHERE bpmn_process_id = ${processId}
    `.execute(db);
  }
}
