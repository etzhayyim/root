import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A  (TLD policy / registrar catalog / eligibility advisory — public
//          reference data, no PII; registrant draft records carry only the
//          domain owner DID, not contact PII per ADR-0018 Tier 1)

/**
 * domain.etzhayyim.com Phase 1 — TLD registration assistance schema
 * (ADR-0036 Worker-direct Hyperdrive + ADR-0056 BPMN-as-actor +
 *  ADR-2604282300 T2 = pymagatama + Zeebe, no CF Worker).
 *
 * Tables (5 vertex + 2 edge):
 *   vertex_domain_tld                 TLD catalog (.law / .lawyer / ...)
 *   vertex_domain_registrar           registrar catalog (cloudflare / namecheap / ...)
 *   vertex_domain_eligibility_advice  TLD × jurisdiction × regulator advisory
 *   vertex_domain_registration        etzhayyim-side registration ledger (draft → active)
 *   vertex_domain_legal_regulator     legal regulator catalog (JFBA / ABA / SRA / ...)
 *   edge_domain_registrar_supports_tld   registrar ⇄ TLD support matrix
 *   edge_domain_tld_accepts_regulator    TLD ⇄ accepted Legal Regulator
 *
 * Streaming MVs (1):
 *   mv_domain_registrable_via         per-TLD: open registrar + restriction
 *                                     summary, used by registerAssist BPMN
 *
 * Cardinality is small (~tens of TLDs × ~tens of registrars), so MV is safe
 * (well below the 500K-key guardrail in 30-graph/graph-schema/CLAUDE.md).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_tld (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      tld varchar NOT NULL,
      operator varchar NOT NULL,
      restricted boolean NOT NULL,
      eligibility_summary varchar,
      eligibility_policy_url varchar,
      verification_required boolean NOT NULL,
      typical_uses varchar,
      notes varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_registrar (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      registrar_slug varchar NOT NULL,
      name varchar NOT NULL,
      homepage_url varchar,
      iana_id varchar,
      jp_friendly boolean,
      notes varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_legal_regulator (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      regulator_slug varchar NOT NULL,
      name varchar NOT NULL,
      jurisdiction varchar NOT NULL,
      kind varchar NOT NULL,
      public_register_url varchar,
      notes varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_eligibility_advice (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      tld varchar NOT NULL,
      jurisdiction varchar NOT NULL,
      regulator_slug varchar,
      actor_kind varchar NOT NULL,
      eligible boolean NOT NULL,
      basis varchar NOT NULL,
      policy_excerpt varchar,
      source_url varchar,
      effective_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_registration (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      domain_name varchar NOT NULL,
      tld varchar NOT NULL,
      registrar_slug varchar,
      registrant_did varchar NOT NULL,
      registrant_name varchar,
      registrant_kind varchar NOT NULL,
      jurisdiction varchar,
      regulator_slug varchar,
      eligibility_evidence_url varchar,
      eligibility_advice_vid varchar,
      registered_at varchar,
      expires_at varchar,
      auto_renew boolean,
      ns_provider varchar,
      status varchar NOT NULL,
      notes varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_domain_registrar_supports_tld (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      registrar_slug varchar NOT NULL,
      tld varchar NOT NULL,
      verified_at varchar,
      handles_verification boolean,
      notes varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_domain_tld_accepts_regulator (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      tld varchar NOT NULL,
      regulator_slug varchar NOT NULL,
      basis varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MV ───────────────────────────────────────────────────
  // Per-TLD rollup of supporting registrars + restriction status.
  // Cardinality: ~tens of TLDs × ~tens of registrars (MV safe).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_registrable_via AS
      SELECT
        t.tld,
        t.operator,
        t.restricted,
        t.verification_required,
        t.eligibility_summary,
        COUNT(e.edge_id) AS registrar_count
      FROM vertex_domain_tld t
      LEFT JOIN edge_domain_registrar_supports_tld e
        ON e.tld = t.tld
      WHERE t.status = 'active'
      GROUP BY t.tld, t.operator, t.restricted, t.verification_required, t.eligibility_summary;
  `.execute(db);

  // ── Grants ─────────────────────────────────────────────────────────
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_tld                    TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_tld                    TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_registrar              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_registrar              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_legal_regulator        TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_legal_regulator        TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_eligibility_advice     TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_eligibility_advice     TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_registration           TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_domain_registration           TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_domain_registrar_supports_tld   TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_domain_registrar_supports_tld   TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_domain_tld_accepts_regulator    TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_domain_tld_accepts_regulator    TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_registrable_via`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_domain_tld_accepts_regulator`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_domain_registrar_supports_tld`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_registration`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_eligibility_advice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_legal_regulator`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_registrar`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_tld`.execute(db);
}
