"""Captured from Kysely migration 20260501140000_vertex_owl_reasoner_schema."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501140000_vertex_owl_reasoner_schema"
down_revision = 'r_20260501140000_vertex_market_listing_settlement'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_owl_class (\n'
         '      vertex_id    TEXT PRIMARY KEY,\n'
         '      class_iri    TEXT NOT NULL,\n'
         '      label        TEXT,\n'
         "      profile      TEXT NOT NULL DEFAULT 'ALL',\n"
         '      -- ALL | RL | EL | QL | DL\n'
         '      source_nsid  TEXT,\n'
         '      created_at   TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_owl_property (\n'
         '      vertex_id          TEXT PRIMARY KEY,\n'
         '      property_iri       TEXT NOT NULL,\n'
         '      property_type      TEXT NOT NULL,\n'
         '      -- ObjectProperty | DataProperty | AnnotationProperty\n'
         '      is_functional      BOOLEAN DEFAULT FALSE,\n'
         '      is_transitive      BOOLEAN DEFAULT FALSE,\n'
         '      is_symmetric       BOOLEAN DEFAULT FALSE,\n'
         '      is_inverse_functional BOOLEAN DEFAULT FALSE,\n'
         "      profile            TEXT NOT NULL DEFAULT 'ALL',\n"
         '      source_nsid        TEXT,\n'
         '      created_at         TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_owl_subclass (\n'
         '      from_vertex_id TEXT NOT NULL,   -- subclass IRI\n'
         '      to_vertex_id   TEXT NOT NULL,   -- superclass IRI\n'
         '      axiom_type     TEXT NOT NULL,   -- SubClassOf | EquivalentClasses | '
         'DisjointClasses\n'
         "      profile        TEXT NOT NULL DEFAULT 'ALL',\n"
         '      created_at     TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_owl_property_domain (\n'
         '      from_vertex_id TEXT NOT NULL,   -- property\n'
         '      to_vertex_id   TEXT NOT NULL,   -- domain class\n'
         "      profile        TEXT NOT NULL DEFAULT 'ALL',\n"
         '      created_at     TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_owl_property_range (\n'
         '      from_vertex_id TEXT NOT NULL,   -- property\n'
         '      to_vertex_id   TEXT NOT NULL,   -- range class or datatype\n'
         "      profile        TEXT NOT NULL DEFAULT 'ALL',\n"
         '      created_at     TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_owl_property_chain (\n'
         '      chain_vertex_id TEXT NOT NULL,  -- result property vertex_id\n'
         '      position        INT  NOT NULL,  -- 1-based position in chain\n'
         '      member_iri      TEXT NOT NULL,  -- property IRI at this position\n'
         '      created_at      TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_owl_inferred (\n'
         '      vertex_id    TEXT PRIMARY KEY,\n'
         '      -- SHA256(subject||predicate||object||profile)\n'
         '      subject      TEXT NOT NULL,\n'
         '      predicate    TEXT NOT NULL,\n'
         '      object       TEXT NOT NULL,\n'
         '      profile      TEXT NOT NULL,\n'
         '      -- RL | EL | DL\n'
         '      confidence   REAL    DEFAULT 1.0,\n'
         '      derived_at   TIMESTAMPTZ DEFAULT NOW(),\n'
         '      ontology_ver TEXT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shacl_violation', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_el_dl_diff', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_range', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_domain', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_subproperty', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d3', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d2', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d1', 'parameters': []},
 {'sql': 'DROP VIEW IF EXISTS v_rdf_triple', 'parameters': []},
 {'sql': '\n'
         '    CREATE VIEW v_rdf_triple AS\n'
         '    -- actors typed as etzhayyim:Actor\n'
         '    SELECT actor_did           AS subject,\n'
         "           'rdf:type'          AS predicate,\n"
         "           'etzhayyim:Actor'        AS object\n"
         '    FROM   vertex_bpmn_process_def\n'
         '    UNION ALL\n'
         '    -- follows graph to etzhayyim:follows\n'
         '    SELECT src_vid             AS subject,\n'
         "           'etzhayyim:follows'      AS predicate,\n"
         '           dst_vid             AS object\n'
         '    FROM   edge_follows\n'
         '    UNION ALL\n'
         '    -- DID to handle (via vertex_profile which has both did and handle)\n'
         '    SELECT did                 AS subject,\n'
         "           'etzhayyim:handle'       AS predicate,\n"
         '           handle              AS object\n'
         '    FROM   vertex_profile\n'
         '    WHERE  handle IS NOT NULL\n'
         '    UNION ALL\n'
         '    -- inferred facts from Layer-2 batch reasoner\n'
         '    SELECT subject, predicate, object\n'
         '    FROM   vertex_owl_inferred\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_owl_derivation (\n'
         '      from_vertex_id TEXT NOT NULL,   -- vertex_owl_inferred\n'
         '      to_vertex_id   TEXT NOT NULL,   -- vertex_owl_class or vertex_owl_property (source '
         'axiom)\n'
         '      rule_name      TEXT,\n'
         '      -- RL: cls-svf1/prp-spo1 etc. EL: saturation step. DL: tableau rule\n'
         '      created_at     TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_owl_benchmark (\n'
         '      vertex_id             TEXT PRIMARY KEY,\n'
         "      -- '{ontology_ver}:{profile}'\n"
         '      ontology_ver          TEXT NOT NULL,\n'
         '      profile               TEXT NOT NULL,\n'
         '      -- EL | DL\n'
         '      class_count           INT,\n'
         '      inferred_subsumptions INT,\n'
         '      duration_ms           INT,\n'
         '      consistent            BOOLEAN,\n'
         '      peak_ram_mb           INT,\n'
         '      hermit_version        TEXT,\n'
         '      -- DL only\n'
         '      el_completeness_pct   REAL,\n'
         '      -- EL: what % of DL inferences EL++ also found\n'
         '      started_at            TIMESTAMPTZ,\n'
         '      completed_at          TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shacl_shape (\n'
         '      vertex_id       TEXT PRIMARY KEY,\n'
         '      shape_iri       TEXT NOT NULL,\n'
         '      target_class    TEXT NOT NULL,\n'
         '      constraint_type TEXT NOT NULL,\n'
         '      -- minCount|maxCount|datatype|class|pattern|nodeKind|sparql\n'
         '      constraint_json JSONB NOT NULL,\n'
         "      severity        TEXT DEFAULT 'Violation',\n"
         '      source_nsid     TEXT,\n'
         '      enabled         BOOLEAN DEFAULT TRUE,\n'
         '      created_at      TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shacl_result (\n'
         '      vertex_id       TEXT PRIMARY KEY,\n'
         "      -- '{node_iri}:{shape_id}:{validated_at_ms}'\n"
         '      node_iri        TEXT NOT NULL,\n'
         '      shape_id        TEXT NOT NULL,\n'
         '      violation_type  TEXT NOT NULL,\n'
         '      message         TEXT,\n'
         "      severity        TEXT DEFAULT 'Violation',\n"
         '      validated_at    TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_shacl_violation (\n'
         '      from_vertex_id  TEXT NOT NULL,  -- node IRI (references vertex_* by DID/IRI)\n'
         '      to_vertex_id    TEXT NOT NULL,  -- vertex_shacl_shape\n'
         '      constraint_type TEXT NOT NULL,\n'
         '      created_at      TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ql_rewrite (\n'
         '      vertex_id    TEXT PRIMARY KEY,\n'
         '      -- SHA256(sparql_in)\n'
         '      sparql_in    TEXT NOT NULL,\n'
         '      sql_out      TEXT NOT NULL,\n'
         '      ontology_ver TEXT NOT NULL,\n'
         '      hit_count    INT  DEFAULT 0,\n'
         '      cached_at    TIMESTAMPTZ DEFAULT NOW()\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d1', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_type_d1 AS\n'
         '    SELECT t.subject,\n'
         "           'rdf:type'        AS predicate,\n"
         '           e.to_vertex_id    AS superclass\n'
         '    FROM   v_rdf_triple      t\n'
         '    JOIN   edge_owl_subclass e\n'
         '      ON   e.from_vertex_id = t.object\n'
         "      AND  t.predicate = 'rdf:type'\n"
         "      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')\n"
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d2', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_type_d2 AS\n'
         '    SELECT d1.subject,\n'
         "           'rdf:type'        AS predicate,\n"
         '           e.to_vertex_id    AS superclass\n'
         '    FROM   mv_owl_rl_type_d1 d1\n'
         '    JOIN   edge_owl_subclass  e\n'
         '      ON   e.from_vertex_id = d1.superclass\n'
         "      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')\n"
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d3', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_type_d3 AS\n'
         '    SELECT d2.subject,\n'
         "           'rdf:type'        AS predicate,\n"
         '           e.to_vertex_id    AS superclass\n'
         '    FROM   mv_owl_rl_type_d2 d2\n'
         '    JOIN   edge_owl_subclass  e\n'
         '      ON   e.from_vertex_id = d2.superclass\n'
         "      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')\n"
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_subproperty', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_subproperty AS\n'
         '    SELECT t.subject,\n'
         '           e.to_vertex_id AS predicate,\n'
         '           t.object\n'
         '    FROM   v_rdf_triple t\n'
         '    JOIN   edge_owl_subclass e\n'
         '      ON   e.from_vertex_id = t.predicate\n'
         "      AND  e.axiom_type = 'SubObjectPropertyOf'\n"
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_domain', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_domain AS\n'
         '    SELECT t.subject,\n'
         "           'rdf:type'        AS predicate,\n"
         '           d.to_vertex_id    AS inferred_class\n'
         '    FROM   v_rdf_triple t\n'
         '    JOIN   edge_owl_property_domain d ON d.from_vertex_id = t.predicate\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_range', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_rl_range AS\n'
         '    SELECT t.object          AS subject,\n'
         "           'rdf:type'        AS predicate,\n"
         '           r.to_vertex_id    AS inferred_class\n'
         '    FROM   v_rdf_triple t\n'
         '    JOIN   edge_owl_property_range r ON r.from_vertex_id = t.predicate\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_el_dl_diff', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_owl_el_dl_diff AS\n'
         '    SELECT el.subject,\n'
         '           el.predicate,\n'
         '           el.object,\n'
         '           CASE\n'
         "             WHEN dl.vertex_id IS NOT NULL THEN 'agreed'\n"
         "             ELSE                               'el_only'\n"
         '           END AS status\n'
         '    FROM   vertex_owl_inferred el\n'
         '    LEFT JOIN vertex_owl_inferred dl\n'
         '      ON   dl.subject   = el.subject\n'
         '      AND  dl.predicate = el.predicate\n'
         '      AND  dl.object    = el.object\n'
         "      AND  dl.profile   = 'DL'\n"
         "    WHERE  el.profile = 'EL'\n"
         '    UNION ALL\n'
         '    SELECT dl.subject,\n'
         '           dl.predicate,\n'
         '           dl.object,\n'
         "           'dl_only' AS status\n"
         '    FROM   vertex_owl_inferred dl\n'
         '    LEFT JOIN vertex_owl_inferred el\n'
         '      ON   el.subject   = dl.subject\n'
         '      AND  el.predicate = dl.predicate\n'
         '      AND  el.object    = dl.object\n'
         "      AND  el.profile   = 'EL'\n"
         "    WHERE  dl.profile = 'DL'\n"
         '      AND  el.vertex_id IS NULL\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shacl_violation', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_shacl_violation AS\n'
         '    SELECT t.subject                         AS node_iri,\n'
         '           s.vertex_id                       AS shape_id,\n'
         '           s.severity,\n'
         '           s.constraint_type,\n'
         '           s.constraint_json\n'
         '    FROM   v_rdf_triple    t\n'
         '    JOIN   vertex_shacl_shape s\n'
         '      ON   s.target_class = t.object\n'
         "      AND  t.predicate    = 'rdf:type'\n"
         '      AND  s.enabled      = TRUE\n'
         "    WHERE  s.constraint_type IN ('minCount','maxCount','class','nodeKind')\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION owl_rl_is_type(subject TEXT, class_iri TEXT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT EXISTS (\n'
         '        SELECT 1 FROM v_rdf_triple\n'
         "        WHERE subject = $1 AND predicate = 'rdf:type' AND object = $2\n"
         '        UNION ALL\n'
         '        SELECT 1 FROM mv_owl_rl_type_d1\n'
         '        WHERE subject = $1 AND superclass = $2\n'
         '        UNION ALL\n'
         '        SELECT 1 FROM mv_owl_rl_type_d2\n'
         '        WHERE subject = $1 AND superclass = $2\n'
         '        UNION ALL\n'
         '        SELECT 1 FROM mv_owl_rl_type_d3\n'
         '        WHERE subject = $1 AND superclass = $2\n'
         '      )\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION owl_rl_check_functional(subject TEXT, property TEXT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT COUNT(DISTINCT object) <= 1\n'
         '      FROM v_rdf_triple\n'
         '      WHERE subject = $1 AND predicate = $2\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION shacl_min_count(node TEXT, property TEXT, min_count INT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT COUNT(*) >= $3\n'
         '      FROM v_rdf_triple\n'
         '      WHERE subject = $1 AND predicate = $2\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION shacl_max_count(node TEXT, property TEXT, max_count INT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT COUNT(*) <= $3\n'
         '      FROM v_rdf_triple\n'
         '      WHERE subject = $1 AND predicate = $2\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION shacl_pattern(value TEXT, pattern TEXT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT $1 ~ $2\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE OR REPLACE FUNCTION shacl_class(node TEXT, class_iri TEXT)\n'
         '    RETURNS BOOLEAN LANGUAGE SQL AS $$\n'
         '      SELECT owl_rl_is_type($1, $2)\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_subclass_from\n'
         '    ON edge_owl_subclass(from_vertex_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_subclass_to\n    ON edge_owl_subclass(to_vertex_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_property_domain_from\n'
         '    ON edge_owl_property_domain(from_vertex_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_property_range_from\n'
         '    ON edge_owl_property_range(from_vertex_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_inferred_subject\n    ON vertex_owl_inferred(subject)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_inferred_profile\n    ON vertex_owl_inferred(profile)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_inferred_subject_profile\n'
         '    ON vertex_owl_inferred(subject, profile)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_owl_benchmark_ver_profile\n'
         '    ON vertex_owl_benchmark(ontology_ver, profile)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shacl_shape_target\n'
         '    ON vertex_shacl_shape(target_class)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shacl_result_node\n    ON vertex_shacl_result(node_iri)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_ql_rewrite_ver\n    ON vertex_ql_rewrite(ontology_ver)',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS owl_rl_is_type', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS owl_rl_check_functional', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS shacl_min_count', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS shacl_max_count', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS shacl_pattern', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS shacl_class', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shacl_violation', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_el_dl_diff', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_range', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_domain', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_subproperty', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d3', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d2', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d1', 'parameters': []},
 {'sql': 'DROP VIEW IF EXISTS v_rdf_triple', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_ql_rewrite', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_shacl_violation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shacl_result', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shacl_shape', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_owl_benchmark', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_owl_derivation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_owl_inferred', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_owl_property_chain', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_owl_property_range', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_owl_property_domain', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_owl_subclass', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_owl_property', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_owl_class', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
