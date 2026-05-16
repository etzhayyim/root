import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260428250000: influence analytics schema.
 *
 * - ALTER edge_business_person_relation: add confidence + verification_status
 *   (provenance gate — llm_inferred vs verified)
 * - Indexes on person_vertex_id for all 4 career/skill/cert/edu tables
 * - vertex_influence_score: per-person centrality cache written by scoreInfluence BPMN
 * - mv_influence_centrality: SQL streaming MV (pure out/in-degree + gov/bridge scores)
 *   Cardinality: 7 persons max (no OOM risk, no BACKGROUND DDL needed)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Provenance columns on relation edge
  await sql`ALTER TABLE edge_business_person_relation
    ADD COLUMN confidence DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE edge_business_person_relation
    ADD COLUMN verification_status VARCHAR`.execute(db);

  // Indexes for graph traversal
  await sql`CREATE INDEX IF NOT EXISTS idx_bpcareer_person
    ON vertex_business_person_career_event(person_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bpskill_person
    ON edge_business_person_skill(person_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bpcert_person
    ON vertex_business_person_cert(person_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bpedu_person
    ON vertex_business_person_edu(person_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bprel_src
    ON edge_business_person_relation(src_person_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bprel_dst
    ON edge_business_person_relation(dst_person_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_bprel_type
    ON edge_business_person_relation(relation_type)`.execute(db);

  // Influence score cache — written by scoreInfluence.bpmn (R/PT24H)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_influence_score (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      faction_label     VARCHAR,
      hub_score         DOUBLE PRECISION,
      bridge_score      DOUBLE PRECISION,
      gov_score         DOUBLE PRECISION,
      out_degree        BIGINT,
      in_degree         BIGINT,
      cross_faction_edges BIGINT,
      career_span_years BIGINT,
      computed_at       VARCHAR
    )
  `.execute(db);

  // Streaming MV: pure SQL centrality from relation edges
  // Cardinality bounded by vertex_business_person row count (~7) — safe for streaming
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_influence_centrality AS
    SELECT
      p.vertex_id                                         AS person_id,
      p.name_ja,
      p.org_name,
      COALESCE(o.out_deg, 0)                              AS out_degree,
      COALESCE(i.in_deg, 0)                               AS in_degree,
      COALESCE(o.out_deg, 0) + COALESCE(i.in_deg, 0)     AS hub_score,
      COALESCE(g.gov_deg, 0)                              AS gov_score,
      COALESCE(x.cross_deg, 0)                            AS bridge_score,
      COALESCE(str.strong_deg, 0)                         AS strong_tie_count,
      COALESCE(c.career_count, 0)                         AS career_event_count
    FROM vertex_business_person p
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS out_deg
      FROM edge_business_person_relation
      GROUP BY src_person_id
    ) o ON o.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT dst_person_id, COUNT(*) AS in_deg
      FROM edge_business_person_relation
      GROUP BY dst_person_id
    ) i ON i.dst_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS gov_deg
      FROM edge_business_person_relation
      WHERE relation_type = 'government_advisory'
      GROUP BY src_person_id
    ) g ON g.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS cross_deg
      FROM edge_business_person_relation
      WHERE relation_type IN ('conference_co_speaker', 'consortium_member', 'government_advisory')
      GROUP BY src_person_id
    ) x ON x.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS strong_deg
      FROM edge_business_person_relation
      WHERE strength = 'strong'
      GROUP BY src_person_id
    ) str ON str.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT person_vertex_id, COUNT(*) AS career_count
      FROM vertex_business_person_career_event
      GROUP BY person_vertex_id
    ) c ON c.person_vertex_id = p.vertex_id
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_influence_centrality`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_influence_score`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bprel_type`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bprel_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bprel_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bpedu_person`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bpcert_person`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bpskill_person`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bpcareer_person`.execute(db);
  await sql`ALTER TABLE edge_business_person_relation DROP COLUMN IF EXISTS verification_status`.execute(db);
  await sql`ALTER TABLE edge_business_person_relation DROP COLUMN IF EXISTS confidence`.execute(db);
}
