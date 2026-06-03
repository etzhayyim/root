import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2604261717 Phase 1 — claim-level stake vertex / edge / MV.
 *
 * Domain tables for "正しいと得・嘘で損" — staked claim attestations. The
 * canonical authority lives on chain in `ClaimStakeEscrow` (etzhayyim private
 * chain, chainId 260425). These rows are the graph projection a downstream
 * Phase 1.5 consumer fills in by tailing `ClaimPosted` /  `ClaimChallenged`
 * / `ClaimUpheld` / `ClaimSlashed` / `ClaimRefunded` events from the same
 * `vertex_blockchain_block` ingest path that ADR-2604251935 already
 * provides.
 *
 * Schema invariants (CLAUDE.md):
 *   - ALL tables follow `vertex_<label>` / `edge_<type>` (no exceptions).
 *   - Promoted columns, NOT 1NF — pull payload up onto the row.
 *   - VARCHAR / BIGINT / DOUBLE PRECISION / DATE only (RW lacks NUMERIC(p,s)).
 *   - RLS 3 cols (`org_id`, `user_id`, `actor_id`) + `created_at` on every
 *     vertex/edge that holds caller-attributable data.
 *   - No upsert-on-conflict and no high-cardinality `GROUP BY` in MVs (RW limits).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_claim_stake ─────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_claim_stake (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      claim_hash VARCHAR,
      did_hash VARCHAR,
      at_record_cid VARCHAR,
      claimant_addr VARCHAR,
      claimant_did VARCHAR,

      bond VARCHAR,
      bond_wei_dec VARCHAR,
      chain_id BIGINT,
      escrow_addr VARCHAR,
      claim_type VARCHAR,
      arbiter VARCHAR,

      claim_text VARCHAR,
      claim_text_len BIGINT,

      challenge_period_sec BIGINT,
      posted_at VARCHAR,
      window_closes_at VARCHAR,

      state VARCHAR,
      outcome VARCHAR,
      settled_at VARCHAR,
      settle_tx_hash VARCHAR,

      claimant_payout VARCHAR,
      challenger_payout VARCHAR,
      treasury_amount VARCHAR,
      reward_amount VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_claim_id ON vertex_claim_stake (claim_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_claimant ON vertex_claim_stake (claimant_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_state ON vertex_claim_stake (state)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_window_closes ON vertex_claim_stake (window_closes_at)`.execute(db);

  // ── vertex_claim_challenge ────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_claim_challenge (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      challenger_did_hash VARCHAR,
      challenger_did VARCHAR,
      challenger_addr VARCHAR,
      counter_bond VARCHAR,
      counter_bond_wei_dec VARCHAR,
      rebuttal VARCHAR,
      rebuttal_len BIGINT,
      posted_at VARCHAR,
      challenge_tx_hash VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_claim_id ON vertex_claim_challenge (claim_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_challenger ON vertex_claim_challenge (challenger_did)`.execute(db);

  // ── vertex_claim_resolution ───────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_claim_resolution (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      outcome VARCHAR,
      rationale VARCHAR,
      tx_hash VARCHAR,
      arbiter_addr VARCHAR,
      claimant_payout VARCHAR,
      challenger_payout VARCHAR,
      treasury_amount VARCHAR,
      reward_amount VARCHAR,
      settled_at VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_resolution_claim_id ON vertex_claim_resolution (claim_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_resolution_outcome ON vertex_claim_resolution (outcome)`.execute(db);

  // ── edge_claim_challenge_for ──────────────────────────────────────────────
  // src = challenge vertex, dst = claim vertex. CSR-side lookup: "all challenges of claim X".
  await sql`
    CREATE TABLE IF NOT EXISTS edge_claim_challenge_for (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR,
      counter_bond VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_claim_challenge_for_dst ON edge_claim_challenge_for (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_claim_challenge_for_src ON edge_claim_challenge_for (src_vid)`.execute(db);

  // ── edge_claim_resolution_for ─────────────────────────────────────────────
  // src = resolution vertex, dst = claim vertex. 1:1 with vertex_claim_resolution.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_claim_resolution_for (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR,
      outcome VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_claim_resolution_for_dst ON edge_claim_resolution_for (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_claim_resolution_for_src ON edge_claim_resolution_for (src_vid)`.execute(db);

  // ── mv_claim_stake_outcomes ───────────────────────────────────────────────
  // Narrow rollup over `state` (≤ 6 distinct values). Not by claimant — that
  // would be high cardinality. Use plain VIEW for per-claimant queries.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_claim_stake_outcomes AS
    SELECT state,
           COUNT(*)                                              AS claim_count,
           SUM(CASE WHEN bond IS NULL THEN 0 ELSE 1 END)         AS bond_set_count
      FROM vertex_claim_stake
     GROUP BY state
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_claim_stake_outcomes`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_claim_resolution_for`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_claim_challenge_for`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_claim_resolution`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_claim_challenge`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_claim_stake`.execute(db);
}
