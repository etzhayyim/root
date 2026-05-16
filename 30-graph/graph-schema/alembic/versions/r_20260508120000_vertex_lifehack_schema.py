"""Captured from Kysely migration 20260508120000_vertex_lifehack_schema."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508120000_vertex_lifehack_schema"
down_revision = 'r_20260508120000_vertex_lawfirm_admin_app_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_topic (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      topic_id varchar NOT NULL,\n'
         '      category varchar NOT NULL,\n'
         '      title_ja varchar,\n'
         '      title_en varchar,\n'
         '      summary_ja varchar,\n'
         '      summary_en varchar,\n'
         '      parent_topic_id varchar,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_tip (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      tip_id varchar NOT NULL,\n'
         '      topic_id varchar NOT NULL,\n'
         '      body_ja varchar,\n'
         '      body_en varchar,\n'
         '      effectiveness_score double precision,\n'
         '      cost_jpy_min double precision,\n'
         '      cost_jpy_max double precision,\n'
         '      difficulty varchar,\n'
         '      source_url varchar,\n'
         '      source_authority varchar,\n'
         '      evidence_summary varchar,\n'
         '      llm_model varchar,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_product (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      product_id varchar NOT NULL,\n'
         '      name varchar NOT NULL,\n'
         '      brand varchar,\n'
         '      category varchar NOT NULL,\n'
         '      source_type varchar NOT NULL,\n'
         '      price_jpy_min double precision,\n'
         '      price_jpy_max double precision,\n'
         '      amazon_search_keyword varchar,\n'
         '      asin varchar,\n'
         '      pse_certified boolean,\n'
         '      tsukuru_cad_model_did varchar,\n'
         '      tsukuru_factory_did varchar,\n'
         '      tsukuru_production_order_nsid varchar,\n'
         '      estimated_make_cost_jpy double precision,\n'
         '      estimated_make_time_hours double precision,\n'
         '      notes_ja varchar,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_environment_reading (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      reading_id varchar NOT NULL,\n'
         '      reporter_did varchar,\n'
         '      location_h3 varchar,\n'
         '      humidity_pct double precision,\n'
         '      temp_c double precision,\n'
         '      pm25_ugm3 double precision,\n'
         '      ts_ms bigint NOT NULL,\n'
         '      source varchar,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_post_log (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      post_id varchar NOT NULL,\n'
         '      tip_id varchar NOT NULL,\n'
         '      topic_id varchar NOT NULL,\n'
         '      bsky_uri varchar,\n'
         '      bsky_cid varchar,\n'
         '      posted_at_ms bigint NOT NULL,\n'
         '      engagement_score double precision,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lifehack_user_query (\n'
         '      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord '
         'int, owner_did varchar,\n'
         '      query_id varchar NOT NULL,\n'
         '      asker_did varchar,\n'
         '      query_text varchar,\n'
         '      answered_tip_ids varchar,\n'
         '      llm_model varchar,\n'
         '      latency_ms int,\n'
         '      status varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_lifehack_tip_solves_topic (\n'
         '      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, '
         'owner_did varchar,\n'
         '      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_lifehack_tip_recommends_product (\n'
         '      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, '
         'owner_did varchar,\n'
         '      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_lifehack_topic_relates_to (\n'
         '      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, '
         'owner_did varchar,\n'
         '      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,\n'
         '      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_top_tips_by_topic AS\n'
         '      SELECT\n'
         '        t.topic_id,\n'
         '        t.tip_id,\n'
         '        t.body_ja,\n'
         '        t.effectiveness_score,\n'
         '        t.cost_jpy_min,\n'
         '        t.difficulty,\n'
         '        t.source_authority\n'
         '      FROM vertex_lifehack_tip t\n'
         "      WHERE t.status = 'active'\n"
         '        AND t.effectiveness_score IS NOT NULL;\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_recently_posted AS\n'
         '      SELECT\n'
         '        tip_id,\n'
         '        topic_id,\n'
         '        MAX(posted_at_ms) AS last_posted_at_ms,\n'
         '        COUNT(*) AS post_count\n'
         '      FROM vertex_lifehack_post_log\n'
         "      WHERE status = 'active'\n"
         '      GROUP BY tip_id, topic_id;\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_static_risk_now AS\n'
         '      SELECT\n'
         '        location_h3,\n'
         '        COUNT(*) AS reading_count,\n'
         '        AVG(humidity_pct) AS avg_humidity_pct,\n'
         '        MIN(humidity_pct) AS min_humidity_pct,\n'
         '        MAX(ts_ms) AS last_ts_ms\n'
         '      FROM vertex_lifehack_environment_reading\n'
         "      WHERE status = 'active'\n"
         '        AND humidity_pct IS NOT NULL\n'
         '        AND humidity_pct < 40.0\n'
         '      GROUP BY location_h3;\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_trending_topic AS\n'
         '      SELECT\n'
         '        topic_id,\n'
         '        COUNT(*) AS post_count,\n'
         '        SUM(COALESCE(engagement_score, 0)) AS engagement_total,\n'
         '        MAX(posted_at_ms) AS last_posted_at_ms\n'
         '      FROM vertex_lifehack_post_log\n'
         "      WHERE status = 'active'\n"
         '      GROUP BY topic_id;\n'
         '  ',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_topic TO root', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_topic TO kaisya_app', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_tip TO root', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_tip TO kaisya_app', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_product TO root', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_product TO kaisya_app', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_environment_reading TO root',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_environment_reading TO kaisya_app',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_post_log TO root', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_post_log TO kaisya_app',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_user_query TO root', 'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON vertex_lifehack_user_query TO kaisya_app',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_tip_solves_topic TO root',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_tip_solves_topic TO kaisya_app',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_tip_recommends_product TO root',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_tip_recommends_product TO kaisya_app',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_topic_relates_to TO root',
  'parameters': []},
 {'sql': 'GRANT SELECT, INSERT, UPDATE ON edge_lifehack_topic_relates_to TO kaisya_app',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_trending_topic', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_static_risk_now', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_recently_posted', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_top_tips_by_topic', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_lifehack_topic_relates_to', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_lifehack_tip_recommends_product', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_lifehack_tip_solves_topic', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_user_query', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_post_log', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_environment_reading', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_product', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_tip', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lifehack_topic', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
