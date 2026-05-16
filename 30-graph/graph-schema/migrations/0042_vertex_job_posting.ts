import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0042: vertex_job_posting + edge_posting_employer / edge_posting_occupation.
 *
 * Stores corporate-linked job postings from public-feed sources only.
 * Every posting MUST anchor to a vertex_legal_entity row via employer_did
 * (LEI / JP 法人番号 / SIREN / etc.). Postings without employer anchor are rejected.
 *
 * Allowed sources (per recruit actor manifest governance.dataSources.allowed):
 *   usajobs, jobbank, eures, hellowork
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_job_posting (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      source_id         VARCHAR,
      source_url        VARCHAR,
      title             VARCHAR,
      description       VARCHAR,
      employer_did      VARCHAR,
      employer_name     VARCHAR,
      employer_registry_id VARCHAR,
      isco_code         VARCHAR,
      onet_soc_code     VARCHAR,
      country           VARCHAR,
      location          VARCHAR,
      remote_allowed    BOOLEAN,
      employment_type   VARCHAR,
      salary_min        DOUBLE PRECISION,
      salary_max        DOUBLE PRECISION,
      salary_currency   VARCHAR,
      posted_at         VARCHAR,
      expires_at        VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_posting_occupation (
      edge_id           VARCHAR PRIMARY KEY,
      posting_id        VARCHAR,
      occupation_id     VARCHAR,
      mapping_source    VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_posting_occupation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_job_posting`.execute(db);
}
