import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for 4 ARIA protocol BPMN processes.
// F5 watcher deploys each to Zeebe within 30s of INSERT.
// ADR-0056 BPMN-as-actor: INSERT rows → automatic Zeebe deploy.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readBpmn = (file: string) =>
  readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/aria", file),
    "utf8",
  );

const CREATED_AT = "2026-05-01T19:50:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.aria";

const ENTRIES = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-attention-ingest-v1",
    bpmnProcessId: "aria_attention_ingest",
    sourcePath: "00-contracts/bpmn/ai/gftd/aria/attentionIngest.bpmn",
    file: "attentionIngest.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-request-ingest-v1",
    bpmnProcessId: "aria_request_ingest",
    sourcePath: "00-contracts/bpmn/ai/gftd/aria/requestIngest.bpmn",
    file: "requestIngest.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-money-flow-ingest-v1",
    bpmnProcessId: "aria_money_flow_ingest",
    sourcePath: "00-contracts/bpmn/ai/gftd/aria/moneyFlowIngest.bpmn",
    file: "moneyFlowIngest.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-minimax-sweep-v1",
    bpmnProcessId: "aria_minimax_sweep",
    sourcePath: "00-contracts/bpmn/ai/gftd/aria/ariaMinimaxSweep.bpmn",
    file: "ariaMinimaxSweep.bpmn",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
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
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);
  }
}
