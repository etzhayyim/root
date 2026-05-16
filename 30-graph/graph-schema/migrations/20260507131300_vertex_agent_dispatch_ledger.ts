import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_dispatch_ledger (
      vertex_id              VARCHAR PRIMARY KEY,
      agent_did              VARCHAR NOT NULL,
      dispatch_plan_id       VARCHAR NOT NULL,
      realworld_effect_id    VARCHAR,
      channel                VARCHAR NOT NULL,
      task_type              VARCHAR,
      payload_hash           VARCHAR NOT NULL,
      authority_ref          VARCHAR NOT NULL,
      policy_ref             VARCHAR NOT NULL,
      dispatch_state         VARCHAR NOT NULL,
      created_at             VARCHAR NOT NULL,
      updated_at             VARCHAR NOT NULL,
      sensitivity_ord        BIGINT DEFAULT 1,
      actor_id               VARCHAR,
      owner_did              VARCHAR,
      org_id                 VARCHAR,
      user_id                VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dispatch_ledger_agent_time ON vertex_agent_dispatch_ledger (agent_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dispatch_ledger_state ON vertex_agent_dispatch_ledger (dispatch_state, updated_at)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_agent_dispatch_ledger`.execute(db);
}
