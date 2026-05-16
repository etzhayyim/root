import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0035 — JPN Seizure (差し押さえ) Cluster Phase 1 MVP base schema.
 *
 * Scope: 国税徴収法 (kokuzei) aggregator + public 統計 MV.
 * Tier separation (ADR-0018 compliant):
 *   Tier 1/2 (Repo)        : caseId / authorityDid / caseType / amountBucket / status / periodYm
 *   Tier 3 (Preferences)   : debtorDid / debtor name / exact amount / property detail
 *                            → NOT stored in graph. Accessed via server-side Preferences only.
 *
 * 4 vertex tables (Tier 1/2 projection only) + 1 narrow MV.
 *
 * MV memory safety (graph-schema/CLAUDE.md §MV Memory Safety Guardrails):
 *   - mv_sashiosae_stats_by_type: GROUP BY (case_type, authority_did, period_ym, amount_bucket)
 *   - cardinality bound: 7 case_types × ~3k authorities × ~60 months × 5 buckets ≈ 6.3M max,
 *     typically <1M active. Row count per group bounded by anonymized caseId (no MAX varchar).
 *   - No JOIN across tables; pure aggregation on single vertex table.
 *
 * Spec: 90-docs/adr/0035-jpn-seizure-cluster-topology.md
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── sashiosae vertex tables (Tier 1/2 only) ──────────────────────────
  await sql`
    CREATE TABLE vertex_atrecord_sashiosae_choushuu_case (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      case_type       VARCHAR NOT NULL,
      status          VARCHAR NOT NULL,
      amount_bucket   VARCHAR NOT NULL,
      period_ym       VARCHAR NOT NULL,
      tax_kind        VARCHAR,
      created_at      TIMESTAMPTZ NOT NULL,
      closed_at       TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_sashiosae_notice (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      notice_id       VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      property_type   VARCHAR NOT NULL,
      priority_rank   INTEGER,
      noticed_at      TIMESTAMPTZ NOT NULL,
      effective_at    TIMESTAMPTZ,
      created_at      TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_sashiosae_release (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      release_id      VARCHAR NOT NULL,
      notice_id       VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      reason          VARCHAR NOT NULL,
      released_at     TIMESTAMPTZ NOT NULL,
      created_at      TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_sashiosae_kanka_result (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      rkey              VARCHAR NOT NULL,
      kanka_id          VARCHAR NOT NULL,
      notice_id         VARCHAR NOT NULL,
      case_id           VARCHAR NOT NULL,
      authority_did     VARCHAR NOT NULL,
      kanka_method      VARCHAR NOT NULL,
      auction_id        VARCHAR NOT NULL,
      property_type     VARCHAR,
      estimated_value   DOUBLE PRECISION,
      scheduled_at      TIMESTAMPTZ NOT NULL,
      venue_url         VARCHAR,
      closed_at         TIMESTAMPTZ,
      clearing_bucket   VARCHAR,
      status            VARCHAR NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Indexes for query paths ──────────────────────────────────────────
  await sql`CREATE INDEX idx_sashiosae_case_authority_period ON vertex_atrecord_sashiosae_choushuu_case (authority_did, period_ym)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_case_type_status ON vertex_atrecord_sashiosae_choushuu_case (case_type, status)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_notice_case ON vertex_atrecord_sashiosae_notice (case_id)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_kanka_scheduled ON vertex_atrecord_sashiosae_kanka_result (scheduled_at, status)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_kanka_authority ON vertex_atrecord_sashiosae_kanka_result (authority_did, scheduled_at)`.execute(db);

  // ── Streaming MV: statsByType aggregation (narrow, bounded cardinality) ──
  await sql`
    CREATE MATERIALIZED VIEW mv_sashiosae_stats_by_type AS
    SELECT
      case_type,
      authority_did,
      period_ym,
      amount_bucket,
      status,
      COUNT(*) AS case_count
    FROM vertex_atrecord_sashiosae_choushuu_case
    GROUP BY case_type, authority_did, period_ym, amount_bucket, status
  `.execute(db);

  // ── Edge: caseToNotice (case_id → notice) ────────────────────────────
  await sql`
    CREATE TABLE edge_sashiosae_case_notice (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      _seq             BIGINT NOT NULL,
      owner_did        VARCHAR NOT NULL,
      priority_rank    INTEGER,
      created_at       TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_edge_sashiosae_case_notice_src ON edge_sashiosae_case_notice (src_vid)`.execute(db);
  await sql`CREATE INDEX idx_edge_sashiosae_case_notice_dst ON edge_sashiosae_case_notice (dst_vid)`.execute(db);

  // ── Crawler cursor (NTA 公売公告 ingest via sashiosae-ingest-nta-koubai.mjs) ──
  // Mirrors 0048_vertex_page_extract_cursor pattern (kuruma/media_anime/etc).
  await sql`ALTER TABLE vertex_page ADD COLUMN IF NOT EXISTS extracted_for_sashiosae TIMESTAMPTZ`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_sashiosae_stats_by_type`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_sashiosae_case_notice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_sashiosae_kanka_result`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_sashiosae_release`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_sashiosae_notice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_sashiosae_choushuu_case`.execute(db);
  await sql`ALTER TABLE vertex_page DROP COLUMN IF EXISTS extracted_for_sashiosae`.execute(db);
}
