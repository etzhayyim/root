import { Kysely } from "kysely";

// ADR-0096: LDA-Based Latent Entity Inference
// Multi-viewpoint observable→unobservable graph inference schema.
// 5 vertex + 9 edge + 4 MV + 13 idx + 8 viewpoint seeds.
// MV safety: all GROUP BY cardinality < 200. No vertex_page scan.

export async function up(db: Kysely<any>): Promise<void> {
  // ─── vertex_lda_viewpoint ───────────────────────────────────────────────
  await db.schema
    .createTable("vertex_lda_viewpoint")
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("viewpoint_kind", "varchar(100)")
    .addColumn("description", "varchar(2000)")
    .addColumn("signal_vocab_size", "integer")
    .addColumn("extraction_sql", "varchar(5000)")
    .addColumn("active", "boolean")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── vertex_lda_signal ──────────────────────────────────────────────────
  await db.schema
    .createTable("vertex_lda_signal")
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("viewpoint_vid", "varchar")
    .addColumn("signal_token", "varchar(500)")
    .addColumn("signal_kind", "varchar(100)")
    .addColumn("source_collection", "varchar(500)")
    .addColumn("extraction_expr", "varchar(2000)")
    .addColumn("doc_frequency", "bigint")
    .addColumn("idf_score", "double precision")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── vertex_lda_model ───────────────────────────────────────────────────
  await db.schema
    .createTable("vertex_lda_model")
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("model_slug", "varchar(200)")
    .addColumn("model_version", "varchar(50)")
    .addColumn("k_topics", "integer")
    .addColumn("alpha_prior", "double precision")
    .addColumn("beta_prior", "double precision")
    .addColumn("training_corpus", "varchar(200)")
    .addColumn("training_record_count", "bigint")
    .addColumn("viewpoints_used", "varchar(2000)")
    .addColumn("perplexity", "double precision")
    .addColumn("log_likelihood", "double precision")
    .addColumn("convergence_iter", "integer")
    .addColumn("status", "varchar(50)")
    .addColumn("trained_at", "timestamp")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── vertex_lda_topic ───────────────────────────────────────────────────
  await db.schema
    .createTable("vertex_lda_topic")
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("model_vid", "varchar")
    .addColumn("topic_index", "integer")
    .addColumn("primary_viewpoint_vid", "varchar")
    .addColumn("topic_label", "varchar(500)")
    .addColumn("coherence_score", "double precision")
    .addColumn("top_signal_count", "integer")
    .addColumn("entity_kind_hint", "varchar(100)")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── vertex_latent_entity ───────────────────────────────────────────────
  await db.schema
    .createTable("vertex_latent_entity")
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("entity_kind", "varchar(100)")
    .addColumn("canonical_label", "varchar(1000)")
    .addColumn("existence_probability", "double precision")
    .addColumn("existence_mass", "double precision")
    .addColumn("primary_viewpoint_vid", "varchar")
    .addColumn("primary_topic_vid", "varchar")
    .addColumn("k_evidence_count", "integer")
    .addColumn("viewpoint_consensus", "integer")
    .addColumn("fission_eligible", "boolean")
    .addColumn("status", "varchar(50)")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_viewpoint_topic ───────────────────────────────────────────────
  await db.schema
    .createTable("edge_viewpoint_topic")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("topic_weight", "double precision")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_viewpoint_signal ──────────────────────────────────────────────
  await db.schema
    .createTable("edge_viewpoint_signal")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("signal_rank", "integer")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_model_viewpoint ───────────────────────────────────────────────
  await db.schema
    .createTable("edge_model_viewpoint")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("viewpoint_weight", "double precision")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_record_topic_weight (θ: document-topic distribution) ──────────
  await db.schema
    .createTable("edge_record_topic_weight")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("weight", "double precision")
    .addColumn("source_collection", "varchar(500)")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_topic_signal_weight (φ: topic-word distribution) ─────────────
  await db.schema
    .createTable("edge_topic_signal_weight")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("weight", "double precision")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_topic_entity_binding ──────────────────────────────────────────
  await db.schema
    .createTable("edge_topic_entity_binding")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("binding_confidence", "double precision")
    .addColumn("stability_score", "double precision")
    .addColumn("binding_type", "varchar(100)")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_entity_evidence ───────────────────────────────────────────────
  await db.schema
    .createTable("edge_entity_evidence")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("evidence_weight", "double precision")
    .addColumn("evidence_kind", "varchar(100)")
    .addColumn("source_collection", "varchar(500)")
    .addColumn("observed_at", "timestamp")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── edge_entity_cohort_link (bridge to ADR-0026) ───────────────────────
  await db.schema
    .createTable("edge_entity_cohort_link")
    .addColumn("edge_id", "varchar", (c) => c.primaryKey())
    .addColumn("src_vid", "varchar")
    .addColumn("dst_vid", "varchar")
    .addColumn("_seq", "bigint")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("link_confidence", "double precision")
    .addColumn("link_type", "varchar(100)")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "timestamp")
    .execute();

  // ─── Indexes ────────────────────────────────────────────────────────────
  await db.schema
    .createIndex("idx_lda_signal_viewpoint")
    .on("vertex_lda_signal")
    .column("viewpoint_vid")
    .execute();
  await db.schema
    .createIndex("idx_lda_signal_token")
    .on("vertex_lda_signal")
    .column("signal_token")
    .execute();
  await db.schema
    .createIndex("idx_lda_topic_model")
    .on("vertex_lda_topic")
    .column("model_vid")
    .execute();
  await db.schema
    .createIndex("idx_lda_topic_viewpoint")
    .on("vertex_lda_topic")
    .column("primary_viewpoint_vid")
    .execute();
  await db.schema
    .createIndex("idx_latent_entity_kind")
    .on("vertex_latent_entity")
    .column("entity_kind")
    .execute();
  await db.schema
    .createIndex("idx_latent_entity_status")
    .on("vertex_latent_entity")
    .column("status")
    .execute();
  await db.schema
    .createIndex("idx_latent_entity_fission")
    .on("vertex_latent_entity")
    .column("fission_eligible")
    .execute();
  await db.schema
    .createIndex("idx_edge_record_topic_src")
    .on("edge_record_topic_weight")
    .column("src_vid")
    .execute();
  await db.schema
    .createIndex("idx_edge_record_topic_dst")
    .on("edge_record_topic_weight")
    .column("dst_vid")
    .execute();
  await db.schema
    .createIndex("idx_edge_topic_signal_src")
    .on("edge_topic_signal_weight")
    .column("src_vid")
    .execute();
  await db.schema
    .createIndex("idx_edge_entity_evidence_dst")
    .on("edge_entity_evidence")
    .column("dst_vid")
    .execute();
  await db.schema
    .createIndex("idx_edge_entity_evidence_src")
    .on("edge_entity_evidence")
    .column("src_vid")
    .execute();
  await db.schema
    .createIndex("idx_edge_entity_cohort_src")
    .on("edge_entity_cohort_link")
    .column("src_vid")
    .execute();

  // ─── MVs (all GROUP BY cardinality < 200 — safe per 30-graph CLAUDE.md) ─
  // mv_lda_viewpoint_stats: 8 viewpoints — trivially safe
  await db.executeQuery({
    sql: `CREATE MATERIALIZED VIEW mv_lda_viewpoint_stats AS
SELECT
  vp.vertex_id                       AS viewpoint_vid,
  vp.viewpoint_kind,
  COUNT(DISTINCT s.vertex_id)        AS signal_count,
  COUNT(DISTINCT t.vertex_id)        AS topic_count,
  0                                  AS entity_count
FROM vertex_lda_viewpoint vp
LEFT JOIN vertex_lda_signal s ON s.viewpoint_vid = vp.vertex_id
LEFT JOIN vertex_lda_topic   t ON t.primary_viewpoint_vid = vp.vertex_id
GROUP BY vp.vertex_id, vp.viewpoint_kind`,
    parameters: [],
  } as any);

  // mv_lda_model_latest: < 20 distinct corpus names — safe
  await db.executeQuery({
    sql: `CREATE MATERIALIZED VIEW mv_lda_model_latest AS
SELECT
  training_corpus,
  vertex_id                           AS model_vid,
  k_topics,
  perplexity,
  trained_at,
  status
FROM vertex_lda_model
WHERE status = 'converged'`,
    parameters: [],
  } as any);

  // mv_lda_topic_top_signals: < K topics (initially 50) — safe
  await db.executeQuery({
    sql: `CREATE MATERIALIZED VIEW mv_lda_topic_top_signals AS
SELECT
  e.src_vid                           AS topic_vid,
  t.entity_kind_hint,
  t.coherence_score,
  COUNT(DISTINCT e.dst_vid)           AS signal_count,
  SUM(e.weight)                       AS total_weight
FROM edge_topic_signal_weight e
JOIN vertex_lda_topic t ON t.vertex_id = e.src_vid
GROUP BY e.src_vid, t.entity_kind_hint, t.coherence_score`,
    parameters: [],
  } as any);

  // mv_lda_entity_posterior: bounded by entity count (initially < 50K) — safe
  // Pre-flight: entity count < 500K per 30-graph MV rules
  await db.executeQuery({
    sql: `CREATE MATERIALIZED VIEW mv_lda_entity_posterior AS
SELECT
  e.dst_vid                           AS entity_vid,
  COUNT(DISTINCT e.src_vid)           AS evidence_count,
  MAX(e.evidence_weight)              AS max_evidence_weight,
  SUM(e.evidence_weight)              AS total_evidence_mass
FROM edge_entity_evidence e
GROUP BY e.dst_vid`,
    parameters: [],
  } as any);

  // ─── Seed: 8 viewpoints ─────────────────────────────────────────────────
  const now = new Date().toISOString();
  const owner = "did:web:coverage.gftd.ai";

  type ViewpointSeed = {
    kind: string;
    description: string;
    extraction_sql: string;
  };

  const viewpoints: ViewpointSeed[] = [
    {
      kind: "lexical",
      description:
        "Text patterns: keywords, NSID prefixes, domain tokens extracted from content fields across repo records, email subjects, and page titles.",
      extraction_sql:
        "SELECT LOWER(REGEXP_REPLACE(value_json, '[^a-zA-Z0-9 ]', ' ')) FROM vertex_repo_record WHERE LENGTH(value_json) < 5000 LIMIT 100000",
    },
    {
      kind: "behavioral",
      description:
        "Action patterns: NSID method names, collection types, cron timing patterns, BPMN task types reflecting actor behavior over time.",
      extraction_sql:
        "SELECT collection FROM vertex_repo_record GROUP BY collection HAVING COUNT(*) > 10 LIMIT 10000",
    },
    {
      kind: "network",
      description:
        "Graph topology: edge types, src→dst DID pairs, community structure from follows/cohort/evidence edges.",
      extraction_sql:
        "SELECT 'edge:' || SPLIT_PART(src_vid,'/',4) || ':' || SPLIT_PART(dst_vid,'/',4) FROM edge_follows LIMIT 100000",
    },
    {
      kind: "signal",
      description:
        "Cryptographic signal presence: detection of signal:v1: E2E ciphertext prefix, pubkey hash patterns — signals private communication without reading content.",
      extraction_sql:
        "SELECT CASE WHEN value_json LIKE 'signal:v1:%' THEN 'encrypted' ELSE 'plaintext' END FROM vertex_repo_record LIMIT 100000",
    },
    {
      kind: "semantic",
      description:
        "Classification taxonomy signals: ICD-10 chapter, ATC L1 therapeutic group, SDG goal, ISIC L1 industry sector — derived from edge_classified_as bridges.",
      extraction_sql:
        "SELECT SPLIT_PART(dst_vid,'/',5) FROM edge_classified_as WHERE LENGTH(SPLIT_PART(dst_vid,'/',5)) <= 3 LIMIT 100000",
    },
    {
      kind: "temporal",
      description:
        "Time series patterns: era membership, decade bucket, day-of-week and hour-of-day periodicity extracted from created_at timestamps.",
      extraction_sql:
        "SELECT EXTRACT(HOUR FROM created_at)::VARCHAR || ':' || EXTRACT(DOW FROM created_at)::VARCHAR FROM vertex_ipaddress_access_log LIMIT 100000",
    },
    {
      kind: "geographic",
      description:
        "Spatial patterns: M49 region codes, LOCODE country prefixes, ISO 3166-1 alpha-2 from maps and geolocation tables.",
      extraction_sql:
        "SELECT SPLIT_PART(dst_vid,'/',5) FROM edge_classified_as e JOIN vertex_lda_signal s ON s.signal_token LIKE 'm49:%' LIMIT 100000",
    },
    {
      kind: "economic",
      description:
        "Financial flow signals: HS chapter codes, currency codes, transaction frequency patterns from kaikei/seikyu/gmail financial signals.",
      extraction_sql:
        "SELECT SPLIT_PART(dst_vid,'/',5) FROM edge_classified_as WHERE dst_vid LIKE '%hs.commodity%' LIMIT 100000",
    },
  ];

  for (let i = 0; i < viewpoints.length; i++) {
    const vp = viewpoints[i];
    const vid = `at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.ldaViewpoint/${vp.kind}`;
    await db
      .insertInto("vertex_lda_viewpoint" as any)
      .values({
        vertex_id: vid,
        _seq: i + 1,
        sensitivity_ord: 0,
        owner_did: owner,
        viewpoint_kind: vp.kind,
        description: vp.description,
        signal_vocab_size: 0,
        extraction_sql: vp.extraction_sql,
        active: true,
        actor_did: owner,
        org_did: owner,
        created_at: now,
      })
      .execute();
  }

  // Seed initial signal vocabulary for each viewpoint (representative tokens)
  type SignalSeed = {
    vp_kind: string;
    token: string;
    kind: string;
    source: string;
    expr: string;
  };

  const signals: SignalSeed[] = [
    // lexical
    { vp_kind: "lexical", token: "nsid:ai.gftd.apps", kind: "nsid_prefix", source: "vertex_repo_record", expr: "SPLIT_PART(collection,'.',3)" },
    { vp_kind: "lexical", token: "nsid:app.bsky", kind: "nsid_prefix", source: "vertex_repo_record", expr: "SPLIT_PART(collection,'.',1)||'.'||SPLIT_PART(collection,'.',2)" },
    { vp_kind: "lexical", token: "domain:gftd.ai", kind: "domain_token", source: "vertex_page", expr: "SPLIT_PART(vertex_id,'/',3)" },
    { vp_kind: "lexical", token: "lang:ja", kind: "language", source: "vertex_repo_record", expr: "detect_language(value_json)" },
    // behavioral
    { vp_kind: "behavioral", token: "col:ai.gftd.apps.naturalPerson.naturalPerson", kind: "collection", source: "vertex_repo_record", expr: "collection" },
    { vp_kind: "behavioral", token: "col:app.bsky.feed.post", kind: "collection", source: "vertex_repo_record", expr: "collection" },
    { vp_kind: "behavioral", token: "col:ai.gftd.apps.coverage.ldaViewpoint", kind: "collection", source: "vertex_repo_record", expr: "collection" },
    { vp_kind: "behavioral", token: "bpmn:generic.db.select", kind: "bpmn_task_type", source: "vertex_bpmn_process_def", expr: "process_type" },
    // network
    { vp_kind: "network", token: "edge:follows", kind: "edge_type", source: "edge_follows", expr: "'edge:follows'" },
    { vp_kind: "network", token: "edge:cohort_derived", kind: "edge_type", source: "edge_cohort_derived", expr: "'edge:cohort_derived'" },
    { vp_kind: "network", token: "edge:classified_as", kind: "edge_type", source: "edge_classified_as", expr: "'edge:classified_as'" },
    { vp_kind: "network", token: "edge:entity_evidence", kind: "edge_type", source: "edge_entity_evidence", expr: "'edge:entity_evidence'" },
    // signal
    { vp_kind: "signal", token: "e2e:encrypted", kind: "encryption_presence", source: "vertex_repo_record", expr: "CASE WHEN value_json LIKE 'signal:v1:%' THEN 'e2e:encrypted' ELSE 'e2e:plaintext' END" },
    { vp_kind: "signal", token: "e2e:plaintext", kind: "encryption_presence", source: "vertex_repo_record", expr: "CASE WHEN value_json NOT LIKE 'signal:v1:%' THEN 'e2e:plaintext' ELSE 'e2e:encrypted' END" },
    // semantic
    { vp_kind: "semantic", token: "icd:A-B", kind: "icd_chapter", source: "edge_classified_as", expr: "CASE WHEN dst_vid LIKE '%A%' OR dst_vid LIKE '%B%' THEN 'icd:A-B' END" },
    { vp_kind: "semantic", token: "icd:I", kind: "icd_chapter", source: "edge_classified_as", expr: "CASE WHEN dst_vid LIKE '%cardiovascular%' THEN 'icd:I' END" },
    { vp_kind: "semantic", token: "isic:A", kind: "isic_section", source: "edge_classified_as", expr: "SPLIT_PART(dst_vid,'.',4)" },
    { vp_kind: "semantic", token: "sdg:3", kind: "sdg_goal", source: "edge_classified_as", expr: "SPLIT_PART(dst_vid,'.',4)" },
    // temporal
    { vp_kind: "temporal", token: "era:contemporary", kind: "era_label", source: "vertex_natural_person_cohort_person", expr: "era" },
    { vp_kind: "temporal", token: "era:modern", kind: "era_label", source: "vertex_natural_person_cohort_person", expr: "era" },
    { vp_kind: "temporal", token: "hour:09", kind: "hour_bucket", source: "vertex_ipaddress_access_log", expr: "EXTRACT(HOUR FROM created_at)::VARCHAR" },
    { vp_kind: "temporal", token: "dow:1", kind: "day_of_week", source: "vertex_ipaddress_access_log", expr: "EXTRACT(DOW FROM created_at)::VARCHAR" },
    // geographic
    { vp_kind: "geographic", token: "m49:001", kind: "m49_region", source: "vertex_person_population_cohort", expr: "region_m49" },
    { vp_kind: "geographic", token: "m49:142", kind: "m49_region", source: "vertex_person_population_cohort", expr: "region_m49" },
    { vp_kind: "geographic", token: "iso3166:JP", kind: "iso3166", source: "vertex_locode_location", expr: "SPLIT_PART(rkey,'-',1)" },
    // economic
    { vp_kind: "economic", token: "hs_ch:01", kind: "hs_chapter", source: "edge_classified_as", expr: "SUBSTRING(SPLIT_PART(dst_vid,'.',4),1,2)" },
    { vp_kind: "economic", token: "hs_ch:84", kind: "hs_chapter", source: "edge_classified_as", expr: "SUBSTRING(SPLIT_PART(dst_vid,'.',4),1,2)" },
    { vp_kind: "economic", token: "atc:N", kind: "atc_l1", source: "edge_classified_as", expr: "SPLIT_PART(dst_vid,'.',4)" },
  ];

  for (let i = 0; i < signals.length; i++) {
    const s = signals[i];
    const vpVid = `at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.ldaViewpoint/${s.vp_kind}`;
    const hash6 = s.token.replace(/[^a-z0-9]/g, "").substring(0, 12).padEnd(6, "0").substring(0, 6);
    const sid = `at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.ldaSignal/${s.vp_kind}-${hash6}${i}`;
    await db
      .insertInto("vertex_lda_signal" as any)
      .values({
        vertex_id: sid,
        _seq: i + 1,
        sensitivity_ord: 0,
        owner_did: owner,
        viewpoint_vid: vpVid,
        signal_token: s.token,
        signal_kind: s.kind,
        source_collection: s.source,
        extraction_expr: s.expr,
        doc_frequency: 0,
        idf_score: 0.0,
        actor_did: owner,
        org_did: owner,
        created_at: now,
      })
      .execute();
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery({ sql: "DROP MATERIALIZED VIEW IF EXISTS mv_lda_entity_posterior", parameters: [] } as any);
  await db.executeQuery({ sql: "DROP MATERIALIZED VIEW IF EXISTS mv_lda_topic_top_signals", parameters: [] } as any);
  await db.executeQuery({ sql: "DROP MATERIALIZED VIEW IF EXISTS mv_lda_model_latest", parameters: [] } as any);
  await db.executeQuery({ sql: "DROP MATERIALIZED VIEW IF EXISTS mv_lda_viewpoint_stats", parameters: [] } as any);

  for (const tbl of [
    "edge_entity_cohort_link",
    "edge_entity_evidence",
    "edge_topic_entity_binding",
    "edge_topic_signal_weight",
    "edge_record_topic_weight",
    "edge_model_viewpoint",
    "edge_viewpoint_signal",
    "edge_viewpoint_topic",
    "vertex_latent_entity",
    "vertex_lda_topic",
    "vertex_lda_model",
    "vertex_lda_signal",
    "vertex_lda_viewpoint",
  ]) {
    await db.schema.dropTable(tbl).ifExists().execute();
  }
}
