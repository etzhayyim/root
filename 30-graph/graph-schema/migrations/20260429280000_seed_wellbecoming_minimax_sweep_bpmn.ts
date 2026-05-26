import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for wellbecoming minimaxSweep BPMN.
// Timer-start R/PT5M: runs every 5 minutes, picks the worst-separation-delta
// callers and runs the LangGraph minimax loop (batch_size=3).
// ADR-2604291800 §minimax-persistent-loop.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-04-29T23:50:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.wellbecoming";

const VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/wellbecoming-minimax-sweep-v1";
const BPMN_PROCESS_ID = "wellbecoming_minimax_sweep";
const SOURCE_PATH =
  "00-contracts/bpmn/ai/gftd/wellbecoming/minimaxSweep.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, SOURCE_PATH),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${VERTEX_ID}, ${OWNER_DID}, ${BPMN_PROCESS_ID}, 1, ${xml},
           CAST(${size} AS integer), ${SOURCE_PATH}, 'active', ${CREATED_AT},
           1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${VERTEX_ID}
  `.execute(db);
}
