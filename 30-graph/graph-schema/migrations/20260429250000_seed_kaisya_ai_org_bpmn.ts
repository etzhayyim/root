import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for etzhayyim
// Artificial Organism (ADR-2604291800 § ai_org). 8 AI agents, timer-start cadence.
// Humans only act as tasklist approvers via vertex_kaisya_task.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readBpmn = (file: string) =>
  readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/com/etzhayyim/kaisya", file),
    "utf8",
  );

const CREATED_AT = "2026-04-29T23:25:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.kaisya";

// Timer-start BPMN processes (no lexicon binding needed — Zeebe fires them)
const TIMER_ENTRIES = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-ceo-daily-briefing-v1",
    bpmnProcessId: "kaisya_ceo_daily_briefing",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/ceoDailyBriefing.bpmn",
    file: "ceoDailyBriefing.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-coo-ops-monitor-v1",
    bpmnProcessId: "kaisya_coo_ops_monitor",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/cooOpsMonitor.bpmn",
    file: "cooOpsMonitor.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-clo-case-sweep-v1",
    bpmnProcessId: "kaisya_clo_case_sweep",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/cloCaseSweep.bpmn",
    file: "cloCaseSweep.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-eng-deploy-health-check-v1",
    bpmnProcessId: "kaisya_eng_deploy_health_check",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/engDeployHealthCheck.bpmn",
    file: "engDeployHealthCheck.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-eng-infra-monitor-v1",
    bpmnProcessId: "kaisya_eng_infra_monitor",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/engInfraMonitor.bpmn",
    file: "engInfraMonitor.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-brand-content-briefing-v1",
    bpmnProcessId: "kaisya_brand_content_briefing",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/brandContentBriefing.bpmn",
    file: "brandContentBriefing.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-creative-asset-pipeline-v1",
    bpmnProcessId: "kaisya_creative_asset_pipeline",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/kaisya/creativeAssetPipeline.bpmn",
    file: "creativeAssetPipeline.bpmn",
  },
];

// XRPC-triggered procedures (none-start) — need lexicon bindings
const XRPC_ENTRIES = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-approve-task-v1",
    bpmnProcessId: "kaisya_approve_task",
    sourcePath: "",  // inline-only, no BPMN file (direct DB update via pymagatama primitive)
    nsid: "com.etzhayyim.apps.kaisya.approveTask",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-kaisya-approveTask-v1",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-reject-task-v1",
    bpmnProcessId: "kaisya_reject_task",
    sourcePath: "",
    nsid: "com.etzhayyim.apps.kaisya.rejectTask",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-kaisya-rejectTask-v1",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-list-tasks-v1",
    bpmnProcessId: "kaisya_list_tasks",
    sourcePath: "",
    nsid: "com.etzhayyim.apps.kaisya.listTasks",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-kaisya-listTasks-v1",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-get-agent-log-v1",
    bpmnProcessId: "kaisya_get_agent_log",
    sourcePath: "",
    nsid: "com.etzhayyim.apps.kaisya.getAgentLog",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-kaisya-getAgentLog-v1",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // Timer-start BPMNs — process defs only
  for (const e of TIMER_ENTRIES) {
    const xml = readBpmn(e.file);
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${e.vertexId}, ${OWNER_DID}, ${e.bpmnProcessId}, 1, ${xml},
             CAST(${size} AS integer), ${e.sourcePath}, 'active', ${CREATED_AT},
             1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
      )
    `.execute(db);
  }

  // XRPC handlers — lexicon bindings (no BPMN XML, handled by pymagatama kaisya module)
  for (const e of XRPC_ENTRIES) {
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${e.bindingVertexId}, ${OWNER_DID}, ${e.nsid}, ${e.bpmnProcessId},
             1, CAST(30000 AS integer), NULL, 'active', ${CREATED_AT},
             1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of TIMER_ENTRIES) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);
  }
  for (const e of XRPC_ENTRIES) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVertexId}
    `.execute(db);
  }
}
