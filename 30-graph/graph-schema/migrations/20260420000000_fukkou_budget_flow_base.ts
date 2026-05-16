import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0036 — JPN Reconstruction Budget (復興予算) Flow Lineage base schema.
 *
 * Tracks the full lifecycle of 復興予算 (2011 東日本大震災 post-disaster
 * reconstruction budget):
 *
 *   Taxpayers → 復興特別税 + 復興債 → 復興庁 → 都道府県 復興局 → 市町村 / 事業者
 *
 * Tier separation (ADR-0018 compliant):
 *   Tier 1 public  : authority DIDs, amount buckets, fiscal_year, category
 *                    (復興予算 is public money — full flow MUST be auditable)
 *   Tier 2 domain  : per-flow amount JPY (exact), counterparty entity ID
 *                    (counterparty 法人番号 is public — Tier 1 OK, but narrative
 *                     may contain case-specific detail → Tier 2 signal-encrypted)
 *   Tier 3 (rare)  : 個人 grant recipients (住宅再建補助金等) — debtor_did pattern
 *
 * 3 vertex + 2 edge + 1 narrow MV. Designed for gov-resource-flow WIT
 * compatibility (same source_id/destination_id pattern).
 *
 * Spec: 90-docs/adr/0036-fukkou-budget-flow-lineage.md (to be authored)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 復興予算 flow event (source → destination, 1 row per fiscal transaction) ──
  await sql`
    CREATE TABLE vertex_fukkou_budget_flow (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      rkey              VARCHAR NOT NULL,
      flow_id           VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      source_did        VARCHAR NOT NULL,
      source_kind       VARCHAR NOT NULL,
      destination_did   VARCHAR NOT NULL,
      destination_kind  VARCHAR NOT NULL,
      category          VARCHAR NOT NULL,
      sub_category      VARCHAR,
      amount_jpy        DOUBLE PRECISION NOT NULL,
      amount_bucket     VARCHAR NOT NULL,
      effective_date    TIMESTAMPTZ NOT NULL,
      legal_basis       VARCHAR,
      narrative         VARCHAR,
      source_url        VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── taxpayer → 復興予算 ingress (徴税 + 復興債 発行) ──
  await sql`
    CREATE TABLE edge_fukkou_taxed_to (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      tax_code          VARCHAR NOT NULL,
      amount_jpy        DOUBLE PRECISION NOT NULL,
      taxpayer_count    BIGINT,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── 復興予算 → recipient egress (補助金 / 賠償 / 事業委託) ──
  await sql`
    CREATE TABLE edge_fukkou_disbursed_to (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      fiscal_year          VARCHAR NOT NULL,
      disbursement_kind    VARCHAR NOT NULL,
      amount_jpy           DOUBLE PRECISION NOT NULL,
      recipient_category   VARCHAR NOT NULL,
      recipient_lei        VARCHAR,
      recipient_houjin_no  VARCHAR,
      contract_number      VARCHAR,
      created_at           TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Taxpayer type aggregation (for ingress side) ──
  await sql`
    CREATE TABLE vertex_fukkou_taxpayer_stat (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      tax_code          VARCHAR NOT NULL,
      payer_category    VARCHAR NOT NULL,
      payer_count       BIGINT NOT NULL,
      total_amount_jpy  DOUBLE PRECISION NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Indexes ───────────────────────────────────────────────────────────
  await sql`CREATE INDEX idx_fukkou_flow_fy_category ON vertex_fukkou_budget_flow (fiscal_year, category)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_flow_source ON vertex_fukkou_budget_flow (source_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_flow_destination ON vertex_fukkou_budget_flow (destination_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_taxed_fy ON edge_fukkou_taxed_to (fiscal_year, tax_code)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_disbursed_fy ON edge_fukkou_disbursed_to (fiscal_year, recipient_category)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_taxpayer_fy ON vertex_fukkou_taxpayer_stat (fiscal_year, tax_code)`.execute(db);

  // ── Streaming MV: fiscal_year × category aggregate (bounded: ~25 FY × ~10 category) ──
  await sql`
    CREATE MATERIALIZED VIEW mv_fukkou_flow_by_category AS
    SELECT
      fiscal_year,
      category,
      source_kind,
      destination_kind,
      COUNT(*)           AS flow_count,
      SUM(amount_jpy)    AS total_jpy
    FROM vertex_fukkou_budget_flow
    GROUP BY fiscal_year, category, source_kind, destination_kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_fukkou_flow_by_category`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_taxpayer_stat`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_disbursed_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_taxed_to`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_budget_flow`.execute(db);
}
