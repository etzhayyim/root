import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:apps.etzhayyim.com";
const createdAt = "2026-04-30T21:57:00+09:00";
const actorId = "sys.bpmn.seed.apps-directory";
const writeTableAllowlist = [
  "vertex_apps_directory_listing",
  "vertex_apps_directory_feature",
  "vertex_apps_directory_install_intent",
  "edge_apps_directory_listing_feature",
  "edge_apps_directory_listing_install_intent",
].join(",");

const seeds: Seed[] = [
  { slug: "register-app-listing", op: "registerAppListing", processId: "apps_directory_register_app_listing", writeTableAllowlist },
  { slug: "update-app-listing", op: "updateAppListing", processId: "apps_directory_update_app_listing", writeTableAllowlist },
  { slug: "list-apps", op: "listApps", processId: "apps_directory_list_apps", writeTableAllowlist: "" },
  { slug: "get-app-listing", op: "getAppListing", processId: "apps_directory_get_app_listing", writeTableAllowlist: "" },
  { slug: "feature-app", op: "featureApp", processId: "apps_directory_feature_app", writeTableAllowlist },
  { slug: "record-install-intent", op: "recordInstallIntent", processId: "apps_directory_record_install_intent", writeTableAllowlist },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/appsDirectory/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-${s.slug}-v1`;

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
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
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
        ${bindingVertexId(s)}, ${ownerDid}, ${`com.etzhayyim.apps.apps.${s.op}`}, ${s.processId}, 1,
        30000, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
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
