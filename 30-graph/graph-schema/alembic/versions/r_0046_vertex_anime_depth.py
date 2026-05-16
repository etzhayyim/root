"""Captured from Kysely migration 0046_vertex_anime_depth."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0046_vertex_anime_depth"
down_revision = 'r_0045_vertex_kuruma_depth'
branch_labels = None
depends_on = None

UP = [{'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_title (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    external_ids    VARCHAR,\n'
         '    title_en        VARCHAR,\n'
         '    title_ja        VARCHAR,\n'
         '    type            VARCHAR,\n'
         '    episodes        INT,\n'
         '    status          VARCHAR,\n'
         '    season          VARCHAR,\n'
         '    year            INT,\n'
         '    studio_did      VARCHAR,\n'
         '    committee_did   VARCHAR,\n'
         '    franchise_did   VARCHAR,\n'
         '    source_did      VARCHAR,\n'
         '    picture_url     VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_franchise (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    wikidata_qid VARCHAR,\n'
         '    first_year INT,\n'
         '    last_year INT,\n'
         '    work_count INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_studio (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name VARCHAR,\n'
         '    country VARCHAR,\n'
         '    wikidata_qid VARCHAR,\n'
         '    legal_entity_did VARCHAR,\n'
         '    founded_year INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_committee (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    year            INT,\n'
         '    member_count    INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_staff (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    name_ja         VARCHAR,\n'
         '    staff_role      VARCHAR,\n'
         '    wikidata_qid    VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    legal_entity_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_character (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    name_ja         VARCHAR,\n'
         '    character_role  VARCHAR,\n'
         '    gender          VARCHAR,\n'
         '    voice_actor_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_episode (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    episode_number  INT,\n'
         '    title_en        VARCHAR,\n'
         '    title_ja        VARCHAR,\n'
         '    aired_date      DATE,\n'
         '    duration_sec    INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_broadcaster (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    name            VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    wikidata_qid    VARCHAR,\n'
         '    legal_entity_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_distribution (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    platform_did    VARCHAR,\n'
         '    country         VARCHAR,\n'
         '    license_start   DATE,\n'
         '    license_end     DATE,\n'
         '    sub_lang        VARCHAR,\n'
         '    dub_lang        VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_source (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    source_title    VARCHAR,\n'
         '    author_did      VARCHAR,\n'
         '    publisher_did   VARCHAR,\n'
         '    first_year      INT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_song (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    seq             INT,\n'
         '    name            VARCHAR,\n'
         '    artist          VARCHAR,\n'
         '    composer_did    VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_merchandise (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    sku             VARCHAR,\n'
         '    kind            VARCHAR,\n'
         '    manufacturer_did VARCHAR,\n'
         '    msrp_jpy        BIGINT,\n'
         '    release_date    DATE\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_anime_ratings (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did       VARCHAR,\n'
         '    source          VARCHAR,\n'
         '    rating_numeric  DOUBLE PRECISION,\n'
         '    rating_scale    VARCHAR,\n'
         '    votes_count     BIGINT,\n'
         '    snapshot_date   DATE\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_produced_by (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    production_role VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_funded_by (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_committee_member (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    investment_share DOUBLE PRECISION\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_part_of_franchise (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_stars_character (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_voiced_by (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_directed_by (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    credit_role VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_aired_on (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    start_date DATE,\n'
         '    end_date DATE,\n'
         '    slot VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_licensed_to (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_adapted_from (\n'
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
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_anime_has_song (\n'
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
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_studio_production_count AS\n'
         '    SELECT s.vertex_id AS studio_did,\n'
         '           s.name      AS studio_name,\n'
         '           COUNT(DISTINCT t.vertex_id) AS title_count,\n'
         '           MIN(t.year)                  AS first_year,\n'
         '           MAX(t.year)                  AS last_year\n'
         '    FROM vertex_anime_studio s\n'
         '    LEFT JOIN edge_anime_produced_by p ON p.dst_vid = s.vertex_id\n'
         '    LEFT JOIN vertex_anime_title   t ON t.vertex_id = p.src_vid\n'
         '    GROUP BY s.vertex_id, s.name',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_distribution_by_country AS\n'
         '    SELECT country,\n'
         '           COUNT(DISTINCT title_did) AS title_count,\n'
         '           COUNT(DISTINCT platform_did) AS platform_count\n'
         '    FROM vertex_anime_distribution\n'
         '    GROUP BY country',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_character_depth AS\n'
         '    SELECT title_did, COUNT(*)::BIGINT AS character_count\n'
         '    FROM vertex_anime_character\n'
         '    GROUP BY title_did',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_committee_network AS\n'
         '    SELECT cm.dst_vid AS legal_entity_did,\n'
         '           COUNT(DISTINCT cm.src_vid) AS committee_count\n'
         '    FROM edge_anime_committee_member cm\n'
         '    GROUP BY cm.dst_vid',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_source_adaptation_ratio AS\n'
         '    SELECT kind AS source_kind,\n'
         '           COUNT(DISTINCT title_did) AS adapted_title_count\n'
         '    FROM vertex_anime_source\n'
         '    GROUP BY kind',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_anime_source_adaptation_ratio', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_anime_committee_network', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_anime_character_depth', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_anime_distribution_by_country', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_anime_studio_production_count', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_has_song', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_adapted_from', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_licensed_to', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_aired_on', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_directed_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_voiced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_stars_character', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_part_of_franchise', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_committee_member', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_funded_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_anime_produced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_ratings', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_merchandise', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_song', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_source', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_distribution', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_broadcaster', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_episode', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_character', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_staff', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_committee', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_studio', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_franchise', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_anime_title', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
