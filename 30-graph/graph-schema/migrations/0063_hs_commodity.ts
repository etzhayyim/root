import { Kysely, sql } from 'kysely';

/**
 * Migration 0063: HS 2017 commodity master + CPC↔HS concordance.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 * Data sources (UNSD authoritative):
 *   - /tables/CPC/CPCv21_HS2017/CPC21-HS2017.csv  (5,843 rows → 5,387 unique HS2017 subheadings)
 *   - /tables/CPC/CPCv21_HS12/cpc21-hs2012.txt    (5,584 rows → 5,205 unique HS2012 subheadings)
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ collection='app.etzhayyim.apps.hs.commodity'
 *       96 chapters + 1,222 headings + 5,387 subheadings = 6,705 rows
 *   - edge_classified_as system='hs2017' : 5,843 rows
 *   - edge_classified_as system='hs2012' : 5,584 rows
 *   - dim_world_domain.hs.world_total   : 6,705
 *
 * Names are placeholders (`"HS 2017 subheading 010121"` etc.) until WCO
 * descriptive text is ingested in a follow-up pass; codes themselves are
 * authoritative from UNSD.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE VIEW IF NOT EXISTS view_hs_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity'
  `.execute(db);

  await sql`UPDATE dim_world_domain SET world_total = 6705 WHERE domain = 'hs'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_hs_commodity`.execute(db);
  await sql`UPDATE dim_world_domain SET world_total = 5300 WHERE domain = 'hs'`.execute(db);
}
