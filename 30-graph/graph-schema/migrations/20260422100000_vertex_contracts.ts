import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_contracts_* — projection of vertex_legal_entity into
 * social-contract.etzhayyim.com:entity:* DID space, plus fresh-crawl
 * vertex_contracts_social_contract (constitution / treaty).
 *
 * Design (ADR-0049 contracts pilot, 2026-04-22):
 *   vertex_contracts_organization is a PROJECTION over vertex_legal_entity
 *   (123.5M rows already ingested by legal-entity.etzhayyim.com crawler).
 *   legal_entity_ref is the foreign key back to the authoritative row.
 *   vertex_id is content-addressed via the minted entity DID so repeat
 *   projection is idempotent (ON CONFLICT (vertex_id) DO NOTHING).
 *
 *   vertex_contracts_social_contract is FRESH CRAWL output from
 *   UN Treaty Collection / Constitute Project (law full-text corpus is
 *   out of scope — delegated to houbun.etzhayyim.com per ADR-0052).
 *
 * Write path: Hyperdrive direct (ADR-0036). Handlers:
 *   20-actors/magatama/py/src/pymagatama/handlers/contracts.py
 *
 * Related:
 *   ADR-0049 shared Python UDF pool
 *   ADR-0036 worker-direct Hyperdrive persistence
 *   ADR-0052 houbun actor topology (complementary, law full-text)
 *   60-apps/etzhayyim-project-social-contract/CLAUDE.md — entity DID pattern
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_contracts_organization: projection over vertex_legal_entity ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_contracts_organization (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      did VARCHAR,
      legal_entity_ref VARCHAR,
      country VARCHAR,
      lei VARCHAR,
      national_id VARCHAR,
      name VARCHAR,
      legal_name VARCHAR,
      entity_type VARCHAR,
      isic VARCHAR,
      duns VARCHAR,
      wikidata_qid VARCHAR,
      opencorporates_id VARCHAR,
      status VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      confidence DOUBLE PRECISION,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Projection lookup back to the authoritative legal-entity row.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_legal_entity_ref
      ON vertex_contracts_organization (legal_entity_ref)
  `.execute(db);

  // Primary business-key lookups for resolveOrganization XRPC.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_lei
      ON vertex_contracts_organization (lei)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_national_id
      ON vertex_contracts_organization (national_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_did
      ON vertex_contracts_organization (did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_country
      ON vertex_contracts_organization (country)
  `.execute(db);

  // ── vertex_contracts_social_contract: fresh crawl (treaty / constitution) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_contracts_social_contract (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      name VARCHAR,
      constitutional_type VARCHAR,
      jurisdiction VARCHAR,
      adopted_date VARCHAR,
      effective_date VARCHAR,
      scope VARCHAR,
      url VARCHAR,
      un_reg_no VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      confidence DOUBLE PRECISION,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_jurisdiction
      ON vertex_contracts_social_contract (jurisdiction)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_source_record_id
      ON vertex_contracts_social_contract (source_record_id)
  `.execute(db);

  // ── edge_contracts_grantedBy: (Authority)-GRANTS->(Organization) ──
  // src_vid = sovereign authority DID, dst_vid = organization DID.
  // Populated lazily by mintOrganizationDid when country is known.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_contracts_grantedBy (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      contract_type VARCHAR,
      granted_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_contracts_grantedBy_src
      ON edge_contracts_grantedBy (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_contracts_grantedBy_dst
      ON edge_contracts_grantedBy (dst_vid)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_contracts_grantedBy_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_contracts_grantedBy_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_contracts_grantedBy`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_contracts_social_contract_source_record_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_social_contract_jurisdiction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_contracts_social_contract`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_contracts_org_country`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_org_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_org_national_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_org_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_org_legal_entity_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_contracts_organization`.execute(db);
}
