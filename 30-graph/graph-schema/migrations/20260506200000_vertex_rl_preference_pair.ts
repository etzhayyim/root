import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 1 RL preference pair table — ADR-2604291800 Well-Becoming DPO dataset.
//
// vertex_rl_preference_pair:  cross-actor (chosen, rejected) pairs for DPO fine-tuning.
//   Pairing strategy: same action_nsid, different actor_did,
//   reward_scalar(chosen) - reward_scalar(rejected) >= delta_threshold.
//
// Generated daily by rl_generate_preferences BPMN (R/P1D) once total step count
// exceeds min_steps (default 50).

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_rl_preference_pair (
      vertex_id          VARCHAR PRIMARY KEY,   -- 'rl:pair:{sorted step ids}'
      _seq               BIGINT,
      created_date       DATE,

      -- The inference action type that produced both steps
      action_nsid        VARCHAR NOT NULL,

      -- Step references
      chosen_step_id     VARCHAR NOT NULL,      -- FK vertex_rl_step.vertex_id (higher reward)
      rejected_step_id   VARCHAR NOT NULL,      -- FK vertex_rl_step.vertex_id (lower reward)

      -- Actor provenance
      chosen_actor_did   VARCHAR NOT NULL,
      rejected_actor_did VARCHAR NOT NULL,

      -- Reward signal
      chosen_reward      DOUBLE PRECISION NOT NULL,
      rejected_reward    DOUBLE PRECISION NOT NULL,
      reward_delta       DOUBLE PRECISION NOT NULL,  -- chosen - rejected

      -- Pairing metadata
      pairing_strategy   VARCHAR DEFAULT 'cross_actor_reward_delta',
      dataset_version    VARCHAR DEFAULT 'v1',

      -- RLS
      sensitivity_ord    INTEGER DEFAULT 1,
      owner_did          VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,

      created_at         TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_pair_action
      ON vertex_rl_preference_pair (action_nsid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_pair_chosen_actor
      ON vertex_rl_preference_pair (chosen_actor_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_rl_pair_created
      ON vertex_rl_preference_pair (created_at)
  `.execute(db);

  // Rolling pair stats per action_nsid — bounded cardinality (~10s of distinct action types).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rl_pair_stats AS
    SELECT
      action_nsid,
      COUNT(*)                         AS total_pairs,
      AVG(reward_delta)                AS mean_delta,
      MIN(reward_delta)                AS min_delta,
      MAX(reward_delta)                AS max_delta,
      COUNT(DISTINCT chosen_actor_did) AS distinct_chosen_actors,
      MAX(created_at)                  AS last_pair_at
    FROM vertex_rl_preference_pair
    GROUP BY action_nsid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_rl_pair_stats`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_rl_preference_pair`.execute(db);
}
