import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for 4 additional wellbecoming BPMN processes
// (ADR-2604291800): detectBottleneck / proactiveConnect / floorViolationAlert
// / agentLoop. F5 watcher deploys each to Zeebe within 30s.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..", "..");
const readBpmn = (file: string) =>
  readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/com/etzhayyim/wellbecoming", file),
    "utf8",
  );

const CREATED_AT = "2026-04-29T23:10:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.wellbecoming";

const TIMER_ENTRIES = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-detect-bottleneck-v1",
    bpmnProcessId: "wellbecoming_detect_bottleneck",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/wellbecoming/detectBottleneck.bpmn",
    file: "detectBottleneck.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-proactive-connect-v1",
    bpmnProcessId: "wellbecoming_proactive_connect",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/wellbecoming/proactiveConnect.bpmn",
    file: "proactiveConnect.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-floor-violation-alert-v1",
    bpmnProcessId: "wellbecoming_floor_violation_alert",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/wellbecoming/floorViolationAlert.bpmn",
    file: "floorViolationAlert.bpmn",
  },
];

// agentLoop is XRPC-triggered (none-start) — needs a lexicon binding too.
const XRPC_ENTRY = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-agent-loop-v1",
  bpmnProcessId: "wellbecoming_agent_loop",
  sourcePath: "00-contracts/bpmn/com/etzhayyim/wellbecoming/agentLoop.bpmn",
  file: "agentLoop.bpmn",
  nsid: "com.etzhayyim.apps.wellbecoming.agentLoop",
};

export async function up(db: Kysely<unknown>): Promise<void> {
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

  // agentLoop process def
  const agentXml = readBpmn(XRPC_ENTRY.file);
  const agentSize = Buffer.byteLength(agentXml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${XRPC_ENTRY.vertexId}, ${OWNER_DID}, ${XRPC_ENTRY.bpmnProcessId}, 1, ${agentXml},
           CAST(${agentSize} AS integer), ${XRPC_ENTRY.sourcePath}, 'active', ${CREATED_AT},
           1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${XRPC_ENTRY.vertexId}
    )
  `.execute(db);

  // agentLoop lexicon binding
  const bindingVertexId = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-wellbecoming-agentLoop-v1";
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${bindingVertexId}, ${OWNER_DID}, ${XRPC_ENTRY.nsid}, ${XRPC_ENTRY.bpmnProcessId},
           1, CAST(120000 AS integer), NULL, 'active', ${CREATED_AT},
           1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  const allIds = [
    ...TIMER_ENTRIES.map((e) => e.vertexId),
    XRPC_ENTRY.vertexId,
  ];
  for (const vertexId of allIds) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}
    `.execute(db);
  }
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding
    WHERE nsid = ${XRPC_ENTRY.nsid}
  `.execute(db);
}
