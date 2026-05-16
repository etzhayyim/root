import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_counterparty_model (
      vertex_id VARCHAR PRIMARY KEY,
      agent_did VARCHAR NOT NULL,
      counterparty_ref VARCHAR NOT NULL,
      model_kind VARCHAR NOT NULL,
      prior_preferences_json VARCHAR NOT NULL,
      protected_assets_json VARCHAR NOT NULL,
      confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      sensitivity_ord BIGINT DEFAULT 1,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_protected_asset (
      vertex_id VARCHAR PRIMARY KEY,
      agent_did VARCHAR NOT NULL,
      counterparty_ref VARCHAR NOT NULL,
      asset_ref VARCHAR NOT NULL,
      asset_kind VARCHAR NOT NULL,
      protected_state_json VARCHAR NOT NULL,
      violation_cost DOUBLE PRECISION NOT NULL DEFAULT 1.0,
      reversibility_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      sensitivity_ord BIGINT DEFAULT 1,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_agent_counterparty_protects_asset (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_minimax_evaluation (
      vertex_id VARCHAR PRIMARY KEY,
      agent_did VARCHAR NOT NULL,
      action_id VARCHAR NOT NULL,
      counterparty_ref VARCHAR NOT NULL,
      payoff_matrix_json VARCHAR NOT NULL,
      worst_case_utility DOUBLE PRECISION NOT NULL,
      minimax_regret DOUBLE PRECISION NOT NULL,
      protected_asset_violation DOUBLE PRECISION NOT NULL,
      selected_response VARCHAR,
      evaluation_state VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      sensitivity_ord BIGINT DEFAULT 1,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_agent_counterparty_model_agent ON vertex_agent_counterparty_model (agent_did, counterparty_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_protected_asset_counterparty ON vertex_agent_protected_asset (agent_did, counterparty_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_counterparty_asset_src ON edge_agent_counterparty_protects_asset (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_minimax_agent_time ON vertex_agent_minimax_evaluation (agent_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_minimax_counterparty ON vertex_agent_minimax_evaluation (counterparty_ref, evaluation_state)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_agent_minimax_evaluation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_agent_counterparty_protects_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_protected_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_counterparty_model`.execute(db);
}
