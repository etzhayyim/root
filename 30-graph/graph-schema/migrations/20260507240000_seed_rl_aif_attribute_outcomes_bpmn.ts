import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for Phase 3
// AIF causal attribution BPMN (ADR-2605061200, ADR-0056).
// Closes the RL feedback loop: dispatched actions -> outcome steps.
// F5 watcher deploys to Zeebe within 30s of INSERT.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T23:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

const PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-aif-attribute-outcomes-v1";
const BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-attribute-outcomes-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/rl/rlAifAttributeOutcomes.bpmn"),
    "utf8",
  );
  const byteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VID}, ${OWNER_DID}, 'rl_aif_attribute_outcomes', 1,
      ${xml}, CAST(${byteSize} AS integer),
      '00-contracts/bpmn/ai/gftd/rl/rlAifAttributeOutcomes.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VID}, ${OWNER_DID}, 'rl_aif_attribute_outcomes',
      'app.etzhayyim.apps.rl.aifAttributeOutcomes',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
