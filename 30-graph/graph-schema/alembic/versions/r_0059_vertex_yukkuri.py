"""Captured from Kysely migration 0059_vertex_yukkuri."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0059_vertex_yukkuri"
down_revision = 'r_0057_vertex_hospitality_actor'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_yukkuri_video (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      project_id       VARCHAR,\n'
         '      title            VARCHAR,\n'
         '      topic            VARCHAR,\n'
         '      language         VARCHAR,\n'
         '      target_sec       INT,\n'
         '      duration_sec     INT,\n'
         '      resolution       VARCHAR,\n'
         '      fps              INT,\n'
         '      status           VARCHAR,\n'
         '      blob_key         VARCHAR,\n'
         '      mime_type        VARCHAR,\n'
         '      seed             BIGINT,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_yukkuri_scene (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      video_uri        VARCHAR,\n'
         '      idx              INT,\n'
         '      start_sec        DOUBLE PRECISION,\n'
         '      duration_sec     DOUBLE PRECISION,\n'
         '      summary          VARCHAR,\n'
         '      background_asset_uri VARCHAR,\n'
         '      bgm_asset_uri    VARCHAR,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_yukkuri_line (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      video_uri        VARCHAR,\n'
         '      scene_uri        VARCHAR,\n'
         '      idx              INT,\n'
         '      speaker          VARCHAR,\n'
         '      text             VARCHAR,\n'
         '      emotion          VARCHAR,\n'
         '      voice_preset     VARCHAR,\n'
         '      voice_blob_key   VARCHAR,\n'
         '      mime_type        VARCHAR,\n'
         '      duration_sec     DOUBLE PRECISION,\n'
         '      phoneme_blob_key VARCHAR,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_yukkuri_asset (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  INT,\n'
         '      owner_did        VARCHAR,\n'
         '      video_uri        VARCHAR,\n'
         '      scene_uri        VARCHAR,\n'
         '      kind             VARCHAR,\n'
         '      blob_key         VARCHAR,\n'
         '      mime_type        VARCHAR,\n'
         '      width            INT,\n'
         '      height           INT,\n'
         '      duration_sec     DOUBLE PRECISION,\n'
         '      loudness_lufs    DOUBLE PRECISION,\n'
         '      actor_did        VARCHAR,\n'
         '      source_ref       VARCHAR,\n'
         '      license          VARCHAR,\n'
         '      created_at       VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_yukkuri_generation (\n'
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
         '      video_sec          DOUBLE PRECISION,\n'
         '      render_backend     VARCHAR,\n'
         '      inference_ms       INT,\n'
         '      render_ms          INT,\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_has_scene (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_has_line (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_uses_asset (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_voiced_by (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_produced_by (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_generated_by (\n'
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
         '      CREATE TABLE IF NOT EXISTS edge_yukkuri_regen_lineage (\n'
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

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_yukkuri_regen_lineage', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_generated_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_produced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_voiced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_uses_asset', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_has_line', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_yukkuri_has_scene', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_yukkuri_generation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_yukkuri_asset', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_yukkuri_line', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_yukkuri_scene', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_yukkuri_video', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
