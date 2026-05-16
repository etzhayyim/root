import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260428230000: business-person career/skill/cert/edu tables.
 *
 * Separate tables for structured career history, skill linkage (→ ESCO vertex_skill),
 * certifications, and education for vertex_business_person entries.
 * Sensitivity: sensitivity_ord=200 (ADR-0018 Tier 3 identified person).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Career events: one row per role/org tenure
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_person_career_event (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      org_name          VARCHAR,
      org_did           VARCHAR,
      title             VARCHAR,
      department        VARCHAR,
      employment_type   VARCHAR,
      since             VARCHAR,
      until             VARCHAR,
      country           VARCHAR,
      description       VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  // Edge: business_person → vertex_skill (ESCO skill taxonomy, migration 0041)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_business_person_skill (
      edge_id           VARCHAR PRIMARY KEY,
      person_vertex_id  VARCHAR,
      skill_id          VARCHAR,
      proficiency_level VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);

  // Certifications: CISSP, CISM, CISA, CEH, CompTIA, etc.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_person_cert (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      cert_name         VARCHAR,
      cert_code         VARCHAR,
      issuer            VARCHAR,
      issued_at         VARCHAR,
      expires_at        VARCHAR,
      credential_url    VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  // Education: university, degree, field of study
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_person_edu (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      institution       VARCHAR,
      degree            VARCHAR,
      field_of_study    VARCHAR,
      start_year        VARCHAR,
      end_year          VARCHAR,
      country           VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_business_person_edu`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_person_cert`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_business_person_skill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_person_career_event`.execute(db);
}
