import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated zk-proof submission log).

/**
 * karma.etzhayyim.com — zk-SNARK rebirth non-linkability proof schema (K3).
 *
 * Backs the RebirthVerifier.sol contract on Base L2. One row per
 * submitted proof; the verifier_contract column captures which
 * deployment accepted the proof (so multiple test/prod verifiers
 * can coexist without ambiguity).
 *
 * Tables (1 vertex + 1 streaming MV):
 *   vertex_karma_rebirth_proof   per-proof submission record
 *   mv_karma_rebirth_proof_recent  last 7d successful verifications
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_rebirth_proof (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      proof_id varchar NOT NULL,
      old_did_hash varchar,
      new_did varchar NOT NULL,
      new_santana_root varchar NOT NULL,
      nullifier varchar NOT NULL,
      proof_blob varchar,
      public_signals varchar,
      verifier_contract varchar,
      verifier_chain varchar,
      verified_at varchar,
      verified_at_ms bigint,
      tx_hash varchar,
      block_number bigint,
      status varchar NOT NULL,
      error_message varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_proof_new_did ON vertex_karma_rebirth_proof (new_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_proof_nullifier ON vertex_karma_rebirth_proof (nullifier)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_proof_status ON vertex_karma_rebirth_proof (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_proof_verified_at ON vertex_karma_rebirth_proof (verified_at_ms)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_rebirth_proof_recent AS
    SELECT
      proof_id,
      new_did,
      new_santana_root,
      nullifier,
      verifier_contract,
      verified_at_ms,
      tx_hash
    FROM vertex_karma_rebirth_proof
    WHERE status = 'verified'
      AND to_timestamp(verified_at_ms / 1000.0) > (now() - INTERVAL '7 days')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_rebirth_proof_recent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_rebirth_proof`.execute(db);
}
