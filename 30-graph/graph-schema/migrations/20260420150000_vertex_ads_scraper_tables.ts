import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Public ad-library scraper ingest schema.
 *
 * Scope: Meta Ad Library, Google Ads Transparency Center, LinkedIn Ad
 * Library, TikTok Commercial Content Library, X Ads Transparency — all
 * fetched via browser automation (yorishiro/playwright) rather than
 * official APIs. Each row is a crawl observation of a public ad creative
 * surfaced in these platforms' DSA / political-transparency portals.
 *
 * GraphAr-native (1 AT record = 1 row, typed columns, no val_json).
 * Owner/RLS columns on every table. Private-text columns are rare here
 * (everything is already public DSA data), but landing_url + raw HTML
 * can carry tracking params; stored plaintext is fine.
 *
 * Cardinality plan (mid-2026 target):
 *   vertex_ads_advertiser    ~200K
 *   vertex_ads_creative      ~10M  (one row per (platform, platform_ad_id))
 *   vertex_ads_snapshot      ~40M  (append-only scrape observations)
 *   edge_ads_*               ~30M total
 *
 * All monetary / reach columns are DOUBLE PRECISION because RisingWave
 * does not support NUMERIC(p,s) (see migration 20260417200000 comment).
 * Impression/spend *ranges* are stored as _min/_max pairs because Meta
 * and TikTok publish banded estimates, not point values.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ----- advertiser ---------------------------------------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ads_advertiser (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      platform                VARCHAR,
      platform_advertiser_id  VARCHAR,
      name                    VARCHAR,
      verified_name           VARCHAR,
      legal_name              VARCHAR,
      page_url                VARCHAR,
      page_category           VARCHAR,
      country                 VARCHAR,
      funding_entity          VARCHAR,
      is_political            BOOLEAN,
      legal_entity_did        VARCHAR,
      first_seen_at           VARCHAR,
      last_seen_at            VARCHAR,
      org_id                  VARCHAR,
      user_id                 VARCHAR,
      actor_id                VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_advertiser_platform_pid ON vertex_ads_advertiser (platform, platform_advertiser_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_advertiser_legal_entity_did ON vertex_ads_advertiser (legal_entity_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_advertiser_country ON vertex_ads_advertiser (country)`.execute(db);

  // ----- creative (1 row per (platform, platform_ad_id)) --------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ads_creative (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      platform                VARCHAR,
      platform_ad_id          VARCHAR,
      advertiser_vertex_id    VARCHAR,
      advertiser_name         VARCHAR,
      creative_type           VARCHAR,
      headline                VARCHAR,
      body_text               VARCHAR,
      cta_text                VARCHAR,
      landing_url             VARCHAR,
      display_url             VARCHAR,
      media_url               VARCHAR,
      media_cid               VARCHAR,
      thumbnail_cid           VARCHAR,
      languages               VARCHAR,
      currency                VARCHAR,
      impressions_min         BIGINT,
      impressions_max         BIGINT,
      spend_min               DOUBLE PRECISION,
      spend_max               DOUBLE PRECISION,
      reach_min               BIGINT,
      reach_max               BIGINT,
      is_political            BOOLEAN,
      is_active               BOOLEAN,
      ad_delivery_start_date  VARCHAR,
      ad_delivery_stop_date   VARCHAR,
      first_seen_at           VARCHAR,
      last_seen_at            VARCHAR,
      source_url              VARCHAR,
      org_id                  VARCHAR,
      user_id                 VARCHAR,
      actor_id                VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_creative_platform_ad_id ON vertex_ads_creative (platform, platform_ad_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_creative_advertiser ON vertex_ads_creative (advertiser_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_creative_last_seen ON vertex_ads_creative (last_seen_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_creative_political ON vertex_ads_creative (is_political)`.execute(db);

  // ----- snapshot (append-only crawl observation) ---------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ads_snapshot (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      creative_vertex_id      VARCHAR,
      platform                VARCHAR,
      platform_ad_id          VARCHAR,
      scraper                 VARCHAR,
      scraper_run_id          VARCHAR,
      scraped_at              VARCHAR,
      source_url              VARCHAR,
      http_status             BIGINT,
      html_cid                VARCHAR,
      screenshot_cid          VARCHAR,
      har_cid                 VARCHAR,
      observed_is_active      BOOLEAN,
      observed_impressions_min BIGINT,
      observed_impressions_max BIGINT,
      observed_spend_min      DOUBLE PRECISION,
      observed_spend_max      DOUBLE PRECISION,
      parser_version          VARCHAR,
      parse_ok                BOOLEAN,
      parse_error             VARCHAR,
      org_id                  VARCHAR,
      user_id                 VARCHAR,
      actor_id                VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_snapshot_creative ON vertex_ads_snapshot (creative_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_snapshot_run ON vertex_ads_snapshot (scraper_run_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_snapshot_platform_ad_id ON vertex_ads_snapshot (platform, platform_ad_id, scraped_at)`.execute(db);

  // ----- scraper run (one row per crawl invocation) -------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ads_scraper_run (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      platform                VARCHAR,
      query_kind              VARCHAR,
      query_value             VARCHAR,
      country                 VARCHAR,
      started_at              VARCHAR,
      finished_at             VARCHAR,
      status                  VARCHAR,
      ads_seen                BIGINT,
      ads_new                 BIGINT,
      ads_updated             BIGINT,
      error_message           VARCHAR,
      user_agent              VARCHAR,
      proxy_country           VARCHAR,
      playwright_trace_cid    VARCHAR,
      robots_txt_snapshot_cid VARCHAR,
      rate_limit_sleep_ms     BIGINT,
      org_id                  VARCHAR,
      user_id                 VARCHAR,
      actor_id                VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_ads_scraper_run_started ON vertex_ads_scraper_run (platform, started_at)`.execute(db);

  // ----- edges --------------------------------------------------------------
  // creative → advertiser
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ads_served_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      platform        VARCHAR,
      first_seen_at   VARCHAR,
      last_seen_at    VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_served_by_src ON edge_ads_served_by (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_served_by_dst ON edge_ads_served_by (dst_vid)`.execute(db);

  // creative → country (ISO 3166-1 alpha-2). One edge per delivery country.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ads_targets_country (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      country         VARCHAR,
      impressions_min BIGINT,
      impressions_max BIGINT,
      spend_min       DOUBLE PRECISION,
      spend_max       DOUBLE PRECISION
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_targets_country_src ON edge_ads_targets_country (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_targets_country_country ON edge_ads_targets_country (country)`.execute(db);

  // creative → demographic bucket (age_range × gender — Meta/LinkedIn publish this)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ads_targets_audience (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      age_range       VARCHAR,
      gender          VARCHAR,
      country         VARCHAR,
      impression_share DOUBLE PRECISION
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_targets_audience_src ON edge_ads_targets_audience (src_vid)`.execute(db);

  // snapshot → creative (append-only observation pointer, used by projector MV)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ads_snapshot_of (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      scraped_at      VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_snapshot_of_src ON edge_ads_snapshot_of (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_snapshot_of_dst ON edge_ads_snapshot_of (dst_vid)`.execute(db);

  // advertiser → legal_entity (GLEIF LEI linkage, mirrors yabai edge_yabai_operated_by pattern)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ads_operated_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      lei             VARCHAR,
      match_method    VARCHAR,
      confidence      DOUBLE PRECISION
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_operated_by_src ON edge_ads_operated_by (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_ads_operated_by_dst ON edge_ads_operated_by (dst_vid)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_ads_operated_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_ads_snapshot_of`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_ads_targets_audience`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_ads_targets_country`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_ads_served_by`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ads_scraper_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ads_snapshot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ads_creative`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ads_advertiser`.execute(db);
}
