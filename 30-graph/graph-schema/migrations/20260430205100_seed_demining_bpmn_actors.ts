import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:dm1nactz.etzhayyim.com";
const createdAt = "2026-04-30T20:51:00+09:00";
const actorId = "sys.bpmn.seed.demining";

const seeds: Seed[] = [
  { slug: "register-hazard-area", op: "registerHazardArea", processId: "demining_register_hazard_area", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit" },
  { slug: "list-hazard-areas", op: "listHazardAreas", processId: "demining_list_hazard_areas", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "record-detection", op: "recordDetection", processId: "demining_record_detection", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit" },
  { slug: "record-clearance-task", op: "recordClearanceTask", processId: "demining_record_clearance_task", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit" },
  { slug: "release-area", op: "releaseArea", processId: "demining_release_area", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit" },
  { slug: "record-eore-session", op: "recordEoreSession", processId: "demining_record_eore_session", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public" },
  { slug: "record-victim", op: "recordVictim", processId: "demining_record_victim", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/demining/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/demining-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/demining-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 300, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.demining.${s.op}`}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        300, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
