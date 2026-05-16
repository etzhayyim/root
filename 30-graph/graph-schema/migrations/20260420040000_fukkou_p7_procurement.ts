import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0037 — 復興予算 Phase 7: Procurement / Vendor / Officer / Org affiliation.
 *
 * Extends 20260420010000_fukkou_political_lineage with the procurement
 * dimension: 入札案件, 受注者 (vendor), 発注担当官 (officer), 親子/関連組織.
 *
 * 4 vertex + 5 edge. Evidence: 会計検査院 報告 / 各社 有報 / 官報 / 各省公表.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_procurement (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      procurement_id    VARCHAR,
      authority_did     VARCHAR,
      project_title     VARCHAR,
      procurement_type  VARCHAR,
      bid_method        VARCHAR,
      announcement_date DATE,
      award_date        DATE,
      award_amount_yen  NUMERIC,
      predicted_price   NUMERIC,
      bid_ratio_pct     NUMERIC,
      fiscal_year       VARCHAR,
      budget_category   VARCHAR,
      source_url        VARCHAR,
      source_doc        VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_vendor (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      vendor_id         VARCHAR,
      corporate_number  VARCHAR,
      org_name          VARCHAR,
      org_name_kana     VARCHAR,
      address           VARCHAR,
      org_type          VARCHAR,
      capital_yen       NUMERIC,
      employees         INTEGER,
      founded_year      INTEGER,
      industry_code     VARCHAR,
      total_awards_yen  NUMERIC,
      award_count       INTEGER,
      linked_recipient_vertex_id VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_officer (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      officer_id        VARCHAR,
      officer_name      VARCHAR,
      officer_role      VARCHAR,
      officer_type      VARCHAR,
      authority_did     VARCHAR,
      ministry          VARCHAR,
      bureau            VARCHAR,
      department        VARCHAR,
      tenure_start      DATE,
      tenure_end        DATE,
      linked_bureaucrat_vertex_id VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_org_affiliation (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      affiliation_id    VARCHAR,
      relation_type     VARCHAR,
      parent_vertex_id  VARCHAR,
      child_vertex_id   VARCHAR,
      ownership_pct     NUMERIC,
      evidence_source   VARCHAR,
      evidence_url      VARCHAR,
      as_of_date        DATE,
      confidence        NUMERIC,
      notes             VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_org_parent (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      parent_vertex_id VARCHAR, child_vertex_id VARCHAR,
      ownership_pct NUMERIC, relation_type VARCHAR,
      evidence_source VARCHAR, as_of_date DATE, created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_org_affiliate (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      from_vertex_id VARCHAR, to_vertex_id VARCHAR,
      relation_type VARCHAR, evidence_source VARCHAR,
      as_of_date DATE, created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_procurement_awarded_to (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      procurement_vertex_id VARCHAR, vendor_vertex_id VARCHAR,
      award_amount_yen NUMERIC, award_share_pct NUMERIC,
      joint_bid_flag BOOLEAN, created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_procurement_handled_by (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      procurement_vertex_id VARCHAR, officer_vertex_id VARCHAR,
      role VARCHAR, created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_vendor_employs_officer (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      vendor_vertex_id VARCHAR, officer_vertex_id VARCHAR,
      role VARCHAR, tenure_start DATE, tenure_end DATE, created_at TIMESTAMPTZ
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    'edge_fukkou_vendor_employs_officer',
    'edge_fukkou_procurement_handled_by',
    'edge_fukkou_procurement_awarded_to',
    'edge_fukkou_org_affiliate',
    'edge_fukkou_org_parent',
    'vertex_fukkou_org_affiliation',
    'vertex_fukkou_officer',
    'vertex_fukkou_vendor',
    'vertex_fukkou_procurement',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
