import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for Phase 1 RL preference pair generation BPMN.
// F5 watcher deploys to Zeebe within 30s of INSERT (ADR-0056).
// Also seeds vertex_bpmn_lexicon_binding for the rl.generate.preferences task.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-06T21:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-generate-preferences-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-generate-preferences-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/rl/rlGeneratePreferences.bpmn"),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VERTEX_ID}, ${OWNER_DID}, 'rl_generate_preferences', 1,
      ${xml}, CAST(${size} AS integer),
      '00-contracts/bpmn/ai/gftd/rl/rlGeneratePreferences.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VERTEX_ID}, ${OWNER_DID}, 'rl_generate_preferences',
      'app.etzhayyim.apps.rl.generatePreferences',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}`.execute(db);
}
