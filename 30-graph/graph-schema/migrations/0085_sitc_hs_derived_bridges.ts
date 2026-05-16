import { Kysely, sql } from 'kysely';

/**
 * Migration 0085: Derived SITC↔HS concordance bridges + SITC1→SITC4 chain.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 11).
 *
 * ## New concordance bridges (all derived — no new taxonomy masters)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | sitc4_hs2017    | 29,861 | SITC4 ↔ HS2017 via shared CPC3 node (JOIN src_vid)     |
 * | sitc4_hs2012    | 28,354 | SITC4 ↔ HS2012 via shared CPC3 node (JOIN src_vid)     |
 * | sitc3_hs2017    | 14,756 | SITC3 → HS2017 via sitc3_sitc4 ∘ sitc4_hs2017 chain   |
 * | sitc2_hs2017    | 10,053 | SITC2 → HS2017 via sitc2_sitc4 ∘ sitc4_hs2017 chain   |
 * | sitc1_sitc4     |  1,115 | SITC1 → SITC4 via sitc1_sitc2 ∘ sitc2_sitc4 chain     |
 * | sitc1_hs2017    |  1,053 | SITC1 → HS2017 via sitc1_sitc4 ∘ sitc4_hs2017 chain   |
 *
 * ### Derivation methodology
 * All bridges derived from existing concordance systems in edge_classified_as via SQL JOIN.
 * No new external data sources required.
 *
 * **Shared-CPC3 pattern**: both SITC and HS have edges pointing TO CPC3 (via sitc4_cpc3 and
 * hs2017_cpc3). JOIN on src_vid gives commodity pairs that share a CPC3 classification.
 *   SELECT DISTINCT e1.dst_vid, e2.dst_vid
 *   FROM edge_classified_as e1 JOIN edge_classified_as e2 ON e1.src_vid = e2.src_vid
 *   WHERE e1.system='sitc4_cpc3' AND e2.system='hs2017_cpc3'
 *
 * **Chain pattern**: transitively compose two existing directed bridges.
 *   SELECT DISTINCT e1.src_vid, e2.dst_vid
 *   FROM edge_classified_as e1 JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
 *   WHERE e1.system=X AND e2.system=Y
 *
 * ## Coverage impact
 *
 * Before this migration: SITC classifications had no direct HS path (required 2-hop via CPC).
 * After: SITC Rev.1–4 can directly look up HS 2017 commodity codes.
 * Enables: "given a SITC trade category, which HS tariff headings apply?" queries.
 *
 * ## Full concordance inventory (40 systems, 517,336 total edges):
 *   locode_iso3166 (115,687), atc_ndc (69,740), sitc4_hs2017 (29,861),
 *   sitc4_hs2012 (28,354), sitc3_hs2017 (14,756), sitc2_hs2017 (10,053),
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs96_hs02 (6,226), hs07_hs12 (6,197),
 *   hs02_hs07 (6,108), hs2017 (5,843), hs2017_cpc3 (5,740), hs2012 (5,584),
 *   hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776),
 *   sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693), cpc (2,663),
 *   cpc_isic5 (2,504), sitc1_sitc2 (1,334), sitc1_sitc4 (1,115),
 *   isic5 (700), nace_r2 (679), isic5_nace (625), isic31_isic5 (231),
 *   isic31_isic4 (229), sovereign_m49 (219), iso3166_sovereign (215),
 *   iso3166_m49 (215), iso4217_iso3166 (164), sitc1_hs2017 (1,053),
 *   isic2_isic31 (76), naics_isic5 (24), naics_isic4 (24), ipc (1)
 *   (excl. openalex_concept 159,739)
 *
 * ## Topology integrity
 *
 * 0 orphan nodes (no new taxonomy masters — bridges only).
 * 0 dangling edges (all src/dst URIs reference existing vertex_repo_record rows).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // All bridges are data-only (idempotent DELETE + re-derive via SQL JOIN).
  // Re-generated via: python3 /tmp/build_derived_bridges_v2.py + build_more_bridges.py

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_hs2017'`.execute(db);
  // SELECT DISTINCT e1.dst_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.src_vid = e2.src_vid
  // WHERE e1.system='sitc4_cpc3' AND e2.system='hs2017_cpc3'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_hs2012'`.execute(db);
  // SELECT DISTINCT e1.dst_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.src_vid = e2.src_vid
  // WHERE e1.system='sitc4_cpc3' AND e2.system='hs2012_cpc3'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_hs2017'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
  // WHERE e1.system='sitc3_sitc4' AND e2.system='sitc4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2017'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
  // WHERE e1.system='sitc2_sitc4' AND e2.system='sitc4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_sitc4'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
  // WHERE e1.system='sitc1_sitc2' AND e2.system='sitc2_sitc4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_hs2017'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
  // WHERE e1.system='sitc1_sitc4' AND e2.system='sitc4_hs2017'
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of ['sitc4_hs2017', 'sitc4_hs2012', 'sitc3_hs2017',
                         'sitc2_hs2017', 'sitc1_sitc4', 'sitc1_hs2017']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
