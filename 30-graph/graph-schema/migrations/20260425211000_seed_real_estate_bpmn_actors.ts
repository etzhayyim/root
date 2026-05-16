import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Entry = { proc: string; bpmnProcessId: string; timeoutMs: number; writeTable: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:real-estate.gftd.ai:ops";
const createdAt = "2026-04-25T21:10:00Z";
const actorTag = "sys.bpmn.seed.real-estate";
const entries: Entry[] = [
  { proc: "registerProperty", bpmnProcessId: "real_estate_register_property", timeoutMs: 20000, writeTable: "vertex_real_estate_property" },
  { proc: "publishListing", bpmnProcessId: "real_estate_publish_listing", timeoutMs: 20000, writeTable: "vertex_real_estate_listing" },
  { proc: "recordTransaction", bpmnProcessId: "real_estate_record_transaction", timeoutMs: 20000, writeTable: "vertex_real_estate_transaction" },
  { proc: "registerSource", bpmnProcessId: "real_estate_register_source", timeoutMs: 15000, writeTable: "vertex_real_estate_source" },
];

const kebab = (s: string) => s.replace(/([A-Z])/g, "-$1").toLowerCase();

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of entries) {
    const sourcePath = `00-contracts/bpmn/ai/gftd/real-estate/${e.proc}.bpmn`;
    const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
    const processVertexId = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-${kebab(e.proc)}-v1`;
    const bindingVertexId = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-${kebab(e.proc)}-v1`;
    await sql`
      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${processVertexId}, ${ownerDid}, ${e.bpmnProcessId}, 1, ${xml}, CAST(${Buffer.byteLength(xml, "utf8")} AS integer), ${sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId})
    `.execute(db);
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${bindingVertexId}, ${ownerDid}, ${`ai.gftd.apps.realEstate.${e.proc}`}, ${e.bpmnProcessId}, 1, CAST(${e.timeoutMs} AS integer), ${e.writeTable}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of entries) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${`at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-${kebab(e.proc)}-v1`}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${`at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-${kebab(e.proc)}-v1`}`.execute(db);
  }
}
