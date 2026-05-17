import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated balance + transfer log; no Tier-3 PII).

/**
 * karma.etzhayyim.com — Well-Becoming Token (WBT) settlement schema (Phase K1).
 *
 * Backs the rebirth.forfeit primitive. On rebirth the old organism's
 * WBT balance moves to the commons pool. WBT issuance / faucet
 * semantics deferred to Phase K6 (token economy).
 *
 * Tables (3 vertex + 2 streaming MV):
 *   vertex_karma_wbt_balance     one row per DID (current balance)
 *   vertex_karma_wbt_transfer    append-only transaction log (content-addressed PK)
 *   vertex_karma_commons_pool    singleton (vertex_id='commons-pool')
 *   mv_karma_wbt_top_balances    descending balance leaderboard (cached)
 *   mv_karma_wbt_recent_transfers last 30d transfers
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_wbt_balance (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      did varchar NOT NULL,
      balance double precision NOT NULL,
      last_tx_ts_ms bigint,
      last_tx_id varchar,
      total_inflow double precision,
      total_outflow double precision,
      tx_count bigint,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_wbt_transfer (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      transfer_id varchar NOT NULL,
      from_did varchar NOT NULL,
      to_did varchar NOT NULL,
      amount double precision NOT NULL,
      reason varchar NOT NULL,
      memo varchar,
      is_forfeit boolean,
      is_inflow boolean,
      ts_ms bigint NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_commons_pool (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      total_balance double precision NOT NULL,
      total_inflow double precision NOT NULL,
      forfeit_inflow_count bigint NOT NULL,
      tax_inflow_count bigint NOT NULL,
      last_inflow_ts_ms bigint,
      last_inflow_did varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_wbt_bal_did ON vertex_karma_wbt_balance (did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wbt_tx_from ON vertex_karma_wbt_transfer (from_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wbt_tx_to ON vertex_karma_wbt_transfer (to_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wbt_tx_ts ON vertex_karma_wbt_transfer (ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wbt_tx_forfeit ON vertex_karma_wbt_transfer (is_forfeit)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_wbt_top_balances AS
    SELECT did, balance, tx_count, last_tx_ts_ms
    FROM vertex_karma_wbt_balance
    WHERE balance > 0
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_wbt_recent_transfers AS
    SELECT
      transfer_id,
      from_did,
      to_did,
      amount,
      reason,
      is_forfeit,
      ts_ms
    FROM vertex_karma_wbt_transfer
    WHERE to_timestamp(ts_ms / 1000.0) > (now() - INTERVAL '30 days')
  `.execute(db);

  // RisingWave's INSERT ... SELECT does not bind current_date / now()
  // in literal positions (Failed to bind expression). Use static
  // ISO date / timestamp strings produced by the migration runner.
  const today = new Date().toISOString().slice(0, 10);
  const nowTs = new Date().toISOString().slice(0, 19).replace("T", " ");
  await sql`
    INSERT INTO vertex_karma_commons_pool (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      total_balance, total_inflow, forfeit_inflow_count, tax_inflow_count,
      last_inflow_ts_ms, last_inflow_did,
      created_at, org_id, user_id, actor_id
    )
    SELECT
      'commons-pool',
      CAST(NULL AS bigint),
      CAST(${today} AS date),
      1,
      'did:web:karma.etzhayyim.com:commons',
      0.0, 0.0, CAST(0 AS bigint), CAST(0 AS bigint),
      CAST(NULL AS bigint),
      CAST(NULL AS varchar),
      ${nowTs},
      'did:web:karma.etzhayyim.com:commons',
      'did:web:karma.etzhayyim.com:commons',
      'sys.commons.init'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_karma_commons_pool WHERE vertex_id = 'commons-pool'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_wbt_recent_transfers`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_wbt_top_balances`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_commons_pool`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_wbt_transfer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_wbt_balance`.execute(db);
}
