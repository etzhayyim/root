import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR,
      did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
      indexed_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (record_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_indexed_at`)} ON ${sql.table(table)} (indexed_at)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await baseVertex(db, "vertex_kenkyusha_discipline");
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced4 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced_broad VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced_narrow VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS name_en VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS name_ja VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS paradigm VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS maturity VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS interdisciplinarity VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS cohort_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS publication_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS citation_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS frontier_count BIGINT`.execute(db);

  await baseVertex(db, "vertex_kenkyusha_frontier");
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS frontier_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS title TEXT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS description TEXT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS detection_method VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS primary_discipline VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS urgency VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS evidence_level VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS consensus_level VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS cohort_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS hypothesis_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS evidence_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS detected_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS last_analyzed_at VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kenkyusha_hypothesis");
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS hypothesis_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS frontier_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS statement TEXT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS rationale TEXT`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS llm_model VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS evaluated_at VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kenkyusha_evidence");
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS evidence_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS frontier_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS hypothesis_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_uri VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS evidence_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS extracted_claim TEXT`.execute(db);

  await baseVertex(db, "vertex_kenkyusha_did_registration");
  await sql`ALTER TABLE vertex_kenkyusha_did_registration ADD COLUMN IF NOT EXISTS path VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kenkyusha_did_registration ADD COLUMN IF NOT EXISTS display_name VARCHAR`.execute(db);

  await baseEdge(db, "edge_kenkyusha_frontier_discipline");
  await baseEdge(db, "edge_kenkyusha_hypothesis_frontier");
  await baseEdge(db, "edge_kenkyusha_evidence_hypothesis");

  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_discipline_isced ON vertex_kenkyusha_discipline (isced4)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_discipline_broad ON vertex_kenkyusha_discipline (isced_broad)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_id ON vertex_kenkyusha_frontier (frontier_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_discipline ON vertex_kenkyusha_frontier (primary_discipline, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_urgency ON vertex_kenkyusha_frontier (urgency, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_hypothesis_id ON vertex_kenkyusha_hypothesis (hypothesis_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_hypothesis_frontier ON vertex_kenkyusha_hypothesis (frontier_id, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_evidence_frontier ON vertex_kenkyusha_evidence (frontier_id, source_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kenkyusha_evidence_hypothesis ON vertex_kenkyusha_evidence (hypothesis_id, evidence_type)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_frontier_status_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kenkyusha_frontier_status_counts AS
    SELECT primary_discipline, urgency, status, count(*)::BIGINT AS frontier_count
    FROM vertex_kenkyusha_frontier
    GROUP BY primary_discipline, urgency, status
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_hypothesis_status_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kenkyusha_hypothesis_status_counts AS
    SELECT frontier_id, status, count(*)::BIGINT AS hypothesis_count, avg(confidence_score) AS avg_confidence_score
    FROM vertex_kenkyusha_hypothesis
    GROUP BY frontier_id, status
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_evidence_type_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kenkyusha_evidence_type_counts AS
    SELECT frontier_id, hypothesis_id, source_type, evidence_type, count(*)::BIGINT AS evidence_count
    FROM vertex_kenkyusha_evidence
    GROUP BY frontier_id, hypothesis_id, source_type, evidence_type
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_evidence_type_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_hypothesis_status_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_frontier_status_counts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_evidence_hypothesis`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_hypothesis_frontier`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_frontier_discipline`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_did_registration`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_evidence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_hypothesis`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_frontier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_discipline`.execute(db);
}
