import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T09:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

interface BpmnEntry {
  processId: string;
  bpmnPath: string;
  processVid: string;
  bindingVid: string;
  nsid: string;
}

const ENTRIES: BpmnEntry[] = [
  {
    processId: "graphSosIntel_inventoryTick",
    bpmnPath: "00-contracts/bpmn/ai/gftd/graph-sos-intel/inventory-tick.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-inventory-tick-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-inventory-tick-v1",
    nsid: "app.etzhayyim.apps.graphSosIntel.inventoryTick",
  },
  {
    processId: "graphSosIntel_briefingTick",
    bpmnPath: "00-contracts/bpmn/ai/gftd/graph-sos-intel/briefing-tick.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-briefing-tick-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-briefing-tick-v1",
    nsid: "app.etzhayyim.apps.graphSosIntel.briefingTick",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    const xml = readFileSync(path.resolve(repoRoot, e.bpmnPath), "utf8");
    const byteSize = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT
        ${e.processVid}, ${OWNER_DID}, ${e.processId}, 1,
        ${xml}, CAST(${byteSize} AS integer),
        ${e.bpmnPath}, 'active', ${CREATED_AT},
        1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.graph-sos-intel'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${e.processVid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, bpmn_process_id, nsid,
         created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT
        ${e.bindingVid}, ${OWNER_DID}, ${e.processId}, ${e.nsid},
        ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.graph-sos-intel'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVid}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${e.processVid}`.execute(db);
  }
}
