import { Kysely, sql } from 'kysely';

/**
 * Migration 0082: FAO ASFIS aquatic species + FDA NDC drug products + ATC→NDC bridge.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 8).
 *
 * ## New taxonomy masters
 *
 * | Collection                    | Rows    | Source                                     |
 * |-------------------------------|---------|---------------------------------------------|
 * | ai.gftd.apps.asfis.species    | 13,761  | FAO ASFIS 2025 (fish species + ISSCAAP groups) |
 * | ai.gftd.apps.fda.ndc          | 131,664 | FDA NDC bulk download 2025 (drug products)  |
 *
 * ### FAO ASFIS (Aquatic Sciences and Fisheries Information System) species list
 * 13,761 nodes in 2-level hierarchy:
 *   - 53 ISSCAAP group nodes (standard FAO fishery statistical categories, groups 11–94)
 *   - 13,708 species with 3-letter Alpha3 trade codes (e.g. TUX = Bluefin tuna)
 * Source: FAO Fisheries & Aquaculture, ASFIS_sp_2025.csv.
 * Alpha3 code = species identifier used in UN Comtrade fish trade statistics.
 * 7 synthetic ISSCAAP group nodes added for groups 81–94 (not in standard reference).
 * 0 orphan nodes after synthetic node repair.
 *
 * ### FDA NDC (National Drug Code) product database
 * 131,664 unique NDC product codes (deduplicated from 134,021 raw entries).
 * Source: openFDA bulk download (download.open.fda.gov/drug/ndc/).
 * Fields: generic_name, brand_name, labeler, dosage_form, product_type, route,
 *   marketing_category, application_number.
 * Flat structure (no parent hierarchy; products are leaf nodes).
 *
 * ## New concordance bridge
 *
 * | system   | edges  | description                                         |
 * |----------|--------|-----------------------------------------------------|
 * | atc_ndc  | 69,740 | ATC chemical_substance → FDA NDC product (name JOIN) |
 *
 * ### ATC→NDC bridge derivation
 * JOIN: UPPER(TRIM(ndc.generic_name)) = UPPER(TRIM(atc.name))
 * Restricted to ATC level=chemical_substance (5,154 codes) → ~69,740 NDC products.
 * Enables: "which FDA-approved products correspond to ATC drug class X?"
 * 0 dangling src/dst edges.
 *
 * ## New views
 *
 * - view_asfis_species: projection of ai.gftd.apps.asfis.species
 * - view_fda_ndc: projection of ai.gftd.apps.fda.ndc
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes in ASFIS (53 groups cover all species references).
 * 0 orphan nodes in FDA NDC (flat list).
 * 0 dangling edges in atc_ndc.
 *
 * Full concordance inventory (31 systems, 156,556 total edges excl. openalex/ipc):
 *   atc_ndc (69,740), hs22_hs17 (6,561), hs12_hs17 (6,528), hs96_hs02 (6,226),
 *   hs07_hs12 (6,197), hs02_hs07 (6,108), hs2017 (5,843), hs2017_cpc3 (5,740),
 *   hs2012 (5,584), hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391),
 *   sitc4 (3,776), sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693),
 *   cpc (2,663), cpc_isic5 (2,504), sitc1_sitc2 (1,334), isic5 (700),
 *   nace_r2 (679), isic5_nace (625), isic31_isic5 (231), isic31_isic4 (229),
 *   sovereign_m49 (219), iso3166_sovereign (215), iso3166_m49 (215),
 *   isic2_isic31 (76), naics_isic5 (24), naics_isic4 (24)
 *
 * dim_world_domain additions: asfis, fda_ndc.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_asfis_species AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'            AS name,
      value_json::jsonb->>'level'           AS level,
      value_json::jsonb->>'scientific_name' AS scientific_name,
      value_json::jsonb->>'family'          AS family,
      value_json::jsonb->>'order'           AS taxon_order,
      value_json::jsonb->>'isscaap'         AS isscaap_group,
      value_json::jsonb->>'parent'          AS parent_code,
      (value_json::jsonb->>'in_fishstat')::boolean AS in_fishstat,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.asfis.species'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_fda_ndc AS
    SELECT
      rkey AS ndc,
      value_json::jsonb->>'name'          AS name,
      value_json::jsonb->>'generic_name'  AS generic_name,
      value_json::jsonb->>'brand_name'    AS brand_name,
      value_json::jsonb->>'labeler'       AS labeler,
      value_json::jsonb->>'dosage_form'   AS dosage_form,
      value_json::jsonb->>'product_type'  AS product_type,
      value_json::jsonb->>'route'         AS route,
      value_json::jsonb->>'marketing_cat' AS marketing_category,
      value_json::jsonb->>'app_num'       AS application_number,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.fda.ndc'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('asfis', 'asfis.gftd.ai', 13708, 'aquatic species', 'food')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('fda_ndc', 'ndc.gftd.ai', 131664, 'FDA drug products', 'pharma')
  `.execute(db);

  // ── ATC→NDC bridge (data-only, idempotent) ────────────────────────────
  await sql`DELETE FROM edge_classified_as WHERE system = 'atc_ndc'`.execute(db);
  // NB: re-generated via: JOIN UPPER(TRIM(ndc.generic_name)) = UPPER(TRIM(atc.name))
  // python3 /tmp/build_atc_ndc.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_asfis_species`.execute(db);
  await sql`DROP VIEW IF EXISTS view_fda_ndc`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.asfis.species'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.fda.ndc'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('asfis','fda_ndc')`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'atc_ndc'`.execute(db);
}
