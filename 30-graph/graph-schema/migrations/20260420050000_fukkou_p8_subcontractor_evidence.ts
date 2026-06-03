import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0037 — 復興予算 Phase 8: Subcontractor chain + Evidence blob registry.
 *
 * - vertex_fukkou_subcontractor  : multi-tier 下請 (Tier 1→4), 業種/従業員等
 * - edge_fukkou_subcontracted_to : 元請→1次→2次→...→n次 chain (報道 + 検査院裏付け)
 * - vertex_fukkou_evidence_blob  : PDF→WebP / web→gyotaku の R2 blob registry
 * - edge_fukkou_evidenced_by     : 任意 vertex → evidence blob の逆引き edge
 *
 * Evidence blob storage: R2 bucket `etzhayyim-graph` / prefix `fukkou/evidence/`.
 * Capture tool: 70-tools/evidence-crawler/capture_blob.py.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_subcontractor (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      sub_id            VARCHAR,
      corporate_number  VARCHAR,
      org_name          VARCHAR,
      org_name_kana     VARCHAR,
      address           VARCHAR,
      prefecture        VARCHAR,
      org_type          VARCHAR,
      typical_tier      INTEGER,
      industry_category VARCHAR,
      employees         INTEGER,
      capital_yen       NUMERIC,
      founded_year      INTEGER,
      linked_vendor_vertex_id VARCHAR,
      first_observed_at DATE,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_subcontracted_to (
      edge_id           VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      procurement_vertex_id VARCHAR,
      parent_vertex_id  VARCHAR,
      child_vertex_id   VARCHAR,
      tier_level        INTEGER,
      scope             VARCHAR,
      amount_yen        NUMERIC,
      share_pct         NUMERIC,
      evidence_source   VARCHAR,
      evidence_blob_id  VARCHAR,
      as_of_date        DATE,
      disclosure_status VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_evidence_blob (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      blob_id           VARCHAR,
      source_type       VARCHAR,
      source_url        VARCHAR,
      source_title      VARCHAR,
      source_issuer     VARCHAR,
      source_date       DATE,
      captured_at       TIMESTAMPTZ,
      sha256            VARCHAR,
      bytes             BIGINT,
      r2_bucket         VARCHAR,
      r2_key_original   VARCHAR,
      r2_key_webp       VARCHAR,
      r2_key_thumbnail  VARCHAR,
      r2_key_dom_html   VARCHAR,
      page_count        INTEGER,
      webp_width        INTEGER,
      webp_height       INTEGER,
      ocr_text_snippet  VARCHAR,
      related_vertex_ids VARCHAR,
      wayback_url       VARCHAR,
      status            VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_evidenced_by (
      edge_id           VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      target_vertex_id  VARCHAR,
      blob_vertex_id    VARCHAR,
      relation          VARCHAR,
      page_ref          VARCHAR,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    'edge_fukkou_evidenced_by',
    'vertex_fukkou_evidence_blob',
    'edge_fukkou_subcontracted_to',
    'vertex_fukkou_subcontractor',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
