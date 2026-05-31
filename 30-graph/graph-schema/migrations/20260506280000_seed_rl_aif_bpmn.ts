import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for Phase 1B
// Active Inference BPMNs (ADR-2604291800, ADR-0056).
// F5 watcher deploys to Zeebe within 30s of INSERT (ADR-0056).

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-06T23:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

// ─── Belief Update (R/PT1H) ──────────────────────────────────────────────────

const BELIEF_PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-aif-belief-update-v1";
const BELIEF_BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-belief-update-v1";

// ─── Learn Model (R/P1D) ─────────────────────────────────────────────────────

const LEARN_PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-aif-learn-model-v1";
const LEARN_BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-learn-model-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── belief update BPMN ──────────────────────────────────────────────────────
  const beliefXml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/rl/rlAifBeliefUpdate.bpmn"),
    "utf8",
  );
  const beliefSize = Buffer.byteLength(beliefXml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BELIEF_PROCESS_VID}, ${OWNER_DID}, 'rl_aif_belief_update', 1,
      ${beliefXml}, CAST(${beliefSize} AS integer),
      '00-contracts/bpmn/ai/gftd/rl/rlAifBeliefUpdate.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${BELIEF_PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BELIEF_BINDING_VID}, ${OWNER_DID}, 'rl_aif_belief_update',
      'app.etzhayyim.apps.rl.aifUpdateBeliefs',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BELIEF_BINDING_VID}
    )
  `.execute(db);

  // ── learn model BPMN ────────────────────────────────────────────────────────
  const learnXml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/rl/rlAifLearnModel.bpmn"),
    "utf8",
  );
  const learnSize = Buffer.byteLength(learnXml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${LEARN_PROCESS_VID}, ${OWNER_DID}, 'rl_aif_learn_model', 1,
      ${learnXml}, CAST(${learnSize} AS integer),
      '00-contracts/bpmn/ai/gftd/rl/rlAifLearnModel.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${LEARN_PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${LEARN_BINDING_VID}, ${OWNER_DID}, 'rl_aif_learn_model',
      'app.etzhayyim.apps.rl.aifLearnModel',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${LEARN_BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${LEARN_BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${LEARN_PROCESS_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BELIEF_BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${BELIEF_PROCESS_VID}`.execute(db);
}
