import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const sourcePath = "00-contracts/bpmn/com/etzhayyim/flight-offer/checkPriceDrop.bpmn";
const xml = () => readFileSync(path.resolve(repoRoot, sourcePath), "utf8");

const processVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/flight-offer-check-price-drop-v1";
const bindingVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/flight-offer-check-price-drop-v1";
const ownerDid = "did:web:flight-offer.etzhayyim.com";
const createdAt = "2026-04-27T12:02:00Z";
const actorTag = "sys.bpmn.seed.flight-offer";

export async function up(db: Kysely<unknown>): Promise<void> {
  const body = xml();
  const size = Buffer.byteLength(body, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${processVertexId}, ${ownerDid}, 'flight_offer_check_price_drop',
           1, ${body}, CAST(${size} AS integer), ${sourcePath}, 'active',
           ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${bindingVertexId}, ${ownerDid}, 'com.etzhayyim.apps.flightOffer.checkPriceDrop',
           'flight_offer_check_price_drop', 1, CAST(15000 AS integer), 'active',
           ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
