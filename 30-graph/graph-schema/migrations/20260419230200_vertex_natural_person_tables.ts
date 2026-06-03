import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_natural_person_* — 4 tables for np02priv9 domain writes (Phase 1A–1.5).
 * cohort_person carries the full 26-dimension cohort hash (see
 * 60-apps/etzhayyim-project-natural-person/CLAUDE.md).
 * PII tier 3 guardrail: sensitivity_ord=300 default for cohort_person /
 * identified_person / person_enrichment so they never federate via AT Relay.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_natural_person_cohort_person (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      cohort_hash VARCHAR, cohort_did VARCHAR,
      country VARCHAR, region VARCHAR, municipality VARCHAR,
      age VARCHAR, gender VARCHAR,
      income_decile VARCHAR, education_isced VARCHAR, occupation_isco VARCHAR,
      employment_status VARCHAR, marital_status VARCHAR,
      household_size VARCHAR, housing_tenure VARCHAR, urban_rural VARCHAR,
      health_icd10 VARCHAR, disability_type VARCHAR, migration_status VARCHAR,
      ethnicity VARCHAR, religion VARCHAR, language_primary VARCHAR,
      entity_did VARCHAR, community_id VARCHAR,
      vital_status VARCHAR, birth_year VARCHAR, death_year VARCHAR,
      death_cause_icd10 VARCHAR, era VARCHAR,
      data_classification VARCHAR, rationale VARCHAR,
      intel_chain_id VARCHAR, intel_estimated_count BIGINT,
      intel_confidence VARCHAR, intel_entity_type VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_natural_person_identified_person (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      person_hash VARCHAR, cohort_did VARCHAR,
      name VARCHAR, country VARCHAR, role VARCHAR, organization VARCHAR,
      source_app VARCHAR, source_record_id VARCHAR,
      enrichment_status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_natural_person_person_enrichment (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      person_hash VARCHAR, enrichment_method VARCHAR, source_url VARCHAR,
      extracted_data VARCHAR, confidence VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_natural_person_census_source (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      source_name VARCHAR, source_org VARCHAR, source_url VARCHAR,
      data_year VARCHAR, dimensions VARCHAR, status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const t of [
    'vertex_natural_person_census_source',
    'vertex_natural_person_person_enrichment',
    'vertex_natural_person_identified_person',
    'vertex_natural_person_cohort_person',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
