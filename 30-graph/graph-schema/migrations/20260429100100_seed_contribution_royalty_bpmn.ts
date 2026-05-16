import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604281400 Phase 2: register contributionRoyaltyDistribute timer-start BPMN
// (R/PT24H royalty credit sweep) so the F5 watcher deploys it to Zeebe.
// BPMN calls generic.db.select → contribution.distributeRoyalties → generic.audit.emit.
// No lexicon binding needed: process is timer-start, not XRPC-triggered.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-28T20:00:00Z";

const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contribution-royalty-distribute-v1";
const OWNER_DID = "did:web:bpmn.gftd.ai";
const BPMN_PROCESS_ID = "contribution_royalty_distribute";
const SOURCE_PATH =
  "00-contracts/bpmn/ai/gftd/contribution/contributionRoyaltyDistribute.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(SOURCE_PATH);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      owner_did,
      bpmn_process_id,
      version,
      xml,
      xml_byte_size,
      source_path,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${PROCESS_VERTEX_ID},
      ${OWNER_DID},
      ${BPMN_PROCESS_ID},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${SOURCE_PATH},
      'active',
      ${createdAt},
      1,
      ${OWNER_DID},
      ${OWNER_DID},
      'sys.bpmn.seed.contribution_royalty_distribute'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
  `.execute(db);
}
