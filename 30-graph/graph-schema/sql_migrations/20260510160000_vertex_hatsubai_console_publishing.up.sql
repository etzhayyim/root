-- etzhayyim-project-hatsubai (発売) — console publishing pipeline schema.
--
-- One actor (`hatsubai.etzhayyim.com`) covers the partner / cert / submission
-- pipeline shared by Nintendo Switch 2, PlayStation 5, Xbox Series X|S
-- and Steam. Per-platform variation is captured by `platform_code`
-- column, not separate tables, so cross-platform queries (release
-- calendar, blocker rollup, devkit utilization) stay one-shot.
--
-- Persistence model:
--   * Plain "GraphAr-native promoted columns" (no JSON, no 1NF blowup)
--   * AT Lexicon float ban → all monetary / proportional fields are
--     scaled BIGINT (price_minor in cents/sen, revshare_bps in 0-10000)
--   * Hard delete only (ADR-0036) — no _alive soft-delete
--   * RLS 3-col (actor_did / org_did / at_did) + created_at on every
--     row per ADR-0095
--
-- Vertices (11):
--   vertex_hatsubai_platform           — Switch2/PS5/Xbox/Steam master
--   vertex_hatsubai_partner_account    — DevNet / Nintendo Dev Portal
--   vertex_hatsubai_devkit             — DevKit/TestKit individual unit
--   vertex_hatsubai_sdk_version        — platform SDK version + cert window
--   vertex_hatsubai_title              — per-platform title row (joins
--                                        the cross-platform vertex_games_title)
--   vertex_hatsubai_title_build        — submitted master ROM / package
--   vertex_hatsubai_trc_check          — TRC / Lotcheck rule result
--   vertex_hatsubai_cert_submission    — cert submission round
--   vertex_hatsubai_age_rating         — CERO / ESRB / PEGI / IARC / GRAC
--   vertex_hatsubai_store_listing      — eShop / PSN Store / MS Store / Steam page
--   vertex_hatsubai_store_asset        — screenshot / trailer / key art / icon
--
-- Edges (7):
--   edge_hatsubai_partner_devkit_holds       partner → devkit
--   edge_hatsubai_title_targets_platform     games_title → platform
--   edge_hatsubai_build_of_title             title_build → title
--   edge_hatsubai_submission_for_build       cert_submission → title_build
--   edge_hatsubai_publisher_publishes        legal_entity → title (revshare_bps)
--   edge_hatsubai_localized_into             title → store_listing
--   edge_hatsubai_rating_required_for_listing store_listing → age_rating
--
-- MVs (5, all bounded cardinality):
--   mv_hatsubai_title_cert_status_latest     title × platform → latest round
--   mv_hatsubai_title_trc_open_failures      title × severity open fails
--   mv_hatsubai_title_age_rating_coverage    title × region rating coverage
--   mv_hatsubai_partner_devkit_utilization   partner × platform devkit usage
--   mv_hatsubai_release_calendar             upcoming release_date × region
--
-- Pipeline-blocker is intentionally a plain VIEW (not MV) — high
-- branching makes it MV-unsafe per the §MV Memory Safety Guardrails.

-- =============================================================
-- Vertices
-- =============================================================

