import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Activate llm_classifier_gate_pattern BPMN (was status='draft', Camunda 7 syntax).
//
// Changes applied:
// 1. BPMN rewritten to Zeebe 8.5: businessRuleTask now uses
//    zeebe:calledDecision decisionId="llm_classifier_gate" resultVariable="gateResult".
//    Non-standard etzhayyim:*/camunda:* attributes removed. retries="0" on service tasks.
//    BPMN status → 'active' + deployed_at cleared so F5 watcher redeploys.
//
// 2. DMN llm_classifier_gate inserted into vertex_bpmn_process_def (same table as BPMN —
//    the dispatcher's _detect_resource_kind() branches on DMN namespace in the XML).
//    deployed_at=NULL → F5 watcher deploys DMN to Zeebe alongside the BPMN.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const BPMN_PROCESS_ID = "llm_classifier_gate_pattern";
const BPMN_FILE = path.resolve(
  repoRoot,
  "00-contracts/bpmn/com/etzhayyim/llm/classifierGatePattern.bpmn",
);

const DMN_DECISION_ID = "llm_classifier_gate";
const DMN_FILE = path.resolve(
  repoRoot,
  "00-contracts/dmn/com/etzhayyim/llm/classifierGate.dmn",
);

export async function up(db: Kysely<unknown>): Promise<void> {
  const bpmnXml = readFileSync(BPMN_FILE, "utf8");
  const bpmnSize = Buffer.byteLength(bpmnXml, "utf8");

  const dmnXml = readFileSync(DMN_FILE, "utf8");
  const dmnSize = Buffer.byteLength(dmnXml, "utf8");

  // Update BPMN row: fixed XML + clear deployed_at so F5 watcher redeploys
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml"              = ${bpmnXml},
        xml_byte_size      = CAST(${bpmnSize} AS integer),
        status             = 'active',
        deployed_at        = NULL,
        deployed_zeebe_key = NULL
    WHERE bpmn_process_id  = ${BPMN_PROCESS_ID}
  `.execute(db);

  // Insert DMN into vertex_bpmn_process_def.
  // The dispatcher's _detect_resource_kind() reads the DMN namespace from the XML
  // to branch deploy logic; bpmn_process_id holds the decision ID for DMN rows.
  const dmnVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${DMN_DECISION_ID}-v1`;
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      bpmn_process_id,
      version,
      "xml",
      xml_byte_size,
      source_path,
      status,
      deployed_at,
      deployed_zeebe_key
    ) VALUES (
      ${dmnVertexId},
      ${DMN_DECISION_ID},
      1,
      ${dmnXml},
      CAST(${dmnSize} AS integer),
      '00-contracts/dmn/com/etzhayyim/llm/classifierGate.dmn',
      'active',
      NULL,
      NULL
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'draft'
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);

  await sql`
    DELETE FROM vertex_bpmn_process_def
    WHERE bpmn_process_id = ${DMN_DECISION_ID}
  `.execute(db);
}
