import { Kysely, sql } from 'kysely';

/**
 * Migration 0070: HS 2012 (H4) commodity master + sitc4/cpc concordance repair.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 *
 * ## HS 2012 (H4) master
 * Source: https://comtradeapi.un.org/files/v1/app/reference/H4.json
 * 6,529 rows (chapters / headings / subheadings).
 * Stored as separate collection 'ai.gftd.apps.hs.commodity2012'.
 * Additionally 81 HS2012-only codes (restructured in HS2017) were patched
 * into 'ai.gftd.apps.hs.commodity' to resolve hs2012 concordance dst_vid dangling.
 *
 * ## Concordance repair (reverse-topological-sort pass)
 * Dangling edge analysis found:
 *   - sitc4: 71 src_vid CPC codes were CPC v2 codes not in v2.1
 *     → remapped via CPC2→CPC21 bridge (3,324 → 3,776 edges after 1→N expansion)
 *   - sitc4: 2 dst_vid SITC Roman-numeral section codes (I, II) → deleted
 *   - cpc: 52 dst_vid "n/a" ISIC codes → deleted (no ISIC mapping by design)
 *   - hs2012: 81 dst_vid HS codes in hs2012 but not hs2017 → patched (see above)
 *
 * Post-repair: 0 dangling edges across all concordance systems.
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ 'ai.gftd.apps.hs.commodity2012': 6,529 rows
 *   - vertex_repo_record @ 'ai.gftd.apps.hs.commodity': 6,789 rows (6,708 + 81 hs2012-only)
 *   - view_hs2012_commodity: new
 *   - edge_classified_as system='sitc4': 3,776 edges (remapped to CPC21)
 *   - edge_classified_as system='cpc': 2,663 edges (52 n/a deleted)
 *   - dim_world_domain.hs2012.world_total: 6,529
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── view_hs2012_commodity ─────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_hs2012_commodity AS
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
    WHERE collection = 'ai.gftd.apps.hs.commodity2012'
  `.execute(db);

  // ── dim_world_domain ──────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2012', 'hs2012.gftd.ai', 6529, 'products', 'trade')
  `.execute(db);

  // ── concordance repair: data-only, idempotent ─────────────────────────
  // sitc4: DELETE Roman-numeral section codes
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4' AND code IN ('I','II')`.execute(db);
  // cpc: DELETE n/a ISIC mapping edges
  await sql`
    DELETE FROM edge_classified_as
    WHERE system = 'cpc' AND dst_vid LIKE '%/n/a'
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_hs2012_commodity`.execute(db);
  await sql`
    DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.hs.commodity2012'
  `.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'hs2012'`.execute(db);
}
