import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 F — seeds BPMN actor rows for ξ stochastic noise injection (OU process).

const PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/wellbecoming-belief-noise-inject-v1";
const BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/wellbecoming-belief-noise-inject-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, bpmn_process_id, version, xml,
       sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VID},
      'wellbecoming_belief_noise_inject',
      1, '',
      1, '', '', 'sys.bpmn.wellbecoming'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, nsid, bpmn_process_id,
       sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VID},
      'app.etzhayyim.apps.wellbecoming.beliefNoiseInject',
      'wellbecoming_belief_noise_inject',
      1, '', '', 'sys.bpmn.wellbecoming'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(
    db,
  );
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
