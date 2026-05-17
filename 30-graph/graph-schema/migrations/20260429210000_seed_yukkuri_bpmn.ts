import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0056: register yukkuriCompose BPMN so the F5 watcher deploys it to Zeebe.
// XRPC-triggered pipeline: scene.persist → voice.synthesize → image.generate
// → video.assemble → critic.review → audit.emit.
// Lexicon binding: ai.gftd.apps.yukkuri.composeVideo → yukkuri_compose process.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-29T20:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yukkuri-compose-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/yukkuri-compose-v1";
const BPMN_PROCESS_ID = "yukkuri_compose";
const SOURCE_PATH = "00-contracts/bpmn/ai/gftd/yukkuri/yukkuriCompose.bpmn";
const NSID = "ai.gftd.apps.yukkuri.composeVideo";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(SOURCE_PATH);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${PROCESS_VERTEX_ID}, ${OWNER_DID}, ${BPMN_PROCESS_ID},
      1, ${xml}, CAST(${xmlByteSize} AS integer),
      ${SOURCE_PATH}, 'active', ${createdAt}, 1,
      ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.yukkuri_compose'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  // Lexicon binding: XRPC NSID → BPMN process.
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id,
      status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${BINDING_VERTEX_ID}, ${OWNER_DID}, ${NSID}, ${BPMN_PROCESS_ID},
      'active', ${createdAt}, 1,
      ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.yukkuri_compose'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}`.execute(db);
}