CREATE TABLE IF NOT EXISTS vertex_hatsubai_platform (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  platform_code VARCHAR,
  display_name VARCHAR,
  holder_legal_entity_did VARCHAR,
  cert_program_name VARCHAR,
  submission_portal_url VARCHAR,
  developer_portal_url VARCHAR,
  region_locked BOOLEAN,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_platform_code
  ON vertex_hatsubai_platform (platform_code);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_partner_account (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  partner_id VARCHAR,
  platform_code VARCHAR,
  legal_entity_did VARCHAR,
  vetting_status VARCHAR,
  nda_signed_at VARCHAR,
  approved_at VARCHAR,
  primary_contact_email VARCHAR,
  region_iso3166 VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_partner_platform
  ON vertex_hatsubai_partner_account (platform_code, vetting_status);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_devkit (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  serial VARCHAR,
  platform_code VARCHAR,
  kit_kind VARCHAR,
  status VARCHAR,
  firmware_version VARCHAR,
  assigned_to_did VARCHAR,
  assigned_at VARCHAR,
  returned_at VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_devkit_assigned
  ON vertex_hatsubai_devkit (assigned_to_did, status);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_sdk_version (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  platform_code VARCHAR,
  sdk_version VARCHAR,
  cert_window_open_at VARCHAR,
  cert_window_close_at VARCHAR,
  release_notes_uri VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_sdk_platform_window
  ON vertex_hatsubai_sdk_version (platform_code, cert_window_close_at);

-- per-platform title projection: 1 cross-platform vertex_games_title
-- joins to N rows here (one per target console).
CREATE TABLE IF NOT EXISTS vertex_hatsubai_title (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  games_title_did VARCHAR,
  platform_code VARCHAR,
  title_id VARCHAR,
  master_status VARCHAR,
  target_release_date VARCHAR,
  lead_studio_did VARCHAR,
  publisher_did VARCHAR,
  storefront_slug VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_title_platform
  ON vertex_hatsubai_title (platform_code);

CREATE INDEX IF NOT EXISTS idx_hatsubai_title_release_date
  ON vertex_hatsubai_title (target_release_date);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_title_build (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  title_did VARCHAR,
  build_cid VARCHAR,
  sdk_version VARCHAR,
  version_label VARCHAR,
  size_bytes BIGINT,
  signed_at VARCHAR,
  manifest_cid VARCHAR,
  is_master_candidate BOOLEAN,
  build_status VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_build_title
  ON vertex_hatsubai_title_build (title_did);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_trc_check (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  build_did VARCHAR,
  rule_id VARCHAR,
  rule_name VARCHAR,
  severity VARCHAR,
  result VARCHAR,
  evidence_uri VARCHAR,
  reviewer_note VARCHAR,
  observed_at VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_trc_build_severity
  ON vertex_hatsubai_trc_check (build_did, severity, result);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_cert_submission (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  build_did VARCHAR,
  round_no BIGINT,
  submitted_at VARCHAR,
  resolved_at VARCHAR,
  result VARCHAR,
  reviewer_note_uri VARCHAR,
  fail_count BIGINT,
  must_fail_count BIGINT,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_submission_build_round
  ON vertex_hatsubai_cert_submission (build_did, round_no);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_age_rating (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  title_did VARCHAR,
  board VARCHAR,
  region_iso3166 VARCHAR,
  rating_label VARCHAR,
  rating_age_min BIGINT,
  descriptor_codes VARCHAR,
  certificate_uri VARCHAR,
  granted_at VARCHAR,
  expires_at VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_rating_title_board
  ON vertex_hatsubai_age_rating (title_did, board);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_store_listing (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  title_did VARCHAR,
  region_iso3166 VARCHAR,
  locale VARCHAR,
  price_minor BIGINT,
  currency_iso4217 VARCHAR,
  release_date VARCHAR,
  preorder_at VARCHAR,
  description_cid VARCHAR,
  short_description VARCHAR,
  publish_status VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_listing_title_region
  ON vertex_hatsubai_store_listing (title_did, region_iso3166);

CREATE TABLE IF NOT EXISTS vertex_hatsubai_store_asset (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  listing_did VARCHAR,
  asset_kind VARCHAR,
  cid VARCHAR,
  width_px BIGINT,
  height_px BIGINT,
  duration_ms BIGINT,
  display_order BIGINT,
  alt_text VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hatsubai_asset_listing
  ON vertex_hatsubai_store_asset (listing_did, asset_kind, display_order);

-- =============================================================
-- Edges
-- =============================================================

CREATE TABLE IF NOT EXISTS edge_hatsubai_partner_devkit_holds (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  assigned_at VARCHAR,
  returned_at VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_title_targets_platform (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  port_status VARCHAR,
  lead_studio_did VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_build_of_title (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  is_master_candidate BOOLEAN,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_submission_for_build (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  round_no BIGINT,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_publisher_publishes (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  revshare_bps BIGINT,
  territory_iso3166 VARCHAR,
  term_starts_at VARCHAR,
  term_ends_at VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_localized_into (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  lead_translator_did VARCHAR,
  locale VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hatsubai_rating_required_for_listing (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  is_blocking BOOLEAN,
  actor_did VARCHAR,
  org_did VARCHAR,
  at_did VARCHAR,
  created_at VARCHAR
);

-- =============================================================
-- Streaming MVs (all bounded cardinality)
-- =============================================================

-- Latest cert round per title × platform.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hatsubai_title_cert_status_latest AS
  SELECT DISTINCT ON (t.vertex_id)
    t.vertex_id           AS title_did,
    t.platform_code       AS platform_code,
    s.vertex_id           AS submission_did,
    s.round_no            AS round_no,
    s.result              AS result,
    s.must_fail_count     AS must_fail_count,
    s.submitted_at        AS submitted_at,
    s.resolved_at         AS resolved_at
  FROM vertex_hatsubai_title t
  JOIN vertex_hatsubai_title_build b ON b.title_did = t.vertex_id
  JOIN vertex_hatsubai_cert_submission s ON s.build_did = b.vertex_id
  ORDER BY t.vertex_id, s.round_no DESC, s.submitted_at DESC;

-- Open TRC fails grouped by title × severity (open = result='fail').
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hatsubai_title_trc_open_failures AS
  SELECT
    b.title_did      AS title_did,
    c.severity       AS severity,
    COUNT(*)         AS open_count
  FROM vertex_hatsubai_trc_check c
  JOIN vertex_hatsubai_title_build b ON b.vertex_id = c.build_did
  WHERE c.result = 'fail'
  GROUP BY b.title_did, c.severity;

-- Age rating coverage: which (title, region) combos have all required boards.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hatsubai_title_age_rating_coverage AS
  SELECT
    title_did,
    region_iso3166,
    COUNT(*)                                     AS rating_count,
    COUNT(*) FILTER (WHERE rating_label IS NOT NULL AND rating_label <> '') AS granted_count
  FROM vertex_hatsubai_age_rating
  GROUP BY title_did, region_iso3166;

-- Devkit utilization per partner × platform.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hatsubai_partner_devkit_utilization AS
  SELECT
    assigned_to_did                                              AS partner_did,
    platform_code                                                AS platform_code,
    COUNT(*) FILTER (WHERE status = 'active')                    AS active_count,
    COUNT(*) FILTER (WHERE status = 'idle')                      AS idle_count,
    COUNT(*) FILTER (WHERE status = 'returned')                  AS returned_count,
    COUNT(*)                                                     AS total_count
  FROM vertex_hatsubai_devkit
  WHERE assigned_to_did IS NOT NULL AND assigned_to_did <> ''
  GROUP BY assigned_to_did, platform_code;

-- Release calendar: keyed by (release_date, platform, region) for low cardinality.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hatsubai_release_calendar AS
  SELECT
    l.release_date          AS release_date,
    t.platform_code         AS platform_code,
    l.region_iso3166        AS region_iso3166,
    COUNT(*)                AS title_count
  FROM vertex_hatsubai_store_listing l
  JOIN vertex_hatsubai_title t ON t.vertex_id = l.title_did
  WHERE l.release_date IS NOT NULL AND l.release_date <> ''
  GROUP BY l.release_date, t.platform_code, l.region_iso3166;

FLUSH;
