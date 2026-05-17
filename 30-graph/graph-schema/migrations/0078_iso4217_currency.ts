import { Kysely, sql } from 'kysely';

/**
 * Migration 0078: ISO 4217 currency codes.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 5 concluded).
 *
 * ## New taxonomy master
 *
 * | Collection                     | Rows | Source                                         |
 * |--------------------------------|------|------------------------------------------------|
 * | ai.gftd.apps.iso4217.currency  |  178 | github.com/datasets/currency-codes (ISO 4217)  |
 *
 * ### ISO 4217 (International Standard for Currency Codes)
 * 178 active currencies (alphabetic code + numeric code + minor unit).
 * Source: ISO / UN Statistics Division. Active currencies only (no WithdrawalDate).
 * Each entry stores: name, numeric_code, minor_unit, entity (country/territory name).
 * Hierarchy: single-level flat list (no parent—all codes are leaf nodes).
 *
 * Used by: SWIFT (BIC), IBAN, financial messaging, trade finance, FX trading.
 * Links to: sovereign.m49_region via entity name matching (future concordance).
 *
 * ## New view
 *
 * - view_iso4217_currency: projection of ai.gftd.apps.iso4217.currency
 *
 * ## Topology integrity
 *
 * 0 orphan nodes (flat single-level hierarchy, no parent refs).
 * No new concordance edges.
 *
 * dim_world_domain addition: iso4217.
 *
 * ## Summary: taxonomy coverage after iteration 5 (2026-04-15)
 *
 * Total taxonomy collections: 22+ standard classification systems.
 * Total concordance edges: 86,167 (27 systems, excl. openalex 159,739 + ipc 1).
 *
 * Complete version chains:
 * - HS: 1996→2002→2007→2012→2017→2022 (6 editions, 5 bridges)
 * - SITC: Rev.1→Rev.2→Rev.3→Rev.4 (4 editions, 3 bridges)
 * - ISIC: Rev.2→Rev.3.1→Rev.4→Rev.5 (4 editions, 3 bridges)
 * - CPC: Ver.2→Ver.2.1→Ver.3 (3 editions, 2 bridges)
 * - NACE: (Rev.1 bridged via ISIC Rev.4) Rev.2→ISIC Rev.4 (679 edges)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE VIEW IF NOT EXISTS view_iso4217_currency AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'       AS name,
      value_json::jsonb->>'numeric'    AS numeric_code,
      value_json::jsonb->>'minor_unit' AS minor_unit,
      value_json::jsonb->>'entity'     AS entity,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.iso4217.currency'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso4217', 'iso4217.etzhayyim.com', 178, 'currencies', 'finance')
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_iso4217_currency`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.iso4217.currency'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'iso4217'`.execute(db);
}
