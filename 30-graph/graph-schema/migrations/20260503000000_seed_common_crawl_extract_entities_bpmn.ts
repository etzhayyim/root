import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Registers common_crawl_extract_entities BPMN actor (ADR-0056):
//   - R/PT1H timer-start: autonomous entity extraction from vertex_page rows
//   - none-start:         manual trigger via app.etzhayyim.apps.commonCrawl.extractEntities XRPC
//
// Task types handled by pymagatama:0.3.29 common_crawl.py:
//   commonCrawl.entities.extract — URL-regex fast-path + OpenRouter LLM fallback
//     Writes to domain state tables; marks processed pages with extracted_for_{domain} timestamp.
//     Domains: kuruma / media_anime / media_gamers / handotai
//
// source_path: 00-contracts/bpmn/ai/gftd/common-crawl/extractEntities.bpmn

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const createdAt = "2026-05-03T00:00:00Z";
const ownerDid = "did:web:bpmn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.common-crawl";

const BPMN_PROCESS_ID = "common_crawl_extract_entities";
const NSID = "app.etzhayyim.apps.commonCrawl.extractEntities";
const BPMN_FILE = "00-contracts/bpmn/ai/gftd/common-crawl/extractEntities.bpmn";

const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/common-crawl-extract-entities-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/common-crawl-extractEntities-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, BPMN_FILE), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${PROCESS_VERTEX_ID}, ${ownerDid}, ${BPMN_PROCESS_ID}, 1,
      ${xml}, CAST(${size} AS integer), ${BPMN_FILE}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${BINDING_VERTEX_ID}, ${ownerDid}, ${NSID}, ${BPMN_PROCESS_ID}, 1,
      CAST(120000 AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def SET status = 'inactive'
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
  await sql`
    UPDATE vertex_bpmn_lexicon_binding SET status = 'inactive'
    WHERE nsid = ${NSID}
  `.execute(db);
}
