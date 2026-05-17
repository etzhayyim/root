import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated bundler interaction log).

/**
 * karma.etzhayyim.com — ERC-4337 user operation log (Phase K3).
 *
 * Audit trail for ERC-4337 user operations submitted to the bundler.
 * Backs the karma.anchor.submitTx primitive when wired to a real
 * Base L2 bundler (Stackup / Pimlico / self-hosted). One row per
 * UserOperation submission attempt.
 *
 * Tables (1 vertex + 1 streaming MV):
 *   vertex_karma_user_op_log         per-userOp submission record
 *   mv_karma_user_op_recent          last 24h ops by status
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_user_op_log (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      op_id varchar NOT NULL,
      sender_address varchar NOT NULL,
      nonce bigint NOT NULL,
      calldata_hash varchar,
      paymaster_address varchar,
      bundler_endpoint varchar,
      anchor_id varchar,
      merkle_root varchar,
      sent_at varchar,
      sent_at_ms bigint,
      status varchar NOT NULL,
      user_op_hash varchar,
      included_tx_hash varchar,
      included_block_number bigint,
      gas_used bigint,
      paymaster_paid_wei varchar,
      error_code varchar,
      error_message varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_uop_status ON vertex_karma_user_op_log (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_uop_anchor ON vertex_karma_user_op_log (anchor_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_uop_sender ON vertex_karma_user_op_log (sender_address)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_uop_sent_at ON vertex_karma_user_op_log (sent_at_ms)`.execute(db);

  // Recent (24h window) ops bounded by submit rate.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_user_op_recent AS
    SELECT
      op_id,
      sender_address,
      anchor_id,
      status,
      user_op_hash,
      included_tx_hash,
      sent_at_ms
    FROM vertex_karma_user_op_log
    WHERE to_timestamp(sent_at_ms / 1000.0) > (now() - INTERVAL '24 hours')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_user_op_recent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_user_op_log`.execute(db);
}
