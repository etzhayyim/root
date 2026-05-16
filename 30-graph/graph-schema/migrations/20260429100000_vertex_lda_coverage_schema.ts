import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0096 LDA latent entity inference schema.
// Tables consumed by inferLdaSignals / inferLdaTopics / inferLdaEntities /
// inferLdaIncremental / inferFission BPMNs (coverage-ui-c0v3r4g3 XRPC
// handlers also query vertex_lda_viewpoint, vertex_latent_entity,
// edge_entity_evidence directly).

export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. LDA viewpoints (named multi-viewpoint dimensions)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lda_viewpoint (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      sensitivity_ord   INTEGER DEFAULT 0,
      owner_did         VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR,
      created_at        TIMESTAMP,
      viewpoint_kind    VARCHAR,
      description       VARCHAR,
      signal_vocab_size INTEGER DEFAULT 0,
      active            BOOLEAN DEFAULT true
    )
  `.execute(db);

  // 2. LDA signal vocabulary (per viewpoint, per token)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lda_signal (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      sensitivity_ord    INTEGER DEFAULT 0,
      owner_did          VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR,
      created_at         TIMESTAMP,
      viewpoint_vid      VARCHAR,
      signal_token       VARCHAR,
      signal_kind        VARCHAR,
      source_collection  VARCHAR,
      extraction_expr    VARCHAR,
      doc_frequency      INTEGER DEFAULT 0,
      idf_score          DOUBLE PRECISION DEFAULT 0.0
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_lda_signal_viewpoint ON vertex_lda_signal(viewpoint_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lda_signal_token ON vertex_lda_signal(signal_token)`.execute(db);

  // 3. LDA models (converged topic models, one per full Gibbs run)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lda_model (
      vertex_id      VARCHAR PRIMARY KEY,
      _seq           BIGINT,
      sensitivity_ord INTEGER DEFAULT 0,
      owner_did      VARCHAR,
      actor_did      VARCHAR,
      org_did        VARCHAR,
      created_at     TIMESTAMP,
      model_slug     VARCHAR,
      k_topics       INTEGER DEFAULT 8,
      alpha          DOUBLE PRECISION DEFAULT 0.1,
      beta           DOUBLE PRECISION DEFAULT 0.01,
      trained_at     TIMESTAMP,
      signal_count   INTEGER DEFAULT 0,
      record_count   INTEGER DEFAULT 0,
      perplexity     DOUBLE PRECISION DEFAULT 0.0,
      status         VARCHAR DEFAULT 'training'
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_lda_model_status ON vertex_lda_model(status)`.execute(db);

  // 4. Latest converged model MV (used as warm-start watermark by inferLdaTopics + inferLdaIncremental)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lda_model_latest AS
    SELECT vertex_id AS model_vid,
           model_slug,
           k_topics,
           alpha,
           beta,
           trained_at,
           signal_count,
           record_count,
           perplexity,
           'lda_gibbs_full' AS training_corpus
    FROM vertex_lda_model
    WHERE status = 'converged'
    ORDER BY trained_at DESC
    LIMIT 1
  `.execute(db);

  // 5. LDA topics (one per topic index per model)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lda_topic (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      sensitivity_ord      INTEGER DEFAULT 0,
      owner_did            VARCHAR,
      actor_did            VARCHAR,
      org_did              VARCHAR,
      created_at           TIMESTAMP,
      model_vid            VARCHAR,
      topic_index          INTEGER,
      primary_viewpoint_vid VARCHAR,
      topic_label          VARCHAR,
      coherence_score      DOUBLE PRECISION DEFAULT 0.0,
      top_signal_count     INTEGER DEFAULT 0,
      entity_kind_hint     VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_lda_topic_model ON vertex_lda_topic(model_vid)`.execute(db);

  // 6. Topic↔signal weight edges (φ matrix)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_topic_signal_weight (
      edge_id         VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      sensitivity_ord INTEGER DEFAULT 0,
      owner_did       VARCHAR,
      actor_did       VARCHAR,
      org_did         VARCHAR,
      created_at      TIMESTAMP,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      model_vid       VARCHAR,
      signal_token    VARCHAR,
      weight          DOUBLE PRECISION DEFAULT 0.0
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_topic_signal_src ON edge_topic_signal_weight(src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_topic_signal_model ON edge_topic_signal_weight(model_vid)`.execute(db);

  // 7. Top signals per topic MV (used by inferLdaEntities consensus check)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lda_topic_top_signals AS
    SELECT
      src_vid AS topic_vid,
      COUNT(*) AS signal_count,
      SUM(weight) AS total_weight,
      MAX(weight) AS top_weight
    FROM edge_topic_signal_weight
    WHERE weight > 0.01
    GROUP BY src_vid
  `.execute(db);

  // 8. Record→topic weight edges (θ matrix, updated daily by inferLdaIncremental)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_record_topic_weight (
      edge_id           VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      sensitivity_ord   INTEGER DEFAULT 0,
      owner_did         VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR,
      created_at        TIMESTAMP,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      weight            DOUBLE PRECISION DEFAULT 0.0,
      source_collection VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_record_topic_src ON edge_record_topic_weight(src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_record_topic_dst ON edge_record_topic_weight(dst_vid)`.execute(db);

  // 9. Latent entities (emerged from multi-viewpoint LDA consensus)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_latent_entity (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT,
      sensitivity_ord        INTEGER DEFAULT 0,
      owner_did              VARCHAR,
      actor_did              VARCHAR,
      org_did                VARCHAR,
      created_at             TIMESTAMP,
      entity_kind            VARCHAR,
      canonical_label        VARCHAR,
      existence_probability  DOUBLE PRECISION DEFAULT 0.0,
      k_evidence_count       INTEGER DEFAULT 0,
      viewpoint_consensus    INTEGER DEFAULT 0,
      fission_eligible       BOOLEAN DEFAULT false,
      status                 VARCHAR DEFAULT 'active',
      primary_topic_vid      VARCHAR,
      individual_did         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_latent_entity_kind ON vertex_latent_entity(entity_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_latent_entity_fission ON vertex_latent_entity(fission_eligible, existence_probability)`.execute(db);

  // 10. Entity evidence edges (record → entity, weighted)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_entity_evidence (
      edge_id         VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      sensitivity_ord INTEGER DEFAULT 0,
      owner_did       VARCHAR,
      actor_did       VARCHAR,
      org_did         VARCHAR,
      created_at      TIMESTAMP,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      evidence_weight DOUBLE PRECISION DEFAULT 0.0
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_entity_evidence_dst ON edge_entity_evidence(dst_vid)`.execute(db);

  // 11. Topic → entity binding edges
  await sql`
    CREATE TABLE IF NOT EXISTS edge_topic_entity_binding (
      edge_id         VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      sensitivity_ord INTEGER DEFAULT 0,
      owner_did       VARCHAR,
      actor_did       VARCHAR,
      org_did         VARCHAR,
      created_at      TIMESTAMP,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      binding_weight  DOUBLE PRECISION DEFAULT 0.0
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_topic_entity_src ON edge_topic_entity_binding(src_vid)`.execute(db);

  // 12. Entity → ADR-0026 cohort link edges (fission gate input)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_entity_cohort_link (
      edge_id         VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      sensitivity_ord INTEGER DEFAULT 0,
      owner_did       VARCHAR,
      actor_did       VARCHAR,
      org_did         VARCHAR,
      created_at      TIMESTAMP,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      link_confidence DOUBLE PRECISION DEFAULT 0.0
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_entity_cohort_src ON edge_entity_cohort_link(src_vid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_lda_topic_top_signals",
    "mv_lda_model_latest",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const tbl of [
    "edge_entity_cohort_link",
    "edge_topic_entity_binding",
    "edge_entity_evidence",
    "vertex_latent_entity",
    "edge_record_topic_weight",
    "edge_topic_signal_weight",
    "vertex_lda_topic",
    "vertex_lda_model",
    "vertex_lda_signal",
    "vertex_lda_viewpoint",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(tbl)}`.execute(db);
  }
}
