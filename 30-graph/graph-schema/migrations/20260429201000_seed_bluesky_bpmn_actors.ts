import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const ownerDid = "did:web:bluesky.gftd.ai";
const createdAt = "2026-04-29T20:10:00+09:00";
const actorId = "sys.bpmn.seed.bluesky";
const writeTableAllowlist = [
  "vertex_bluesky_profile",
  "vertex_bluesky_post",
  "vertex_bluesky_opt_out",
  "vertex_bluesky_tombstone",
].join(",");

const seeds = [
  {
    slug: "bluesky-ingest-actor",
    sourcePath: "00-contracts/bpmn/ai/gftd/bluesky/ingestActor.bpmn",
    processId: "bluesky_ingest_actor",
    nsid: "ai.gftd.apps.bluesky.ingestActor",
    timeoutMs: 120000,
  },
  {
    slug: "bluesky-refresh-stalest",
    sourcePath: "00-contracts/bpmn/ai/gftd/bluesky/refreshStalest.bpmn",
    processId: "bluesky_refresh_stalest",
    nsid: "ai.gftd.apps.bluesky.refreshStalest",
    timeoutMs: 300000,
  },
] as const;

function processVertexId(seed: (typeof seeds)[number]): string {
  return `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${seed.slug}-v1`;
}

function bindingVertexId(seed: (typeof seeds)[number]): string {
  return `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${seed.slug}-v1`;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, seed.sourcePath), "utf8");
    const xmlByteSize = Buffer.byteLength(xml, "utf8");
    const pVid = processVertexId(seed);
    const bVid = bindingVertexId(seed);

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${pVid}, ${ownerDid}, ${seed.processId}, 1, ${xml}, CAST(${xmlByteSize} AS integer),
        ${seed.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${pVid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bVid}, ${ownerDid}, ${seed.nsid}, ${seed.processId}, 1,
        CAST(${seed.timeoutMs} AS integer), ${writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bVid}
      )
    `.execute(db);

    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET write_table_allowlist = ${writeTableAllowlist}
      WHERE bpmn_process_id = ${seed.processId}
        AND nsid = ${seed.nsid}
        AND (write_table_allowlist IS NULL OR write_table_allowlist <> ${writeTableAllowlist})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}`.execute(db);
  }
}
