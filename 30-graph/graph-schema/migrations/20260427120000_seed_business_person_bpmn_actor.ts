import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T12:00:00Z";
const ownerDid = "did:web:business-person.etzhayyim.com";
const actorTag = "sys.bpmn.seed.business-person";
const processVertexId = "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-collectPublicRoles-v1";
const bindingVertexId = "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/businessPerson-collectPublicRoles-v1";
const bpmnProcessId = "business_person_collect_public_roles";
const nsid = "ai.gftd.apps.businessPerson.collectPublicRoles";
const sourcePath = "00-contracts/bpmn/ai/gftd/business-person/collectPublicRoles.bpmn";

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 2, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, write_table_allowlist
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      300000, 'active', ${createdAt}, 2, ${ownerDid}, ${ownerDid},
      ${actorTag}, ${"vertex_business_person"}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
