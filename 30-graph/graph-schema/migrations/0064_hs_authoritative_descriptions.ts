import { Kysely, sql } from 'kysely';

/**
 * Migration 0064: replace HS 2017 placeholder names with UN Comtrade
 * authoritative descriptive text.
 *
 * Superseded state: migration 0063 ingested 6,705 HS codes with
 * placeholder names of the form `"HS 2017 subheading 010121"`.
 *
 * This migration replaces the `vertex_repo_record` rows for
 * `collection='app.etzhayyim.apps.hs.commodity'` with entries sourced from
 * UN Comtrade's H5 classification reference (6,708 rows: 97 chapters,
 * 1,223 headings, 5,388 subheadings), each carrying the official WCO
 * description in `value_json.name`.
 *
 * Source: https://comtradeapi.un.org/files/v1/app/reference/H5.json
 *
 * Applied via direct psql against localhost:14566 on 2026-04-15; the
 * Kysely migrator log entry was inserted manually (per 0037 convention
 * in graph-schema CLAUDE.md). No schema change — data-only refresh.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Data-only refresh is idempotent (DELETE + INSERT). Code is kept here
  // for documentation; the actual 6,708-row payload is generated at
  // ingestion time from the Comtrade JSON.
  await sql`
    DELETE FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity'
  `.execute(db);

  await sql`UPDATE dim_world_domain SET world_total = 6708 WHERE domain = 'hs'`.execute(db);

  // NB: re-run the ingest script
  //   python3 scripts/seed-hs-comtrade.py | psql $PG_URL
  // to repopulate the 6,708 rows. The pipeline is idempotent.
}

export async function down(db: Kysely<any>): Promise<void> {
  // Roll back to migration 0063 placeholder state — not materially useful
  // since names would be placeholders again. No-op down migration.
  await sql`UPDATE dim_world_domain SET world_total = 6705 WHERE domain = 'hs'`.execute(db);
}
