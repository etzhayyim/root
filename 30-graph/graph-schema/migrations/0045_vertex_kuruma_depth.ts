import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0045: kuruma domain depth — 12 vertex + 9 edge + 5 MV (2026-04-14).
 *
 * Design: 90-docs/260414-domain-coverage-depth-design.md §A
 *
 * Expands the flat kuruma domain (80K models) into a supply-chain graph:
 * maker → platform → model → trim → part → supplier (Tier1/2) → plant → unit (VIN) → dealer.
 * Adds monthly sales, recalls, reviews, safety ratings for coverage depth signals.
 *
 * Naming: vertex_kuruma_* / edge_kuruma_* / mv_kuruma_* per graph-schema convention.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex tables (12) ─────────────────────────────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_model (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    maker_did       VARCHAR,
    platform_did    VARCHAR,
    generation_did  VARCHAR,
    name            VARCHAR,
    name_ja         VARCHAR,
    body_type       VARCHAR,
    first_year      INT,
    last_year       INT,
    country         VARCHAR,
    wikidata_qid    VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_trim (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    model_did       VARCHAR,
    variant         VARCHAR,
    engine_spec     VARCHAR,
    transmission    VARCHAR,
    drivetrain      VARCHAR,
    msrp_currency   VARCHAR,
    msrp_amount     DOUBLE PRECISION,
    market          VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_platform (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    name            VARCHAR,
    maker_did       VARCHAR,
    shared_with_dids VARCHAR,
    architecture    VARCHAR,
    launch_year     INT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_part (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    part_number     VARCHAR,
    name            VARCHAR,
    category        VARCHAR,
    supplier_did    VARCHAR,
    tier            INT,
    country_of_origin VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_plant (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    operator_did    VARCHAR,
    country         VARCHAR,
    region          VARCHAR,
    city            VARCHAR,
    capacity_units_year BIGINT,
    opened_year     INT,
    closed_year     INT,
    wikidata_qid    VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_unit (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    vin             VARCHAR,
    model_did       VARCHAR,
    trim_did        VARCHAR,
    plant_did       VARCHAR,
    manufactured_date DATE,
    country_market  VARCHAR,
    first_owner_country VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_sales_monthly (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    model_did       VARCHAR,
    country         VARCHAR,
    year            INT,
    month           INT,
    units_sold      BIGINT,
    revenue_usd     DOUBLE PRECISION,
    source          VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_recall (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    campaign_id     VARCHAR,
    regulator       VARCHAR,
    country         VARCHAR,
    announced_date  DATE,
    defect          VARCHAR,
    remedy          VARCHAR,
    affected_units_est BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_review (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    model_did       VARCHAR,
    reviewer_did    VARCHAR,
    source          VARCHAR,
    title           VARCHAR,
    score_numeric   DOUBLE PRECISION,
    score_scale     VARCHAR,
    published_date  DATE,
    language        VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_feature (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    name            VARCHAR,
    category        VARCHAR,
    iso_standard    VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_generation (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    model_family_did VARCHAR,
    generation_seq  INT,
    start_year      INT,
    end_year        INT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kuruma_safety_rating (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    model_did       VARCHAR,
    authority       VARCHAR,
    rating          VARCHAR,
    tested_year     INT,
    adult_occupant  DOUBLE PRECISION,
    child_occupant  DOUBLE PRECISION,
    pedestrian      DOUBLE PRECISION,
    safety_assist   DOUBLE PRECISION
  )`.execute(db);

  // ── Edge tables (9) ────────────────────────────────────────────────────

  const edge = (name: string, extra: string[] = []) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR${sql.raw(extra.length ? ',' : '')}
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  await edge('edge_kuruma_model_by_maker', ['maker_role VARCHAR']);
  await edge('edge_kuruma_uses_platform');
  await edge('edge_kuruma_contains_part', ['quantity INT', 'position VARCHAR']);
  await edge('edge_kuruma_part_supplier', ['tier INT', 'supply_start DATE', 'supply_end DATE']);
  await edge('edge_kuruma_assembled_at', ['assembly_date DATE']);
  await edge('edge_kuruma_unit_model');
  await edge('edge_kuruma_sold_by', ['sale_date DATE', 'price_usd DOUBLE PRECISION']);
  await edge('edge_kuruma_has_feature', ['standard BOOLEAN', 'optional_group VARCHAR']);
  await edge('edge_kuruma_recall_affects', ['model_did VARCHAR', 'affected_count BIGINT']);

  // ── Streaming MVs (5) ──────────────────────────────────────────────────

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_supply_chain_depth AS
    SELECT m.vertex_id AS model_did,
           COUNT(DISTINCT cp.dst_vid) AS part_count,
           COUNT(DISTINCT ps.dst_vid) AS supplier_count,
           COALESCE(MAX(ps.tier), 0)   AS max_tier
    FROM vertex_kuruma_model m
    LEFT JOIN edge_kuruma_contains_part cp ON cp.src_vid = m.vertex_id
    LEFT JOIN edge_kuruma_part_supplier ps ON ps.src_vid = cp.dst_vid
    GROUP BY m.vertex_id`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_sales_by_country AS
    SELECT s.model_did, s.country, s.year,
           SUM(s.units_sold)::BIGINT AS units_sold_year,
           SUM(s.revenue_usd)        AS revenue_year
    FROM vertex_kuruma_sales_monthly s
    GROUP BY s.model_did, s.country, s.year`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_platform_share AS
    SELECT p.vertex_id AS platform_did,
           p.name       AS platform_name,
           COUNT(DISTINCT m.vertex_id) AS model_count
    FROM vertex_kuruma_platform p
    LEFT JOIN vertex_kuruma_model m ON m.platform_did = p.vertex_id
    GROUP BY p.vertex_id, p.name`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_recall_per_maker AS
    SELECT m.maker_did,
           COUNT(DISTINCT r.vertex_id) AS recall_count,
           SUM(r.affected_units_est)::BIGINT AS total_affected_units
    FROM vertex_kuruma_recall r
    JOIN edge_kuruma_recall_affects ra ON ra.src_vid = r.vertex_id
    JOIN vertex_kuruma_model m ON m.vertex_id = ra.dst_vid
    GROUP BY m.maker_did`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_dealer_density_by_country AS
    SELECT
      SPLIT_PART(SPLIT_PART(repo, '.etzhayyim.com', 1), 'did:web:', 2) AS app_host,
      CAST(NULL AS VARCHAR) AS country,
      COUNT(*)::BIGINT AS dealer_count
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.car_dealer.dealer'
      AND repo = 'did:web:kuruma.etzhayyim.com'
    GROUP BY SPLIT_PART(SPLIT_PART(repo, '.etzhayyim.com', 1), 'did:web:', 2)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // MVs first (dependency order)
  for (const mv of [
    'mv_kuruma_dealer_density_by_country',
    'mv_kuruma_recall_per_maker',
    'mv_kuruma_platform_share',
    'mv_kuruma_sales_by_country',
    'mv_kuruma_supply_chain_depth',
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const t of [
    'edge_kuruma_recall_affects', 'edge_kuruma_has_feature', 'edge_kuruma_sold_by',
    'edge_kuruma_unit_model', 'edge_kuruma_assembled_at', 'edge_kuruma_part_supplier',
    'edge_kuruma_contains_part', 'edge_kuruma_uses_platform', 'edge_kuruma_model_by_maker',
    'vertex_kuruma_safety_rating', 'vertex_kuruma_generation', 'vertex_kuruma_feature',
    'vertex_kuruma_review', 'vertex_kuruma_recall', 'vertex_kuruma_sales_monthly',
    'vertex_kuruma_unit', 'vertex_kuruma_plant', 'vertex_kuruma_part',
    'vertex_kuruma_platform', 'vertex_kuruma_trim', 'vertex_kuruma_model',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
