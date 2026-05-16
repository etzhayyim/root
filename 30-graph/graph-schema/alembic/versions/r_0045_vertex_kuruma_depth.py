"""Captured from Kysely migration 0045_vertex_kuruma_depth."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0045_vertex_kuruma_depth"
down_revision = 'r_0044_vertex_repo_commit_seq_index'
branch_labels = None
depends_on = None

UP = [{'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_model (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    maker_did       VARCHAR,\n'
         '    platform_did    VARCHAR,\n'
         '    generation_did  VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    name_ja         VARCHAR,\n'
         '    body_type       VARCHAR,\n'
         '    first_year      INT,\n'
         '    last_year       INT,\n'
         '    country         VARCHAR,\n'
         '    wikidata_qid    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_trim (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_did       VARCHAR,\n'
         '    variant         VARCHAR,\n'
         '    engine_spec     VARCHAR,\n'
         '    transmission    VARCHAR,\n'
         '    drivetrain      VARCHAR,\n'
         '    msrp_currency   VARCHAR,\n'
         '    msrp_amount     DOUBLE PRECISION,\n'
         '    market          VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_platform (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    maker_did       VARCHAR,\n'
         '    shared_with_dids VARCHAR,\n'
         '    architecture    VARCHAR,\n'
         '    launch_year     INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_part (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    part_number     VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    category        VARCHAR,\n'
         '    supplier_did    VARCHAR,\n'
         '    tier            INT,\n'
         '    country_of_origin VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_plant (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    operator_did    VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    region          VARCHAR,\n'
         '    city            VARCHAR,\n'
         '    capacity_units_year BIGINT,\n'
         '    opened_year     INT,\n'
         '    closed_year     INT,\n'
         '    wikidata_qid    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_unit (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    vin             VARCHAR,\n'
         '    model_did       VARCHAR,\n'
         '    trim_did        VARCHAR,\n'
         '    plant_did       VARCHAR,\n'
         '    manufactured_date DATE,\n'
         '    country_market  VARCHAR,\n'
         '    first_owner_country VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_sales_monthly (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_did       VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    year            INT,\n'
         '    month           INT,\n'
         '    units_sold      BIGINT,\n'
         '    revenue_usd     DOUBLE PRECISION,\n'
         '    source          VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_recall (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    campaign_id     VARCHAR,\n'
         '    regulator       VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    announced_date  DATE,\n'
         '    defect          VARCHAR,\n'
         '    remedy          VARCHAR,\n'
         '    affected_units_est BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_review (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_did       VARCHAR,\n'
         '    reviewer_did    VARCHAR,\n'
         '    source          VARCHAR,\n'
         '    title           VARCHAR,\n'
         '    score_numeric   DOUBLE PRECISION,\n'
         '    score_scale     VARCHAR,\n'
         '    published_date  DATE,\n'
         '    language        VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_feature (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    category        VARCHAR,\n'
         '    iso_standard    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_generation (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_family_did VARCHAR,\n'
         '    generation_seq  INT,\n'
         '    start_year      INT,\n'
         '    end_year        INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kuruma_safety_rating (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_did       VARCHAR,\n'
         '    authority       VARCHAR,\n'
         '    rating          VARCHAR,\n'
         '    tested_year     INT,\n'
         '    adult_occupant  DOUBLE PRECISION,\n'
         '    child_occupant  DOUBLE PRECISION,\n'
         '    pedestrian      DOUBLE PRECISION,\n'
         '    safety_assist   DOUBLE PRECISION\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_model_by_maker (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    maker_role VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_uses_platform (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR\n'
         '    \n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_contains_part (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    quantity INT,\n'
         '    position VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_part_supplier (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    tier INT,\n'
         '    supply_start DATE,\n'
         '    supply_end DATE\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_assembled_at (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    assembly_date DATE\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_unit_model (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR\n'
         '    \n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_sold_by (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    sale_date DATE,\n'
         '    price_usd DOUBLE PRECISION\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_has_feature (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    standard BOOLEAN,\n'
         '    optional_group VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_kuruma_recall_affects (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    model_did VARCHAR,\n'
         '    affected_count BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_supply_chain_depth AS\n'
         '    SELECT m.vertex_id AS model_did,\n'
         '           COUNT(DISTINCT cp.dst_vid) AS part_count,\n'
         '           COUNT(DISTINCT ps.dst_vid) AS supplier_count,\n'
         '           COALESCE(MAX(ps.tier), 0)   AS max_tier\n'
         '    FROM vertex_kuruma_model m\n'
         '    LEFT JOIN edge_kuruma_contains_part cp ON cp.src_vid = m.vertex_id\n'
         '    LEFT JOIN edge_kuruma_part_supplier ps ON ps.src_vid = cp.dst_vid\n'
         '    GROUP BY m.vertex_id',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_sales_by_country AS\n'
         '    SELECT s.model_did, s.country, s.year,\n'
         '           SUM(s.units_sold)::BIGINT AS units_sold_year,\n'
         '           SUM(s.revenue_usd)        AS revenue_year\n'
         '    FROM vertex_kuruma_sales_monthly s\n'
         '    GROUP BY s.model_did, s.country, s.year',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_platform_share AS\n'
         '    SELECT p.vertex_id AS platform_did,\n'
         '           p.name       AS platform_name,\n'
         '           COUNT(DISTINCT m.vertex_id) AS model_count\n'
         '    FROM vertex_kuruma_platform p\n'
         '    LEFT JOIN vertex_kuruma_model m ON m.platform_did = p.vertex_id\n'
         '    GROUP BY p.vertex_id, p.name',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_recall_per_maker AS\n'
         '    SELECT m.maker_did,\n'
         '           COUNT(DISTINCT r.vertex_id) AS recall_count,\n'
         '           SUM(r.affected_units_est)::BIGINT AS total_affected_units\n'
         '    FROM vertex_kuruma_recall r\n'
         '    JOIN edge_kuruma_recall_affects ra ON ra.src_vid = r.vertex_id\n'
         '    JOIN vertex_kuruma_model m ON m.vertex_id = ra.dst_vid\n'
         '    GROUP BY m.maker_did',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kuruma_dealer_density_by_country AS\n'
         '    SELECT\n'
         "      SPLIT_PART(SPLIT_PART(repo, '.gftd.ai', 1), 'did:web:', 2) AS app_host,\n"
         '      CAST(NULL AS VARCHAR) AS country,\n'
         '      COUNT(*)::BIGINT AS dealer_count\n'
         '    FROM vertex_repo_record\n'
         "    WHERE collection = 'ai.gftd.apps.car_dealer.dealer'\n"
         "      AND repo = 'did:web:kuruma.gftd.ai'\n"
         "    GROUP BY SPLIT_PART(SPLIT_PART(repo, '.gftd.ai', 1), 'did:web:', 2)",
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kuruma_dealer_density_by_country', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kuruma_recall_per_maker', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kuruma_platform_share', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kuruma_sales_by_country', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kuruma_supply_chain_depth', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_recall_affects', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_has_feature', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_sold_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_unit_model', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_assembled_at', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_part_supplier', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_contains_part', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_uses_platform', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_kuruma_model_by_maker', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_safety_rating', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_generation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_feature', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_review', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_recall', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_sales_monthly', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_unit', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_plant', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_part', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_platform', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_trim', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kuruma_model', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
