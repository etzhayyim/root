"""Captured from Kysely migration 20260506240000_vertex_hf_model_ingest."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506240000_vertex_hf_model_ingest"
down_revision = 'r_20260506240000_seed_houbun_govinfo_usa_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_model (\n'
         "      vertex_id            VARCHAR PRIMARY KEY,   -- 'hf:model:{repo_id}'\n"
         '      _seq                 BIGINT,\n'
         '      created_date         DATE,\n'
         '\n'
         '      repo_id              VARCHAR NOT NULL,      -- e.g. "google/gemma-4-31B-it"\n'
         '      author               VARCHAR,\n'
         '      sha                  VARCHAR,\n'
         '\n'
         '      -- Primary classification\n'
         '      pipeline_tag         VARCHAR,               -- text-generation | '
         'image-text-to-text | ...\n'
         '      library_name         VARCHAR,               -- transformers | diffusers | gguf | '
         '...\n'
         '      model_type           VARCHAR,               -- from config.model_type (llama / '
         'qwen2 / gemma4 ...)\n'
         '      architecture         VARCHAR,               -- config.architectures[0]\n'
         '      auto_model_class     VARCHAR,               -- transformersInfo.auto_model\n'
         '      inference_state      VARCHAR,               -- warmed | cold | none\n'
         '\n'
         '      -- Scale\n'
         '      num_parameters       BIGINT,                -- safetensors.total (raw param '
         'count)\n'
         '      primary_dtype        VARCHAR,               -- dominant quantization '
         '(BF16/F32/Q4_K_M/...)\n'
         '      used_storage_bytes   BIGINT,                -- usedStorage (sum of sibling file '
         'sizes)\n'
         '\n'
         '      -- Catalog attrs\n'
         '      license              VARCHAR,               -- cardData.license or tags license:*\n'
         '      base_model           VARCHAR,               -- cardData.base_model[0] (first '
         'parent)\n'
         '      trending_score       DOUBLE PRECISION,\n'
         '      downloads_month      BIGINT DEFAULT 0,\n'
         '      likes                INTEGER DEFAULT 0,\n'
         '      gated                BOOLEAN DEFAULT FALSE,\n'
         '      disabled             BOOLEAN DEFAULT FALSE,\n'
         '      private              BOOLEAN DEFAULT FALSE,\n'
         '\n'
         '      -- Raw card data\n'
         '      card_data            VARCHAR,               -- JSON blob of cardData (max 8KB)\n'
         '      spaces_count         INTEGER DEFAULT 0,     -- length of spaces[] array\n'
         '\n'
         '      -- Ingest lifecycle\n'
         "      status               VARCHAR DEFAULT 'pending',\n"
         '      last_scanned_at      TIMESTAMP,\n'
         '      error_message        VARCHAR,\n'
         '      created_at_hf        VARCHAR,               -- original HF createdAt ISO string\n'
         '      last_modified_hf     VARCHAR,               -- HF lastModified ISO string\n'
         '\n'
         '      -- ADR-0095 canonical columns\n'
         "      actor_did            VARCHAR DEFAULT 'did:web:ingest.gftd.ai',\n"
         '      org_did              VARCHAR,\n'
         '      at_did               VARCHAR,\n'
         '      created_at           TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_author ON vertex_hfhub_model (author)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_pipeline ON vertex_hfhub_model (pipeline_tag)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_library ON vertex_hfhub_model (library_name)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_status ON vertex_hfhub_model (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_downloads ON vertex_hfhub_model '
         '(downloads_month DESC)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_params ON vertex_hfhub_model (num_parameters '
         'DESC)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_license ON vertex_hfhub_model (license)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_model_scanned ON vertex_hfhub_model '
         '(last_scanned_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_model_tag (\n'
         '      model_id             VARCHAR NOT NULL,      -- FK vertex_hfhub_model.vertex_id\n'
         '      tag                  VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (model_id, tag)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_mtag_tag ON edge_hfhub_model_tag (tag)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_model_task (\n'
         '      model_id             VARCHAR NOT NULL,\n'
         '      task_category        VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (model_id, task_category)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_mtask_task ON edge_hfhub_model_task (task_category)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_model_language (\n'
         '      model_id             VARCHAR NOT NULL,\n'
         '      lang_code            VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (model_id, lang_code)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_mlang_lang ON edge_hfhub_model_language (lang_code)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_model_base (\n'
         '      model_id             VARCHAR NOT NULL,      -- fine-tuned model vertex_id\n'
         '      base_model_id        VARCHAR NOT NULL,      -- base model repo_id (string, not '
         'FK)\n'
         '      depth                INTEGER DEFAULT 1,     -- lineage depth (1 = direct parent)\n'
         '      PRIMARY KEY (model_id, base_model_id)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_mbase_base ON edge_hfhub_model_base (base_model_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_model_dataset (\n'
         '      model_id             VARCHAR NOT NULL,      -- FK vertex_hfhub_model.vertex_id\n'
         '      dataset_repo_id      VARCHAR NOT NULL,      -- raw dataset name from '
         'cardData.datasets\n'
         '      dataset_vertex_id    VARCHAR,               -- FK vertex_hfhub_dataset.vertex_id '
         '(nullable)\n'
         '      PRIMARY KEY (model_id, dataset_repo_id)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_mds_dataset ON edge_hfhub_model_dataset '
         '(dataset_repo_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_model_task_stats AS\n'
         '    SELECT\n'
         '      pipeline_tag,\n'
         '      COUNT(*)                                                        AS model_count,\n'
         '      SUM(downloads_month)                                            AS '
         'total_downloads,\n'
         '      AVG(downloads_month)                                            AS avg_downloads,\n'
         '      AVG(num_parameters)    FILTER (WHERE num_parameters IS NOT NULL) AS '
         'avg_parameters,\n'
         '      MAX(num_parameters)                                             AS '
         'max_parameters,\n'
         '      SUM(likes)                                                      AS total_likes\n'
         '    FROM vertex_hfhub_model\n'
         '    WHERE pipeline_tag IS NOT NULL\n'
         '    GROUP BY pipeline_tag\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_library_popularity AS\n'
         '    SELECT\n'
         '      library_name,\n'
         '      COUNT(*)              AS model_count,\n'
         '      SUM(downloads_month)  AS total_downloads,\n'
         '      MAX(downloads_month)  AS max_downloads\n'
         '    FROM vertex_hfhub_model\n'
         '    WHERE library_name IS NOT NULL\n'
         '    GROUP BY library_name\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_model_size_bucket AS\n'
         '    SELECT\n'
         '      CASE\n'
         "        WHEN num_parameters IS NULL           THEN 'unknown'\n"
         "        WHEN num_parameters < 1000000000     THEN 'n<1B'\n"
         "        WHEN num_parameters < 7000000000     THEN '1B<n<7B'\n"
         "        WHEN num_parameters < 13000000000    THEN '7B<n<13B'\n"
         "        WHEN num_parameters < 35000000000    THEN '13B<n<35B'\n"
         "        WHEN num_parameters < 70000000000    THEN '35B<n<70B'\n"
         "        ELSE                                      'n>70B'\n"
         '      END                      AS size_bucket,\n'
         '      COUNT(*)                 AS model_count,\n'
         '      AVG(downloads_month)     AS avg_downloads,\n'
         '      SUM(downloads_month)     AS total_downloads\n'
         '    FROM vertex_hfhub_model\n'
         '    GROUP BY 1\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    ALTER TABLE vertex_hfhub_filter\n'
         "    ADD COLUMN IF NOT EXISTS entity_type VARCHAR DEFAULT 'dataset'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_model_size_bucket', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_library_popularity', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_model_task_stats', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_model_dataset', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_model_base', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_model_language', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_model_task', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_model_tag', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_model', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
