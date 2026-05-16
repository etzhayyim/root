import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 3 causal attribution: link dispatched BPMN actions to subsequent
// Well-Becoming observations. Enables B-matrix learning from actual
// action→outcome transitions rather than correlational co-occurrence.
//
// vertex_rl_step.triggered_by_dispatch  — FK vertex_rl_aif_dispatch_log.vertex_id
// vertex_rl_aif_dispatch_log.outcome_step_id — FK vertex_rl_step.vertex_id

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_rl_step
      ADD COLUMN IF NOT EXISTS triggered_by_dispatch VARCHAR
  `.execute(db);

  await sql`
    ALTER TABLE vertex_rl_aif_dispatch_log
      ADD COLUMN IF NOT EXISTS outcome_step_id VARCHAR
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_dispatch_outcome
      ON vertex_rl_aif_dispatch_log (outcome_step_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_step_dispatch
      ON vertex_rl_step (triggered_by_dispatch)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN — migration is additive only.
}
