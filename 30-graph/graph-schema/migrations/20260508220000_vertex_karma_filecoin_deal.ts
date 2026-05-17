import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated Filecoin deal log).

/**
 * karma.etzhayyim.com — Filecoin storage deal log (Phase K3).
 *
 * L4 long-term backup beyond ETH anchor. Each pinned IPFS CID is
 * proposed to N=5 storage providers via Estuary / Lighthouse /
 * Web3.Storage Filecoin API. One row per (cid, sp_address). Renewal
 * cycle (R/P30D) re-proposes deals expiring within 30 days.
 *
 * Karma.lean karma_5_layer_persistence guarantee: 5-layer redundancy
 * across (RisingWave / AT-repo / IPFS-self / IPFS-ext / Filecoin) —
 * this schema backs the Filecoin layer.
 *
 * Tables (1 vertex + 2 streaming MV):
 *   vertex_karma_filecoin_deal       per-(cid, SP) deal record
 *   mv_karma_filecoin_active         active+sealed deals
 *   mv_karma_filecoin_expiring_soon  deals expiring < 30d (renewal queue)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_filecoin_deal (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      deal_id varchar NOT NULL,
      cid varchar NOT NULL,
      sp_address varchar NOT NULL,
      deal_proposal_cid varchar,
      provider_endpoint varchar,
      bundler_used varchar,
      proposed_at varchar,
      proposed_at_ms bigint,
      sealed_at varchar,
      sealed_at_ms bigint,
      expires_at_ms bigint,
      duration_days bigint,
      bytes_size bigint,
      retrieval_url varchar,
      cost_usd_estimate double precision,
      status varchar NOT NULL,
      error_code varchar,
      error_message varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_fil_cid ON vertex_karma_filecoin_deal (cid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fil_sp ON vertex_karma_filecoin_deal (sp_address)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fil_status ON vertex_karma_filecoin_deal (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fil_expires ON vertex_karma_filecoin_deal (expires_at_ms)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_filecoin_active AS
    SELECT
      cid,
      sp_address,
      deal_id,
      sealed_at_ms,
      expires_at_ms,
      bytes_size
    FROM vertex_karma_filecoin_deal
    WHERE status IN ('proposed', 'sealed', 'active')
  `.execute(db);

  // Deals expiring within 30 days (2,592,000,000 ms = 30d).
  // Bounded by deal volume; renewal sweep reads this MV.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_filecoin_expiring_soon AS
    SELECT
      cid,
      sp_address,
      deal_id,
      expires_at_ms,
      bytes_size
    FROM vertex_karma_filecoin_deal
    WHERE status IN ('sealed', 'active')
      AND expires_at_ms IS NOT NULL
      AND to_timestamp(expires_at_ms / 1000.0) < (now() + INTERVAL '30 days')
      AND to_timestamp(expires_at_ms / 1000.0) > now()
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_filecoin_expiring_soon`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_filecoin_active`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_filecoin_deal`.execute(db);
}
