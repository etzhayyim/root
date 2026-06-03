import { Kysely, sql } from "kysely";

/**
 * OWL QL/EL/DL/RL + SHACL reasoning schema
 *
 * Layer mapping (ADR-0044):
 *   Layer 1  vertex_owl_class / _property / edge_owl_* + mv_owl_rl_* + SQL UDF  (RL + SHACL core)
 *   Layer 2  vertex_owl_inferred / vertex_owl_benchmark                          (EL++ + DL batch, pyzeebe)
 *   Layer 3  vertex_ql_rewrite + view v_rdf_triple                               (QL gateway)
 *
 * A-Box rule: v_rdf_triple is a VIEW over existing vertex_/edge_ tables; no dual-write.
 * RW rules: no ON CONFLICT, no LIMIT $N, flush=False in pyzeebe.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // T-Box: OWL classes
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_owl_class (
      vertex_id    TEXT PRIMARY KEY,
      class_iri    TEXT NOT NULL,
      label        TEXT,
      profile      TEXT NOT NULL DEFAULT 'ALL',
      -- ALL | RL | EL | QL | DL
      source_nsid  TEXT,
      created_at   TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // T-Box: OWL properties
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_owl_property (
      vertex_id          TEXT PRIMARY KEY,
      property_iri       TEXT NOT NULL,
      property_type      TEXT NOT NULL,
      -- ObjectProperty | DataProperty | AnnotationProperty
      is_functional      BOOLEAN DEFAULT FALSE,
      is_transitive      BOOLEAN DEFAULT FALSE,
      is_symmetric       BOOLEAN DEFAULT FALSE,
      is_inverse_functional BOOLEAN DEFAULT FALSE,
      profile            TEXT NOT NULL DEFAULT 'ALL',
      source_nsid        TEXT,
      created_at         TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // T-Box edges
  await sql`
    CREATE TABLE IF NOT EXISTS edge_owl_subclass (
      from_vertex_id TEXT NOT NULL,   -- subclass IRI
      to_vertex_id   TEXT NOT NULL,   -- superclass IRI
      axiom_type     TEXT NOT NULL,   -- SubClassOf | EquivalentClasses | DisjointClasses
      profile        TEXT NOT NULL DEFAULT 'ALL',
      created_at     TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_owl_property_domain (
      from_vertex_id TEXT NOT NULL,   -- property
      to_vertex_id   TEXT NOT NULL,   -- domain class
      profile        TEXT NOT NULL DEFAULT 'ALL',
      created_at     TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_owl_property_range (
      from_vertex_id TEXT NOT NULL,   -- property
      to_vertex_id   TEXT NOT NULL,   -- range class or datatype
      profile        TEXT NOT NULL DEFAULT 'ALL',
      created_at     TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // OWL RL prp-spo2: ObjectPropertyChain, (p1 o p2) implies p3
  await sql`
    CREATE TABLE IF NOT EXISTS edge_owl_property_chain (
      chain_vertex_id TEXT NOT NULL,  -- result property vertex_id
      position        INT  NOT NULL,  -- 1-based position in chain
      member_iri      TEXT NOT NULL,  -- property IRI at this position
      created_at      TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_owl_inferred (
      vertex_id    TEXT PRIMARY KEY,
      -- SHA256(subject||predicate||object||profile)
      subject      TEXT NOT NULL,
      predicate    TEXT NOT NULL,
      object       TEXT NOT NULL,
      profile      TEXT NOT NULL,
      -- RL | EL | DL
      confidence   REAL    DEFAULT 1.0,
      derived_at   TIMESTAMPTZ DEFAULT NOW(),
      ontology_ver TEXT
    )
  `.execute(db);

  // A-Box: virtual RDF triple view (no physical rows)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shacl_violation`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_el_dl_diff`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_range`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_domain`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_subproperty`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d3`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d2`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d1`.execute(db);
  await sql`DROP VIEW IF EXISTS v_rdf_triple`.execute(db);
  await sql`
    CREATE VIEW v_rdf_triple AS
    -- actors typed as etzhayyim:Actor
    SELECT actor_did           AS subject,
           'rdf:type'          AS predicate,
           'etzhayyim:Actor'        AS object
    FROM   vertex_bpmn_process_def
    UNION ALL
    -- follows graph to etzhayyim:follows
    SELECT src_vid             AS subject,
           'etzhayyim:follows'      AS predicate,
           dst_vid             AS object
    FROM   edge_follows
    UNION ALL
    -- DID to handle (via vertex_profile which has both did and handle)
    SELECT did                 AS subject,
           'etzhayyim:handle'       AS predicate,
           handle              AS object
    FROM   vertex_profile
    WHERE  handle IS NOT NULL
    UNION ALL
    -- inferred facts from Layer-2 batch reasoner
    SELECT subject, predicate, object
    FROM   vertex_owl_inferred
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_owl_derivation (
      from_vertex_id TEXT NOT NULL,   -- vertex_owl_inferred
      to_vertex_id   TEXT NOT NULL,   -- vertex_owl_class or vertex_owl_property (source axiom)
      rule_name      TEXT,
      -- RL: cls-svf1/prp-spo1 etc. EL: saturation step. DL: tableau rule
      created_at     TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // EL++ vs DL benchmark (comparison)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_owl_benchmark (
      vertex_id             TEXT PRIMARY KEY,
      -- '{ontology_ver}:{profile}'
      ontology_ver          TEXT NOT NULL,
      profile               TEXT NOT NULL,
      -- EL | DL
      class_count           INT,
      inferred_subsumptions INT,
      duration_ms           INT,
      consistent            BOOLEAN,
      peak_ram_mb           INT,
      hermit_version        TEXT,
      -- DL only
      el_completeness_pct   REAL,
      -- EL: what % of DL inferences EL++ also found
      started_at            TIMESTAMPTZ,
      completed_at          TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // SHACL shapes (generated from Lexicon JSON, audit-only)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shacl_shape (
      vertex_id       TEXT PRIMARY KEY,
      shape_iri       TEXT NOT NULL,
      target_class    TEXT NOT NULL,
      constraint_type TEXT NOT NULL,
      -- minCount|maxCount|datatype|class|pattern|nodeKind|sparql
      constraint_json JSONB NOT NULL,
      severity        TEXT DEFAULT 'Violation',
      source_nsid     TEXT,
      enabled         BOOLEAN DEFAULT TRUE,
      created_at      TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shacl_result (
      vertex_id       TEXT PRIMARY KEY,
      -- '{node_iri}:{shape_id}:{validated_at_ms}'
      node_iri        TEXT NOT NULL,
      shape_id        TEXT NOT NULL,
      violation_type  TEXT NOT NULL,
      message         TEXT,
      severity        TEXT DEFAULT 'Violation',
      validated_at    TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_shacl_violation (
      from_vertex_id  TEXT NOT NULL,  -- node IRI (references vertex_* by DID/IRI)
      to_vertex_id    TEXT NOT NULL,  -- vertex_shacl_shape
      constraint_type TEXT NOT NULL,
      created_at      TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // QL rewrite cache
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ql_rewrite (
      vertex_id    TEXT PRIMARY KEY,
      -- SHA256(sparql_in)
      sparql_in    TEXT NOT NULL,
      sql_out      TEXT NOT NULL,
      ontology_ver TEXT NOT NULL,
      hit_count    INT  DEFAULT 0,
      cached_at    TIMESTAMPTZ DEFAULT NOW()
    )
  `.execute(db);

  // Streaming MVs (Layer 1: OWL RL)
  // No background_ddl: source tables start empty so backfill is instant,
  // and dependent MVs (d2 → d1, d3 → d2) need the prior MV to be catalog-visible.

  // RL SubClassOf depth-1: x rdf:type A, SubClassOf(A,B) implies x rdf:type B
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d1`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_type_d1 AS
    SELECT t.subject,
           'rdf:type'        AS predicate,
           e.to_vertex_id    AS superclass
    FROM   v_rdf_triple      t
    JOIN   edge_owl_subclass e
      ON   e.from_vertex_id = t.object
      AND  t.predicate = 'rdf:type'
      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')
  `.execute(db);

  // RL SubClassOf depth-2
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d2`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_type_d2 AS
    SELECT d1.subject,
           'rdf:type'        AS predicate,
           e.to_vertex_id    AS superclass
    FROM   mv_owl_rl_type_d1 d1
    JOIN   edge_owl_subclass  e
      ON   e.from_vertex_id = d1.superclass
      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')
  `.execute(db);

  // RL SubClassOf depth-3 (covers most practical ontology depths)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_type_d3`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_type_d3 AS
    SELECT d2.subject,
           'rdf:type'        AS predicate,
           e.to_vertex_id    AS superclass
    FROM   mv_owl_rl_type_d2 d2
    JOIN   edge_owl_subclass  e
      ON   e.from_vertex_id = d2.superclass
      AND  e.axiom_type IN ('SubClassOf','EquivalentClasses')
  `.execute(db);

  // RL prp-spo1: SubObjectPropertyOf, s p1 o and SubPropertyOf(p1,p2) implies s p2 o
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_subproperty`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_subproperty AS
    SELECT t.subject,
           e.to_vertex_id AS predicate,
           t.object
    FROM   v_rdf_triple t
    JOIN   edge_owl_subclass e
      ON   e.from_vertex_id = t.predicate
      AND  e.axiom_type = 'SubObjectPropertyOf'
  `.execute(db);

  // RL scm-dom1: domain inference, s p o and domain(p, C) implies s rdf:type C
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_domain`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_domain AS
    SELECT t.subject,
           'rdf:type'        AS predicate,
           d.to_vertex_id    AS inferred_class
    FROM   v_rdf_triple t
    JOIN   edge_owl_property_domain d ON d.from_vertex_id = t.predicate
  `.execute(db);

  // RL scm-rng1: range inference, s p o and range(p, C) implies o rdf:type C
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_rl_range`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_rl_range AS
    SELECT t.object          AS subject,
           'rdf:type'        AS predicate,
           r.to_vertex_id    AS inferred_class
    FROM   v_rdf_triple t
    JOIN   edge_owl_property_range r ON r.from_vertex_id = t.predicate
  `.execute(db);

  // EL++ vs DL diff MV
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_owl_el_dl_diff`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_owl_el_dl_diff AS
    SELECT el.subject,
           el.predicate,
           el.object,
           CASE
             WHEN dl.vertex_id IS NOT NULL THEN 'agreed'
             ELSE                               'el_only'
           END AS status
    FROM   vertex_owl_inferred el
    LEFT JOIN vertex_owl_inferred dl
      ON   dl.subject   = el.subject
      AND  dl.predicate = el.predicate
      AND  dl.object    = el.object
      AND  dl.profile   = 'DL'
    WHERE  el.profile = 'EL'
    UNION ALL
    SELECT dl.subject,
           dl.predicate,
           dl.object,
           'dl_only' AS status
    FROM   vertex_owl_inferred dl
    LEFT JOIN vertex_owl_inferred el
      ON   el.subject   = dl.subject
      AND  el.predicate = dl.predicate
      AND  el.object    = dl.object
      AND  el.profile   = 'EL'
    WHERE  dl.profile = 'DL'
      AND  el.vertex_id IS NULL
  `.execute(db);

  // SHACL core violation MV (minCount/class evaluated by SQL UDFs)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shacl_violation`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_shacl_violation AS
    SELECT t.subject                         AS node_iri,
           s.vertex_id                       AS shape_id,
           s.severity,
           s.constraint_type,
           s.constraint_json
    FROM   v_rdf_triple    t
    JOIN   vertex_shacl_shape s
      ON   s.target_class = t.object
      AND  t.predicate    = 'rdf:type'
      AND  s.enabled      = TRUE
    WHERE  s.constraint_type IN ('minCount','maxCount','class','nodeKind')
  `.execute(db);

  // SQL UDFs (Layer 1)

  // RL type check (d1 + d2 + d3 union)
  await sql`
    CREATE OR REPLACE FUNCTION owl_rl_is_type(subject TEXT, class_iri TEXT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT EXISTS (
        SELECT 1 FROM v_rdf_triple
        WHERE subject = $1 AND predicate = 'rdf:type' AND object = $2
        UNION ALL
        SELECT 1 FROM mv_owl_rl_type_d1
        WHERE subject = $1 AND superclass = $2
        UNION ALL
        SELECT 1 FROM mv_owl_rl_type_d2
        WHERE subject = $1 AND superclass = $2
        UNION ALL
        SELECT 1 FROM mv_owl_rl_type_d3
        WHERE subject = $1 AND superclass = $2
      )
    $$
  `.execute(db);

  // RL FunctionalProperty check
  await sql`
    CREATE OR REPLACE FUNCTION owl_rl_check_functional(subject TEXT, property TEXT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT COUNT(DISTINCT object) <= 1
      FROM v_rdf_triple
      WHERE subject = $1 AND predicate = $2
    $$
  `.execute(db);

  // SHACL sh:minCount
  await sql`
    CREATE OR REPLACE FUNCTION shacl_min_count(node TEXT, property TEXT, min_count INT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT COUNT(*) >= $3
      FROM v_rdf_triple
      WHERE subject = $1 AND predicate = $2
    $$
  `.execute(db);

  // SHACL sh:maxCount
  await sql`
    CREATE OR REPLACE FUNCTION shacl_max_count(node TEXT, property TEXT, max_count INT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT COUNT(*) <= $3
      FROM v_rdf_triple
      WHERE subject = $1 AND predicate = $2
    $$
  `.execute(db);

  // SHACL sh:pattern
  await sql`
    CREATE OR REPLACE FUNCTION shacl_pattern(value TEXT, pattern TEXT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT $1 ~ $2
    $$
  `.execute(db);

  // SHACL sh:class (delegates to RL MV)
  await sql`
    CREATE OR REPLACE FUNCTION shacl_class(node TEXT, class_iri TEXT)
    RETURNS BOOLEAN LANGUAGE SQL AS $$
      SELECT owl_rl_is_type($1, $2)
    $$
  `.execute(db);

  // ─── Indexes ─────────────────────────────────────────────────────────────────
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_subclass_from
    ON edge_owl_subclass(from_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_subclass_to
    ON edge_owl_subclass(to_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_property_domain_from
    ON edge_owl_property_domain(from_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_property_range_from
    ON edge_owl_property_range(from_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_inferred_subject
    ON vertex_owl_inferred(subject)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_inferred_profile
    ON vertex_owl_inferred(profile)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_inferred_subject_profile
    ON vertex_owl_inferred(subject, profile)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_owl_benchmark_ver_profile
    ON vertex_owl_benchmark(ontology_ver, profile)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shacl_shape_target
    ON vertex_shacl_shape(target_class)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shacl_result_node
    ON vertex_shacl_result(node_iri)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ql_rewrite_ver
    ON vertex_ql_rewrite(ontology_ver)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const fn of [
    "owl_rl_is_type","owl_rl_check_functional",
    "shacl_min_count","shacl_max_count","shacl_pattern","shacl_class",
  ]) {
    await sql`DROP FUNCTION IF EXISTS ${sql.raw(fn)}`.execute(db);
  }
  for (const mv of [
    "mv_shacl_violation","mv_owl_el_dl_diff",
    "mv_owl_rl_range","mv_owl_rl_domain","mv_owl_rl_subproperty",
    "mv_owl_rl_type_d3","mv_owl_rl_type_d2","mv_owl_rl_type_d1",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  await sql`DROP VIEW IF EXISTS v_rdf_triple`.execute(db);
  for (const t of [
    "vertex_ql_rewrite","edge_shacl_violation",
    "vertex_shacl_result","vertex_shacl_shape",
    "vertex_owl_benchmark","edge_owl_derivation","vertex_owl_inferred",
    "edge_owl_property_chain","edge_owl_property_range",
    "edge_owl_property_domain","edge_owl_subclass",
    "vertex_owl_property","vertex_owl_class",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
