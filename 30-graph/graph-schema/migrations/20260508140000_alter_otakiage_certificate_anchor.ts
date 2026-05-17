import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * otakiage.etzhayyim.com Phase 2b1 — ERC725 certificate anchor schema
 * (ADR-2605081700 + ADR-0074 ERC725 root identity + ADR-2604261830).
 *
 * ALTER vertex_otakiage_certificate to add anchor tracking columns.
 * Phase 2b1 = state tracking only; Phase 2b2 = real on-chain calls
 * via ethers/viem from a sidecar primitive.
 *
 * Added columns:
 *   anchor_chain        varchar  base|base-sepolia|polygon|polygon-amoy
 *   anchor_contract     varchar  ERC725 anchor contract address (0x...)
 *   anchor_status       varchar  pending|queued|submitted|anchored|failed
 *   anchor_tx_hash      varchar  on-chain tx hash (anchored 状態時)
 *   anchor_block_number bigint   block height (anchored 状態時)
 *   anchored_at         varchar  ISO 8601 timestamp
 *   content_hash        varchar  sha256(certificate_json) — token URI base
 *   failure_reason      varchar  failed 状態時の reason
 *
 * Note: anchor_token_id was already declared in
 *   20260508120000_vertex_otakiage_schema.ts so we don't re-add it.
 *
 * MV (1 new):
 *   mv_otakiage_anchor_status  status 別件数 (soak monitor 用)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Add columns one-at-a-time so partial application leaves the DB in
  // a recoverable state if RisingWave hits a transient SlowDown.
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchor_chain varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchor_contract varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchor_status varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchor_tx_hash varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchor_block_number bigint`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN anchored_at varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN content_hash varchar`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate ADD COLUMN failure_reason varchar`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_anchor_status AS
      SELECT
        anchor_status,
        anchor_chain,
        COUNT(*) AS cert_count
      FROM vertex_otakiage_certificate
      WHERE anchor_status IS NOT NULL
      GROUP BY anchor_status, anchor_chain;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_anchor_status`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS failure_reason`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS content_hash`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchored_at`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchor_block_number`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchor_tx_hash`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchor_status`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchor_contract`.execute(db);
  await sql`ALTER TABLE vertex_otakiage_certificate DROP COLUMN IF EXISTS anchor_chain`.execute(db);
}
