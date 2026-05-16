"""Captured from Kysely migration 20260415130300_vertex_ongakuka."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260415130300_vertex_ongakuka"
down_revision = 'r_20260415130200_cohort_lineage_edges'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ongakuka_track (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      project_id       VARCHAR,\n'
         '      title            VARCHAR,\n'
         '      style            VARCHAR,\n'
         '      language         VARCHAR,\n'
         '      bpm              INT,\n'
         '      duration_sec     INT,\n'
         '      status           VARCHAR,\n'
         '      blob_key         VARCHAR,\n'
         '      mime_type        VARCHAR,\n'
         '      model_id         VARCHAR,\n'
         '      seed             BIGINT,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ongakuka_stem (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      track_uri        VARCHAR,\n'
         '      kind             VARCHAR,\n'
         '      blob_key         VARCHAR,\n'
         '      mime_type        VARCHAR,\n'
         '      duration_sec     INT,\n'
         '      loudness_lufs    DOUBLE PRECISION,\n'
         '      actor_did        VARCHAR,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ongakuka_style (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      _seq               BIGINT,\n'
         '      created_date       DATE,\n'
         '      sensitivity_ord    INT,\n'
         '      owner_did          VARCHAR,\n'
         '      name               VARCHAR,\n'
         '      kind               VARCHAR,\n'
         '      prompt             VARCHAR,\n'
         '      embedding_blob_key VARCHAR,\n'
         '      embedding_dim      INT,\n'
         '      embedding_model    VARCHAR,\n'
         '      license            VARCHAR,\n'
         '      created_at         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ongakuka_generation (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      _seq               BIGINT,\n'
         '      created_date       DATE,\n'
         '      sensitivity_ord    INT,\n'
         '      owner_did          VARCHAR,\n'
         '      target_uri         VARCHAR,\n'
         '      stage              VARCHAR,\n'
         '      actor_did          VARCHAR,\n'
         '      model_id           VARCHAR,\n'
         '      params             VARCHAR,\n'
         '      prompt_tokens      INT,\n'
         '      completion_tokens  INT,\n'
         '      audio_sec          DOUBLE PRECISION,\n'
         '      inference_ms       INT,\n'
         '      credits_consumer   INT,\n'
         '      credits_operator   INT,\n'
         '      node               VARCHAR,\n'
         '      status             VARCHAR,\n'
         '      reject_reason      VARCHAR,\n'
         '      created_at         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS edge_ongakuka_has_stem (\n'
         '        edge_id          VARCHAR PRIMARY KEY,\n'
         '        src_vid          VARCHAR,\n'
         '        dst_vid          VARCHAR,\n'
         '        _seq             BIGINT,\n'
         '        created_date     DATE,\n'
         '        sensitivity_ord  INT,\n'
         '        owner_did        VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS edge_ongakuka_used_style (\n'
         '        edge_id          VARCHAR PRIMARY KEY,\n'
         '        src_vid          VARCHAR,\n'
         '        dst_vid          VARCHAR,\n'
         '        _seq             BIGINT,\n'
         '        created_date     DATE,\n'
         '        sensitivity_ord  INT,\n'
         '        owner_did        VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS edge_ongakuka_produced_by (\n'
         '        edge_id          VARCHAR PRIMARY KEY,\n'
         '        src_vid          VARCHAR,\n'
         '        dst_vid          VARCHAR,\n'
         '        _seq             BIGINT,\n'
         '        created_date     DATE,\n'
         '        sensitivity_ord  INT,\n'
         '        owner_did        VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS edge_ongakuka_generated_by (\n'
         '        edge_id          VARCHAR PRIMARY KEY,\n'
         '        src_vid          VARCHAR,\n'
         '        dst_vid          VARCHAR,\n'
         '        _seq             BIGINT,\n'
         '        created_date     DATE,\n'
         '        sensitivity_ord  INT,\n'
         '        owner_did        VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS edge_ongakuka_regen_lineage (\n'
         '        edge_id          VARCHAR PRIMARY KEY,\n'
         '        src_vid          VARCHAR,\n'
         '        dst_vid          VARCHAR,\n'
         '        _seq             BIGINT,\n'
         '        created_date     DATE,\n'
         '        sensitivity_ord  INT,\n'
         '        owner_did        VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_ongakuka_regen_lineage', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_ongakuka_generated_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_ongakuka_produced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_ongakuka_used_style', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_ongakuka_has_stem', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_ongakuka_generation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_ongakuka_style', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_ongakuka_stem', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_ongakuka_track', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
