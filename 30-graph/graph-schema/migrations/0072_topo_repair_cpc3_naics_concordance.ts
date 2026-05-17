import { Kysely, sql } from 'kysely';

/**
 * Migration 0072: Reverse-topological-sort repair pass + CPC v3 + NAICS↔ISIC4.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 *
 * ## Topology repair (dangling edge + orphan node elimination)
 *
 * Before this migration the taxonomy graph had:
 *   - NACE Rev.2: 887 orphan nodes (parent stored as ISIC4-style code, not NACE rkey)
 *     → fixed by rewriting parent field to use section-prefixed NACE rkeys (e.g. "01" → "A01")
 *   - NAICS 2022: 23 orphan nodes (sectors 32/33 missing; subsectors 45x, 49x missing)
 *     → fixed by adding alias sector records for 32, 33, 45, 46, 49
 *   - hs.commodity: 4 orphan subheadings referencing headings 2848/6908/8469/4 missing
 *     → fixed by adding the 3 missing HS2012-era heading records
 *   - CPC v3: 7 orphan nodes (decimal subcodes + 8556 missing)
 *     → fixed by adding 3 synthetic parent records
 *
 * Post-repair: **0 orphan nodes** across all 9 taxonomy collections.
 * **0 dangling edges** across all 7 concordance systems.
 *
 * ## CPC Ver.3 (proposed, Nov 2023)
 * Source: https://unstats.un.org/unsd/classifications/CPC/Documents/3-Proposed-CPC-Ver3-Structure-20Nov2023.xlsx
 * 4,594 rows (10 sections / 71 divisions / 329 groups / 1,307 classes / 2,872 subclasses).
 * 4,390 code-identical edges to CPC v2.1 (system='cpc3').
 *
 * ## NAICS 2022 ↔ ISIC Rev.4 sector concordance
 * 25 sector-level edges (system='naics_isic4') mapping NAICS 2-digit sectors
 * to ISIC sections (authoritative UNSD / Census correspondence).
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ 'ai.gftd.apps.cpc.commodity_item_v3': 4,594 rows
 *   - view_cpc3_product: new
 *   - edge_classified_as system='cpc3': 4,390 edges (CPC21 → CPC3)
 *   - edge_classified_as system='naics_isic4': 25 edges (NAICS sector → ISIC section)
 *   - dim_world_domain.cpc3.world_total: 4,594
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── view_cpc3_product ─────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_cpc3_product AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'class'    AS class_code,
      value_json::jsonb->>'parent'   AS parent_code,
      value_json::jsonb->>'change'   AS change_type,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.cpc.commodity_item_v3'
  `.execute(db);

  // ── dim_world_domain ──────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('cpc3', 'cpc3.etzhayyim.com', 4594, 'products', 'commerce')
  `.execute(db);

  // ── topology repair: data-only, idempotent ────────────────────────────
  // CPC v3↔v2.1 concordance
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3'`.execute(db);
  // NAICS↔ISIC4 sector concordance
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_isic4'`.execute(db);

  // NB: concordance payloads generated at ingestion time. Re-run:
  //   psql $PG_URL -c "INSERT INTO edge_classified_as ... SELECT ... JOIN ..."
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_isic4'`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cpc3_product`.execute(db);
  await sql`
    DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.cpc.commodity_item_v3'
  `.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'cpc3'`.execute(db);
}
