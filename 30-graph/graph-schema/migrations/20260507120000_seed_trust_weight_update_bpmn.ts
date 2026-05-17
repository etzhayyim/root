import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 Repo-as-Attractor — W_ij dynamic trust weight update BPMN seed.
// Timer-start R/PT1H: computes pairwise belief distance D(q_i, q_j) from
// mv_attractor_stability_by_agent and applies Bounded Confidence filter (ε=0.3).
// F5 watcher deploys to Zeebe within 30s of INSERT (ADR-0056).

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T11:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.wellbecoming";

const VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/wellbecoming-trust-weight-update-v1";
const SOURCE_PATH = "00-contracts/bpmn/ai/gftd/wellbecoming/trustWeightUpdate.bpmn";

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
    SELECT
      ${VERTEX_ID}, ${OWNER_DID}, ${"wellbecoming_trust_weight_update"}, 1,
      ${xml}, CAST(${size} AS integer), ${SOURCE_PATH}, 'active', ${CREATED_AT},
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
