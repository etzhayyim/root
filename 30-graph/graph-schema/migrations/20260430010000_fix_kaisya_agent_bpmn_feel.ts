import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix invalid JS ternary (X ? A : B) in 7 kaisya AI-org BPMN files.
// FEEL (Zeebe) requires `if X then A else B` — ternary causes INVALID_ARGUMENT.
// Re-seeds XML from corrected source files and resets status='active' so
// the F5 watcher deploys them on the next 30s tick.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const AGENTS = [
  {
    bpmnProcessId: "kaisya_ceo_daily_briefing",
    file: "ceoDailyBriefing.bpmn",
  },
  {
    bpmnProcessId: "kaisya_coo_ops_monitor",
    file: "cooOpsMonitor.bpmn",
  },
  {
    bpmnProcessId: "kaisya_clo_case_sweep",
    file: "cloCaseSweep.bpmn",
  },
  {
    bpmnProcessId: "kaisya_eng_deploy_health_check",
    file: "engDeployHealthCheck.bpmn",
  },
  {
    bpmnProcessId: "kaisya_eng_infra_monitor",
    file: "engInfraMonitor.bpmn",
  },
  {
    bpmnProcessId: "kaisya_brand_content_briefing",
    file: "brandContentBriefing.bpmn",
  },
  {
    bpmnProcessId: "kaisya_creative_asset_pipeline",
    file: "creativeAssetPipeline.bpmn",
  },
] as const;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const agent of AGENTS) {
    const xml = readFileSync(
      path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/kaisya", agent.file),
      "utf8",
    );
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      UPDATE vertex_bpmn_process_def
      SET "xml" = ${xml},
          xml_byte_size = CAST(${size} AS integer),
          status = 'active'
      WHERE bpmn_process_id = ${agent.bpmnProcessId}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const agent of AGENTS) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'inactive'
      WHERE bpmn_process_id = ${agent.bpmnProcessId}
    `.execute(db);
  }
}
