import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seeds vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for
// commonCrawl.extractEntities (ADR-0056 BPMN-as-actor pattern).
//
// R/PT1H timer-start: commonCrawl.entities.extract Zeebe task for all
// 4 domains (kuruma, media_anime, media_gamers, handotai).
// CF Worker refactored to L3 Dispatcher facade (proxyToBpmn).
// F5 watcher picks up status='active' and deploys extractEntities.bpmn to
// Zeebe within 30s.

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);
const repoRoot   = path.resolve(__dirname, "..", "..", "..");

const ownerDid  = "did:web:bpmn.etzhayyim.com";
const actorId   = "did:web:commoncrawl.etzhayyim.com";
const createdAt = "2026-05-03T10:00:00Z";

const PROCESS_ID  = "common_crawl_extract_entities";
const NSID        = "ai.gftd.apps.commonCrawl.extractEntities";
const BPMN_PATH   = "00-contracts/bpmn/ai/gftd/common-crawl/extractEntities.bpmn";
const PROCESS_VID = `at://${actorId}/ai.gftd.apps.bpmn.processDef/common-crawl-extract-entities-v1`;
const BINDING_VID = `at://${actorId}/ai.gftd.apps.bpmn.binding/common-crawl-extract-entities-v1`;

const BPMN_FILE = path.resolve(repoRoot, BPMN_PATH);

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml  = readFileSync(BPMN_FILE, "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord,
      org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${PROCESS_VID}, ${ownerDid}, ${PROCESS_ID}, 1,
      ${xml}, CAST(${size} AS integer), ${BPMN_PATH}, 'active',
      ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id,
      status, created_at, sensitivity_ord,
      org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${BINDING_VID}, ${ownerDid}, ${NSID}, ${PROCESS_ID},
      'active', ${createdAt}, 100,
      ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
