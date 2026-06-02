import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { file: string; processId: string; nsid: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:open-lei.etzhayyim.com";
const createdAt = "2026-04-30T12:00:00+09:00";
const actorId = "sys.bpmn.seed.open-lei";
const seeds: Seed[] = [
  {
    file: "registerOrgUnit",
    processId: "open_lei_register_org_unit",
    nsid: "com.etzhayyim.apps.openLei.registerOrgUnit",
    writeTableAllowlist: "vertex_org_unit,edge_org_unit_parent",
  },
  {
    file: "dissolveOrgUnit",
    processId: "open_lei_dissolve_org_unit",
    nsid: "com.etzhayyim.apps.openLei.dissolveOrgUnit",
    writeTableAllowlist: "vertex_org_unit",
  },
  {
    file: "moveOrgUnit",
    processId: "open_lei_move_org_unit",
    nsid: "com.etzhayyim.apps.openLei.moveOrgUnit",
    writeTableAllowlist: "vertex_org_unit,edge_org_unit_parent",
  },
  {
    file: "addOrgMember",
    processId: "open_lei_add_org_member",
    nsid: "com.etzhayyim.apps.openLei.addOrgMember",
    writeTableAllowlist: "edge_org_unit_member",
  },
  {
    file: "removeOrgMember",
    processId: "open_lei_remove_org_member",
    nsid: "com.etzhayyim.apps.openLei.removeOrgMember",
    writeTableAllowlist: "edge_org_unit_member",
  },
  {
    file: "queryOrgSubtree",
    processId: "open_lei_query_org_subtree",
    nsid: "com.etzhayyim.apps.openLei.queryOrgSubtree",
    writeTableAllowlist: "",
  },
];
const sourcePath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/open-lei/${s.file}.bpmn`;
const slug = (s: Seed) => s.file.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-lei-${slug(s)}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-lei-${slug(s)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1, ${xml}, CAST(${size} AS integer), ${sourcePath(s)},
             'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})`.execute(db);
    await sql`INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1, 30000, ${s.writeTableAllowlist},
             'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)})`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
