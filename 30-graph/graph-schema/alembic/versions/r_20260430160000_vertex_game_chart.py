"""Captured from Kysely migration 20260430160000_vertex_game_chart."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430160000_vertex_game_chart"
down_revision = 'r_20260430150000_fix_actor_registry_canonical_did'
branch_labels = None
depends_on = None

UP = [{'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_chart_snapshot (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    title_did        VARCHAR,\n'
         '    source           VARCHAR,\n'
         '    week_start       DATE,\n'
         '    rank             INTEGER,\n'
         '    rank_prev        INTEGER,\n'
         '    rank_delta       INTEGER,\n'
         '    external_id      VARCHAR,\n'
         '    title_hint       VARCHAR,\n'
         '    score_source     DOUBLE PRECISION,\n'
         '    players_2w       BIGINT,\n'
         '    price_usd        DOUBLE PRECISION,\n'
         '    metadata_json    VARCHAR,\n'
         '    fetched_at       VARCHAR,\n'
         '    actor_did        VARCHAR,\n'
         '    org_did          VARCHAR,\n'
         '    created_at       VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_game_chart_analysis (\n'
         '    vertex_id       VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    week_start           DATE,\n'
         '    source               VARCHAR,\n'
         '    analysis_ja          VARCHAR,\n'
         '    analysis_en          VARCHAR,\n'
         '    top_genre            VARCHAR,\n'
         '    rising_titles_json   VARCHAR,\n'
         '    falling_titles_json  VARCHAR,\n'
         '    new_entries_json     VARCHAR,\n'
         '    insight_tags_json    VARCHAR,\n'
         '    social_post_rkey     VARCHAR,\n'
         '    model_id             VARCHAR,\n'
         '    actor_did            VARCHAR,\n'
         '    org_did              VARCHAR,\n'
         '    created_at           VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_game_charted_at (\n'
         '    edge_id         VARCHAR PRIMARY KEY,\n'
         '    _seq            BIGINT,\n'
         '    created_date    DATE,\n'
         '    sensitivity_ord BIGINT,\n'
         '    owner_did       VARCHAR,\n'
         '    src_vid         VARCHAR,\n'
         '    dst_vid         VARCHAR,\n'
         '    rank        INTEGER,\n'
         '    source      VARCHAR,\n'
         '    week_start  DATE,\n'
         '    created_at  VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_chart_snapshot_source_week\n'
         '    ON vertex_game_chart_snapshot (source, week_start)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_chart_snapshot_title\n'
         '    ON vertex_game_chart_snapshot (title_did)\n'
         '    WHERE title_did IS NOT NULL',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_chart_analysis_week\n'
         '    ON vertex_game_chart_analysis (week_start, source)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_charted_at_src\n'
         '    ON edge_game_charted_at (src_vid)',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_rank_trend AS\n'
         '    SELECT\n'
         '      title_did,\n'
         '      source,\n'
         '      COUNT(*)                  AS weeks_charted,\n'
         '      CAST(AVG(rank) AS DOUBLE PRECISION) AS avg_rank,\n'
         '      MIN(rank)                 AS peak_rank,\n'
         '      MAX(rank_delta)           AS best_rise,\n'
         '      MIN(rank_delta)           AS worst_fall,\n'
         '      MAX(week_start)           AS last_charted_week\n'
         '    FROM vertex_game_chart_snapshot\n'
         '    WHERE title_did IS NOT NULL\n'
         '    GROUP BY title_did, source',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_genre_chart_dominance AS\n'
         '    SELECT\n'
         '      g.dst_vid                 AS genre_did,\n'
         '      s.source,\n'
         '      COUNT(DISTINCT s.title_did) AS titles_in_chart,\n'
         '      CAST(AVG(s.rank) AS DOUBLE PRECISION) AS avg_rank,\n'
         '      MIN(s.rank)               AS top_rank,\n'
         '      MAX(s.week_start)         AS last_seen_week\n'
         '    FROM vertex_game_chart_snapshot s\n'
         '    JOIN edge_game_has_genre g ON g.src_vid = s.title_did\n'
         '    WHERE s.title_did IS NOT NULL AND s.rank <= 20\n'
         '    GROUP BY g.dst_vid, s.source',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_genre_chart_dominance', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_rank_trend', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_game_charted_at', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_chart_analysis', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_game_chart_snapshot', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
