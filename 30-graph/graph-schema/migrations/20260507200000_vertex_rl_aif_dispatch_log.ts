import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 2 RL policy dispatch log.
// Records every ε-greedy action sample + bpmn-dispatcher outcome.
// Written by rl_policy.task_rl_policy_dispatch (R/PT1H).

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_rl_aif_dispatch_log (
      vertex_id                VARCHAR PRIMARY KEY,  -- 'aif:dispatch:{actor_did}:{dispatched_at}'

      actor_did                VARCHAR NOT NULL,
      action_nsid              VARCHAR NOT NULL,     -- sampled action (BPMN NSID)
      dispatched_at            TIMESTAMP NOT NULL,

      free_energy_at_dispatch  DOUBLE PRECISION,     -- EFE total at time of dispatch (nullable if no data)
      epsilon                  DOUBLE PRECISION NOT NULL,
      was_exploration          BOOLEAN NOT NULL,     -- true = ε random, false = policy weighted
      dispatch_ok              BOOLEAN NOT NULL,
      dispatch_error           VARCHAR,              -- empty string if ok

      sensitivity_ord          INTEGER DEFAULT 1,
      owner_did                VARCHAR,
      org_id                   VARCHAR,
      user_id                  VARCHAR,
      actor_id                 VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_dispatch_actor
      ON vertex_rl_aif_dispatch_log (actor_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_dispatch_at
      ON vertex_rl_aif_dispatch_log (dispatched_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_rl_aif_dispatch_log`.execute(db);
}
