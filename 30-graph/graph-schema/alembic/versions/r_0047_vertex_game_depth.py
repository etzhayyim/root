"""Captured from Kysely migration 0047_vertex_game_depth."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0047_vertex_game_depth"
down_revision = 'r_0046_vertex_anime_depth'
branch_labels = None
depends_on = None

UP = [{'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_title (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    external_ids   VARCHAR,\n'
         '    title_en       VARCHAR,\n'
         '    title_ja       VARCHAR,\n'
         '    release_year   INT,\n'
         '    first_release_date DATE,\n'
         '    franchise_did  VARCHAR,\n'
         '    engine_did     VARCHAR,\n'
         '    developer_did  VARCHAR,\n'
         '    publisher_did  VARCHAR,\n'
         '    genre_did      VARCHAR,\n'
         '    mode_did       VARCHAR,\n'
         '    rating_esrb    VARCHAR,\n'
         '    rating_cero    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_franchise (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    wikidata_qid VARCHAR,\n'
         '    first_year INT,\n'
         '    title_count INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_platform (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    kind VARCHAR,\n'
         '    maker_did VARCHAR,\n'
         '    launch_year INT,\n'
         '    wikidata_qid VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_engine (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    version VARCHAR,\n'
         '    maker_did VARCHAR,\n'
         '    license VARCHAR,\n'
         '    wikidata_qid VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_store (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    operator_did VARCHAR,\n'
         '    country_restrictions VARCHAR,\n'
         '    wikidata_qid VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_character (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    name_ja         VARCHAR,\n'
         '    character_role  VARCHAR,\n'
         '    class           VARCHAR,\n'
         '    first_appearance_title_did VARCHAR,\n'
         '    voice_actor_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_map (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    parent_map_did  VARCHAR,\n'
         '    coord_system    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_item (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    rarity          VARCHAR,\n'
         '    tradeable       BOOLEAN,\n'
         '    msrp_usd        DOUBLE PRECISION\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_quest (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    act             VARCHAR,\n'
         '    prereq_quest_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_dlc (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    release_date    DATE,\n'
         '    msrp_usd        DOUBLE PRECISION\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_sales_monthly (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    region          VARCHAR,\n'
         '    year            INT,\n'
         '    month           INT,\n'
         '    units_sold      BIGINT,\n'
         '    revenue_usd     DOUBLE PRECISION,\n'
         '    source          VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_esports_event (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    year            INT,\n'
         '    country         VARCHAR,\n'
         '    prize_pool_usd  DOUBLE PRECISION,\n'
         '    organizer_did   VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_genre (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    parent_genre_did VARCHAR,\n'
         '    iso_slot VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_mode (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    kind VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_developed_by (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    developer_role VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_published_by (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    region VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_runs_on (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    launch_year INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_uses_engine (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    engine_version VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_sold_on (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    price_usd DOUBLE PRECISION,\n'
         '    available_from DATE,\n'
         '    available_to DATE\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_has_character (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_has_map (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_has_item (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_has_quest (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_part_of_franchise (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_has_genre (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    is_primary BOOLEAN\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_esports_for (\n'
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
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_platform_share AS\n'
         '    SELECT p.vertex_id AS platform_did,\n'
         '           p.name       AS platform_name,\n'
         '           COUNT(DISTINCT ro.src_vid) AS title_count\n'
         '    FROM vertex_game_platform p\n'
         '    LEFT JOIN edge_game_runs_on ro ON ro.dst_vid = p.vertex_id\n'
         '    GROUP BY p.vertex_id, p.name',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_engine_usage AS\n'
         '    SELECT e.vertex_id AS engine_did,\n'
         '           e.name       AS engine_name,\n'
         '           COUNT(DISTINCT ue.src_vid) AS title_count\n'
         '    FROM vertex_game_engine e\n'
         '    LEFT JOIN edge_game_uses_engine ue ON ue.dst_vid = e.vertex_id\n'
         '    GROUP BY e.vertex_id, e.name',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_sales_by_region AS\n'
         '    SELECT region, year,\n'
         '           SUM(units_sold)::BIGINT AS units_year,\n'
         '           SUM(revenue_usd)         AS revenue_year,\n'
         '           COUNT(DISTINCT title_did) AS title_count\n'
         '    FROM vertex_game_sales_monthly\n'
         '    GROUP BY region, year',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_character_depth AS\n'
         '    SELECT title_did, COUNT(*)::BIGINT AS character_count\n'
         '    FROM vertex_game_character\n'
         '    GROUP BY title_did',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_franchise_lifecycle AS\n'
         '    SELECT f.vertex_id AS franchise_did,\n'
         '           f.name       AS franchise_name,\n'
         '           COUNT(DISTINCT t.vertex_id) AS title_count,\n'
         '           MIN(t.release_year) AS first_year,\n'
         '           MAX(t.release_year) AS last_year\n'
         '    FROM vertex_game_franchise f\n'
         '    LEFT JOIN vertex_game_title t ON t.franchise_did = f.vertex_id\n'
         '    GROUP BY f.vertex_id, f.name',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_esports_per_genre AS\n'
         '    SELECT g.vertex_id AS genre_did,\n'
         '           g.name       AS genre_name,\n'
         '           COUNT(DISTINCT ev.vertex_id) AS esports_event_count,\n'
         '           SUM(ev.prize_pool_usd)        AS total_prize_pool_usd\n'
         '    FROM vertex_game_genre g\n'
         '    LEFT JOIN edge_game_has_genre hg ON hg.dst_vid = g.vertex_id\n'
         '    LEFT JOIN vertex_game_esports_event ev ON ev.title_did = hg.src_vid\n'
         '    GROUP BY g.vertex_id, g.name',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_esports_per_genre', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_franchise_lifecycle', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_character_depth', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_sales_by_region', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_engine_usage', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_platform_share', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_esports_for', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_has_genre', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_part_of_franchise', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_has_quest', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_has_item', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_has_map', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_has_character', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_sold_on', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_uses_engine', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_runs_on', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_published_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_developed_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_mode', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_genre', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_esports_event', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_sales_monthly', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_dlc', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_quest', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_item', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_map', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_character', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_store', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_engine', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_platform', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_franchise', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_title', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
