"""Captured from Kysely migration 20260429100000_vertex_lda_coverage_schema."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429100000_vertex_lda_coverage_schema"
down_revision = 'r_20260429100000_vertex_hanrei_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lda_viewpoint (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      sensitivity_ord   INTEGER DEFAULT 0,\n'
         '      owner_did         VARCHAR,\n'
         '      actor_did         VARCHAR,\n'
         '      org_did           VARCHAR,\n'
         '      created_at        TIMESTAMP,\n'
         '      viewpoint_kind    VARCHAR,\n'
         '      description       VARCHAR,\n'
         '      signal_vocab_size INTEGER DEFAULT 0,\n'
         '      active            BOOLEAN DEFAULT true\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lda_signal (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      _seq               BIGINT,\n'
         '      sensitivity_ord    INTEGER DEFAULT 0,\n'
         '      owner_did          VARCHAR,\n'
         '      actor_did          VARCHAR,\n'
         '      org_did            VARCHAR,\n'
         '      created_at         TIMESTAMP,\n'
         '      viewpoint_vid      VARCHAR,\n'
         '      signal_token       VARCHAR,\n'
         '      signal_kind        VARCHAR,\n'
         '      source_collection  VARCHAR,\n'
         '      extraction_expr    VARCHAR,\n'
         '      doc_frequency      INTEGER DEFAULT 0,\n'
         '      idf_score          DOUBLE PRECISION DEFAULT 0.0\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_lda_signal_viewpoint ON vertex_lda_signal(viewpoint_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_lda_signal_token ON vertex_lda_signal(signal_token)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lda_model (\n'
         '      vertex_id      VARCHAR PRIMARY KEY,\n'
         '      _seq           BIGINT,\n'
         '      sensitivity_ord INTEGER DEFAULT 0,\n'
         '      owner_did      VARCHAR,\n'
         '      actor_did      VARCHAR,\n'
         '      org_did        VARCHAR,\n'
         '      created_at     TIMESTAMP,\n'
         '      model_slug     VARCHAR,\n'
         '      k_topics       INTEGER DEFAULT 8,\n'
         '      alpha          DOUBLE PRECISION DEFAULT 0.1,\n'
         '      beta           DOUBLE PRECISION DEFAULT 0.01,\n'
         '      trained_at     TIMESTAMP,\n'
         '      signal_count   INTEGER DEFAULT 0,\n'
         '      record_count   INTEGER DEFAULT 0,\n'
         '      perplexity     DOUBLE PRECISION DEFAULT 0.0,\n'
         "      status         VARCHAR DEFAULT 'training'\n"
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_lda_model_status ON vertex_lda_model(status)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lda_model_latest AS\n'
         '    SELECT vertex_id AS model_vid,\n'
         '           model_slug,\n'
         '           k_topics,\n'
         '           alpha,\n'
         '           beta,\n'
         '           trained_at,\n'
         '           signal_count,\n'
         '           record_count,\n'
         '           perplexity,\n'
         "           'lda_gibbs_full' AS training_corpus\n"
         '    FROM vertex_lda_model\n'
         "    WHERE status = 'converged'\n"
         '    ORDER BY trained_at DESC\n'
         '    LIMIT 1\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_lda_topic (\n'
         '      vertex_id            VARCHAR PRIMARY KEY,\n'
         '      _seq                 BIGINT,\n'
         '      sensitivity_ord      INTEGER DEFAULT 0,\n'
         '      owner_did            VARCHAR,\n'
         '      actor_did            VARCHAR,\n'
         '      org_did              VARCHAR,\n'
         '      created_at           TIMESTAMP,\n'
         '      model_vid            VARCHAR,\n'
         '      topic_index          INTEGER,\n'
         '      primary_viewpoint_vid VARCHAR,\n'
         '      topic_label          VARCHAR,\n'
         '      coherence_score      DOUBLE PRECISION DEFAULT 0.0,\n'
         '      top_signal_count     INTEGER DEFAULT 0,\n'
         '      entity_kind_hint     VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_lda_topic_model ON vertex_lda_topic(model_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_topic_signal_weight (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      sensitivity_ord INTEGER DEFAULT 0,\n'
         '      owner_did       VARCHAR,\n'
         '      actor_did       VARCHAR,\n'
         '      org_did         VARCHAR,\n'
         '      created_at      TIMESTAMP,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      model_vid       VARCHAR,\n'
         '      signal_token    VARCHAR,\n'
         '      weight          DOUBLE PRECISION DEFAULT 0.0\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_topic_signal_src ON edge_topic_signal_weight(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_topic_signal_model ON edge_topic_signal_weight(model_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lda_topic_top_signals AS\n'
         '    SELECT\n'
         '      src_vid AS topic_vid,\n'
         '      COUNT(*) AS signal_count,\n'
         '      SUM(weight) AS total_weight,\n'
         '      MAX(weight) AS top_weight\n'
         '    FROM edge_topic_signal_weight\n'
         '    WHERE weight > 0.01\n'
         '    GROUP BY src_vid\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_record_topic_weight (\n'
         '      edge_id           VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      sensitivity_ord   INTEGER DEFAULT 0,\n'
         '      owner_did         VARCHAR,\n'
         '      actor_did         VARCHAR,\n'
         '      org_did           VARCHAR,\n'
         '      created_at        TIMESTAMP,\n'
         '      src_vid           VARCHAR,\n'
         '      dst_vid           VARCHAR,\n'
         '      weight            DOUBLE PRECISION DEFAULT 0.0,\n'
         '      source_collection VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_record_topic_src ON edge_record_topic_weight(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_record_topic_dst ON edge_record_topic_weight(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_latent_entity (\n'
         '      vertex_id              VARCHAR PRIMARY KEY,\n'
         '      _seq                   BIGINT,\n'
         '      sensitivity_ord        INTEGER DEFAULT 0,\n'
         '      owner_did              VARCHAR,\n'
         '      actor_did              VARCHAR,\n'
         '      org_did                VARCHAR,\n'
         '      created_at             TIMESTAMP,\n'
         '      entity_kind            VARCHAR,\n'
         '      canonical_label        VARCHAR,\n'
         '      existence_probability  DOUBLE PRECISION DEFAULT 0.0,\n'
         '      k_evidence_count       INTEGER DEFAULT 0,\n'
         '      viewpoint_consensus    INTEGER DEFAULT 0,\n'
         '      fission_eligible       BOOLEAN DEFAULT false,\n'
         "      status                 VARCHAR DEFAULT 'active',\n"
         '      primary_topic_vid      VARCHAR,\n'
         '      individual_did         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_latent_entity_kind ON vertex_latent_entity(entity_kind)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_latent_entity_fission ON '
         'vertex_latent_entity(fission_eligible, existence_probability)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_entity_evidence (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      sensitivity_ord INTEGER DEFAULT 0,\n'
         '      owner_did       VARCHAR,\n'
         '      actor_did       VARCHAR,\n'
         '      org_did         VARCHAR,\n'
         '      created_at      TIMESTAMP,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      evidence_weight DOUBLE PRECISION DEFAULT 0.0\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_entity_evidence_dst ON edge_entity_evidence(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_topic_entity_binding (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      sensitivity_ord INTEGER DEFAULT 0,\n'
         '      owner_did       VARCHAR,\n'
         '      actor_did       VARCHAR,\n'
         '      org_did         VARCHAR,\n'
         '      created_at      TIMESTAMP,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      binding_weight  DOUBLE PRECISION DEFAULT 0.0\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_topic_entity_src ON edge_topic_entity_binding(src_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_entity_cohort_link (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      sensitivity_ord INTEGER DEFAULT 0,\n'
         '      owner_did       VARCHAR,\n'
         '      actor_did       VARCHAR,\n'
         '      org_did         VARCHAR,\n'
         '      created_at      TIMESTAMP,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      link_confidence DOUBLE PRECISION DEFAULT 0.0\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_entity_cohort_src ON edge_entity_cohort_link(src_vid)',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lda_topic_top_signals', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_lda_model_latest', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_entity_cohort_link', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_topic_entity_binding', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_entity_evidence', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_latent_entity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_record_topic_weight', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_topic_signal_weight', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lda_topic', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lda_model', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lda_signal', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_lda_viewpoint', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
