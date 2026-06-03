import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0074 ERC725 root identity projection.
// tier: A

/**
 * ERC725 root identity projection for already-registered RisingWave rows.
 *
 * The contract registry remains the source of truth. These tables and columns
 * let RisingWave keep a queryable projection without destructively rewriting
 * existing did:etzhayyim / did:web / did:plc primary keys in one migration.
 *
 * `scripts/migrate-rw-erc725-root.mjs` backfills only facade DIDs that are
 * already linked in `etzhayyimRootIdentityRegistry`.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_erc725_root_identity (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      root_did VARCHAR,
      root_did_hash VARCHAR,
      root_identity_addr VARCHAR,
      chain_id BIGINT,
      registry_addr VARCHAR,
      controller_addr VARCHAR,

      source VARCHAR,
      status VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_erc725_facade_did (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      root_did VARCHAR,
      root_did_hash VARCHAR,
      facade_did VARCHAR,
      facade_did_hash VARCHAR,
      facade_method VARCHAR,
      root_identity_addr VARCHAR,
      chain_id BIGINT,
      registry_addr VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_identity_addr VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN facade_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN facade_did_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN identity_method VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN migration_status VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN root_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN root_did_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN root_identity_addr VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN legacy_claimant_did VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN root_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN root_did_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN root_identity_addr VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN legacy_challenger_did VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_erc725_root_identity_hash
    ON vertex_erc725_root_identity (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_erc725_root_identity_addr
    ON vertex_erc725_root_identity (root_identity_addr)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_erc725_facade_hash
    ON edge_erc725_facade_did (facade_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_erc725_facade_root_hash
    ON edge_erc725_facade_did (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_root_hash
    ON vertex_etzhayyim_identity (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_root_hash
    ON vertex_claim_stake (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_root_hash
    ON vertex_claim_challenge (root_did_hash)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_claim_challenge_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_claim_stake_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_erc725_facade_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_erc725_facade_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_erc725_root_identity_addr`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_erc725_root_identity_hash`.execute(db);

  await sql`ALTER TABLE vertex_claim_challenge DROP COLUMN legacy_challenger_did`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge DROP COLUMN root_identity_addr`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge DROP COLUMN root_did_hash`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge DROP COLUMN root_did`.execute(db);

  await sql`ALTER TABLE vertex_claim_stake DROP COLUMN legacy_claimant_did`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake DROP COLUMN root_identity_addr`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake DROP COLUMN root_did_hash`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake DROP COLUMN root_did`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN migration_status`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN identity_method`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN facade_did_hash`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN facade_did`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_identity_addr`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did_hash`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_erc725_facade_did`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_erc725_root_identity`.execute(db);
}
