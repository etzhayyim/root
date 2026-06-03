import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0035 — JP tax money flow reverse-topology tables.
 *
 * Adds:
 *   vertex_etzhayyim_beneficial_owner — UBO (natural/legal/trust/spc/opaque).
 *   edge_etzhayyim_fiscal_flow        — money move across L0..L7 with derivation_stage guard.
 *   edge_etzhayyim_ownership          — UBO child→parent ownership with evidence_kind provenance.
 *
 * Partition-ready columns: fiscal_year on fiscal_flow; observed_at on ownership.
 *
 * Reverse resolution (leaf payee → taxpayer cohort) is served by a plain
 * recursive CTE at query time (depth ≤ 8), NOT a streaming MV — RisingWave
 * streaming MVs don't support recursive CTE, and the query shape is
 * per-leaf-DID (low cardinality, bounded depth).
 *
 * Follow the MV Memory Safety Guardrails: no GROUP BY over high-cardinality
 * varchar columns here; only narrow indexes for O(log N) traversal.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_beneficial_owner (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      child_did         VARCHAR,
      child_jcn         VARCHAR,
      parent_did        VARCHAR,
      parent_type       VARCHAR,
      ownership_pct     DOUBLE PRECISION,
      voting_pct        DOUBLE PRECISION,
      evidence_kind     VARCHAR,
      evidence_url      VARCHAR,
      observed_at       DATE,
      status            VARCHAR,
      opacity_reason    VARCHAR,
      pii_tier          BIGINT,
      created_at        VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_child_did ON vertex_etzhayyim_beneficial_owner (child_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_parent_did ON vertex_etzhayyim_beneficial_owner (parent_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_status ON vertex_etzhayyim_beneficial_owner (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_etzhayyim_fiscal_flow (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      from_did           VARCHAR,
      to_did             VARCHAR,
      stage              VARCHAR,
      derivation_stage   VARCHAR,
      fiscal_year        BIGINT,
      amount_jpy         BIGINT,
      basis              VARCHAR,
      program_code       VARCHAR,
      source_record_uri  VARCHAR,
      source_url         VARCHAR,
      observed_at        DATE
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_from ON edge_etzhayyim_fiscal_flow (from_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_to ON edge_etzhayyim_fiscal_flow (to_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_stage ON edge_etzhayyim_fiscal_flow (stage, fiscal_year)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_etzhayyim_ownership (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      parent_did         VARCHAR,
      child_did          VARCHAR,
      ownership_pct      DOUBLE PRECISION,
      voting_pct         DOUBLE PRECISION,
      evidence_kind      VARCHAR,
      evidence_url       VARCHAR,
      observed_at        DATE
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_ownership_child ON edge_etzhayyim_ownership (child_did, observed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_ownership_parent ON edge_etzhayyim_ownership (parent_did, observed_at)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_ownership_parent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_ownership_child`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_etzhayyim_ownership`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_stage`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_to`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_from`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_etzhayyim_fiscal_flow`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_parent_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_child_did`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_beneficial_owner`.execute(db);
}
