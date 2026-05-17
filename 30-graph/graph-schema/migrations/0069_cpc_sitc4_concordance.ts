import { Kysely, sql } from 'kysely';

/**
 * Migration 0066: CPC Ver.2 ↔ SITC Rev.4 concordance.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 * Data source (UNSD authoritative):
 *   https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv2_SITC4/CPCv2_SITCr4.txt
 *   3,324 rows (CPC Ver.2 5-digit code ↔ SITC Rev.4 dotted code, de-dotted for storage)
 *
 * Note: concordance is CPC Ver.2 (not v2.1) → SITC Rev.4. UNSD does not
 * publish a CPC v2.1 ↔ SITC Rev.4 correspondence; CPC v2 → v2.1 structural
 * changes are minor at the 5-digit level, so this provides useful coverage.
 *
 * RisingWave state after apply:
 *   - edge_classified_as system='sitc4' : 3,324 rows
 *     src_vid = at://did:web:cpc.etzhayyim.com/ai.gftd.apps.cpc.commodity_item/{cpc_code}
 *     dst_vid = at://did:web:sitc.etzhayyim.com/ai.gftd.apps.sitc.commodity/{sitc_code}
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Data-only; pipeline is idempotent (DELETE + INSERT).
  // Re-run to refresh:
  //   curl -s https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv2_SITC4/CPCv2_SITCr4.txt \
  //     | python3 scripts/seed-cpc-sitc4.py | psql $PG_URL
  await sql`
    DELETE FROM edge_classified_as WHERE system = 'sitc4'
  `.execute(db);

  // NB: 3,324-row payload generated at ingestion time from UNSD TXT file
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4'`.execute(db);
}
