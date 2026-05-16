import type { Kysely } from "kysely";
import { sql } from "kysely";

async function createEdgeTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      relation VARCHAR,
      analysis_id VARCHAR,
      sms_id VARCHAR,
      url_id VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_analysis`)} ON ${sql.table(table)} (analysis_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_url`)} ON ${sql.table(table)} (url_id)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_smishing_geo_intel (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      geo_id VARCHAR,
      url_id VARCHAR,
      analysis_id VARCHAR,
      domain VARCHAR,
      ip_address VARCHAR,
      asn VARCHAR,
      country VARCHAR,
      provider VARCHAR,
      risk_score DOUBLE PRECISION,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_smishing_ioc_indicator (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      ioc_id VARCHAR,
      value VARCHAR,
      ioc_type VARCHAR,
      domain VARCHAR,
      url VARCHAR,
      source_collection VARCHAR,
      source_rkey VARCHAR,
      confidence DOUBLE PRECISION,
      first_seen_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_geo_url_id ON vertex_smishing_geo_intel (url_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_geo_analysis_id ON vertex_smishing_geo_intel (analysis_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_geo_domain ON vertex_smishing_geo_intel (domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_geo_country ON vertex_smishing_geo_intel (country)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_ioc_value ON vertex_smishing_ioc_indicator (value)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_ioc_type ON vertex_smishing_ioc_indicator (ioc_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_ioc_domain ON vertex_smishing_ioc_indicator (domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_smishing_ioc_source ON vertex_smishing_ioc_indicator (source_collection, source_rkey)`.execute(db);

  for (const table of [
    "edge_smishing_sms_threat_detection",
    "edge_smishing_threat_url",
    "edge_smishing_url_geo",
    "edge_smishing_url_takedown",
    "edge_smishing_url_ioc",
  ]) {
    await createEdgeTable(db, table);
  }

  await sql`
    INSERT INTO edge_smishing_sms_threat_detection (
      edge_id, src_vid, dst_vid, relation, analysis_id, sms_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:smishing:sms-threat:' || s.sms_id || ':' || t.analysis_id,
      s.vertex_id,
      t.vertex_id,
      'ANALYZED_AS',
      t.analysis_id,
      s.sms_id,
      coalesce(t.owner_did, s.owner_did),
      t.actor_id,
      t.created_at
    FROM vertex_smishing_sms_message s
    JOIN vertex_smishing_threat_detection t ON t.sms_id = s.sms_id
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    INSERT INTO edge_smishing_threat_url (
      edge_id, src_vid, dst_vid, relation, analysis_id, sms_id, url_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:smishing:threat-url:' || t.analysis_id || ':' || u.url_id,
      t.vertex_id,
      u.vertex_id,
      'EXTRACTED_URL',
      t.analysis_id,
      t.sms_id,
      u.url_id,
      coalesce(u.owner_did, t.owner_did),
      u.actor_id,
      u.created_at
    FROM vertex_smishing_threat_detection t
    JOIN vertex_smishing_url_intel u ON u.analysis_id = t.analysis_id OR u.sms_id = t.sms_id
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    INSERT INTO edge_smishing_url_geo (
      edge_id, src_vid, dst_vid, relation, analysis_id, url_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:smishing:url-geo:' || u.url_id || ':' || g.vertex_id,
      u.vertex_id,
      g.vertex_id,
      'HAS_GEO_INTEL',
      coalesce(g.analysis_id, u.analysis_id),
      u.url_id,
      coalesce(g.owner_did, u.owner_did),
      g.actor_id,
      g.created_at
    FROM vertex_smishing_url_intel u
    JOIN vertex_smishing_geo_intel g ON g.url_id = u.url_id
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    INSERT INTO edge_smishing_url_takedown (
      edge_id, src_vid, dst_vid, relation, analysis_id, url_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:smishing:url-takedown:' || u.url_id || ':' || td.takedown_id,
      u.vertex_id,
      td.vertex_id,
      'REQUESTED_TAKEDOWN',
      coalesce(td.analysis_id, u.analysis_id),
      u.url_id,
      coalesce(td.owner_did, u.owner_did),
      td.actor_id,
      td.created_at
    FROM vertex_smishing_url_intel u
    JOIN vertex_smishing_takedown_request td ON td.url_id = u.url_id
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    INSERT INTO edge_smishing_url_ioc (
      edge_id, src_vid, dst_vid, relation, analysis_id, url_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:smishing:url-ioc:' || u.url_id || ':' || i.vertex_id,
      u.vertex_id,
      i.vertex_id,
      'CONFIRMED_BY_IOC',
      u.analysis_id,
      u.url_id,
      coalesce(i.owner_did, u.owner_did),
      i.actor_id,
      coalesce(i.created_at, u.created_at)
    FROM vertex_smishing_url_intel u
    JOIN vertex_smishing_ioc_indicator i
      ON (i.value IS NOT NULL AND i.value <> '' AND (position(i.value in u.url) > 0 OR position(i.value in u.domain) > 0))
       OR (i.domain IS NOT NULL AND i.domain <> '' AND i.domain = u.domain)
       OR (i.url IS NOT NULL AND i.url <> '' AND i.url = u.url)
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_smishing_url_risk AS
    SELECT
      u.url_id,
      u.analysis_id,
      u.domain,
      max(u.score) AS url_score,
      bool_or(coalesce(u.ioc_confirmed, false)) OR count(i.dst_vid) > 0 AS ioc_confirmed,
      count(DISTINCT g.dst_vid) AS geo_intel_count,
      count(DISTINCT td.dst_vid) AS takedown_count
    FROM vertex_smishing_url_intel u
    LEFT JOIN edge_smishing_url_geo g ON g.src_vid = u.vertex_id
    LEFT JOIN edge_smishing_url_takedown td ON td.src_vid = u.vertex_id
    LEFT JOIN edge_smishing_url_ioc i ON i.src_vid = u.vertex_id
    GROUP BY u.url_id, u.analysis_id, u.domain
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_smishing_threat_flow AS
    SELECT
      t.analysis_id,
      t.sms_id,
      t.classification,
      t.score,
      count(DISTINCT u.dst_vid) AS url_count,
      count(DISTINCT td.dst_vid) AS takedown_count,
      max(t.created_at) AS analyzed_at
    FROM vertex_smishing_threat_detection t
    LEFT JOIN edge_smishing_threat_url u ON u.src_vid = t.vertex_id
    LEFT JOIN edge_smishing_url_takedown td ON td.analysis_id = t.analysis_id
    GROUP BY t.analysis_id, t.sms_id, t.classification, t.score
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_smishing_threat_flow`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_smishing_url_risk`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_smishing_url_ioc`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_smishing_url_takedown`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_smishing_url_geo`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_smishing_threat_url`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_smishing_sms_threat_detection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_smishing_ioc_indicator`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_smishing_geo_intel`.execute(db);
}
