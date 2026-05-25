import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:coverage.etzhayyim.com";
const createdAt = "2026-04-29T22:02:00+09:00";
const actorId = "sys.bpmn.seed.coverage";

const processVertexId = "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/coverage-gap-bridge-v1";
const bindingVertexId = "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/coverage-coverageGapBridge-v1";
const sourcePath = "00-contracts/bpmn/ai/gftd/coverage/coverageGapBridge.bpmn";
const processId = "coverage_gap_bridge";
const nsid = "app.etzhayyim.apps.coverage.coverageGapBridge";
const timeoutMs = 900_000;
const writeTableAllowlist =
  "vertex_coverage_recipe,vertex_crypto_asset_freeze,vertex_rare_earth_coverage," +
  "vertex_coverage_infer_entity,vertex_business_person";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
      actor_did, org_did
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${processId}, 1,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, write_table_allowlist, status, created_at,
      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${processId}, 1,
      CAST(${timeoutMs} AS integer), ${writeTableAllowlist}, 'active', ${createdAt},
      1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
