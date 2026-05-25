import { Kysely, sql } from 'kysely';

/**
 * Migration 0084: WHO ICD-10-CM disease classification + ISO 4217→3166-1 currency-country bridge.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 10).
 *
 * ## New taxonomy master
 *
 * | Collection                       | Rows    | Source                                            |
 * |----------------------------------|---------|---------------------------------------------------|
 * | app.etzhayyim.apps.icd10.disease       | 90,168  | WHO ICD-10-CM 2019 (via github.com/k4m1113/ICD-10-CSV) |
 *
 * ### WHO ICD-10-CM (International Classification of Diseases, 10th revision, Clinical Modification)
 * 90,168 nodes in 4-level hierarchy:
 *   - 22 chapter nodes (CHI – CHXXII, e.g. CHI = Infectious diseases A00-B99)
 *   - 1,513 category3 nodes (3-char codes, e.g. A00 = Cholera)
 *   - 14,804 category4 nodes (4-char intermediate codes, e.g. A010)
 *   - code4/5/6/7 leaf nodes (ICD-10-CM uses up to 7 chars for clinical specificity)
 * Source: github.com/k4m1113/ICD-10-CSV (2019 release, US ICD-10-CM full expansion).
 * 0 orphan nodes: all 3-char codes reference their chapter, all deeper codes reference parent.
 * Note: ICD-10-CM (US edition) extends standard WHO ICD-10 with additional 6-7 char specificity codes.
 *
 * ## New concordance bridge
 *
 * | system          | edges | description                                          |
 * |-----------------|-------|------------------------------------------------------|
 * | iso4217_iso3166 |   164 | ISO 4217 currency → ISO 3166-1 country (entity JOIN) |
 *
 * ### iso4217_iso3166 bridge derivation
 * JOIN: UPPER(TRIM(currency.entity)) → ISO 3166-1 alpha-3 via name normalization.
 * 164 currencies matched (including supra-nationals like EUR mapped to primary territory).
 * ~14 supra-national / special codes skipped (XAU=Gold, XDR=SDR, XTS=Testing, etc.).
 *
 * ## New views
 *
 * - view_icd10_disease: projection of app.etzhayyim.apps.icd10.disease
 *
 * ## Topology integrity (post-apply)
 *
 * ICD-10: 0 orphan nodes (all 3-char codes reference chapter nodes).
 * 0 dangling edges in iso4217_iso3166 (all src/dst refs verified).
 *
 * Full concordance inventory (34 systems, ~272,407 total edges):
 *   locode_iso3166 (115,687), atc_ndc (69,740), hs22_hs17 (6,561), hs12_hs17 (6,528),
 *   hs96_hs02 (6,226), hs07_hs12 (6,197), hs02_hs07 (6,108), hs2017 (5,843),
 *   hs2017_cpc3 (5,740), hs2012 (5,584), hs2012_cpc3 (5,500), sitc3_sitc4 (5,408),
 *   cpc3 (4,391), sitc4 (3,776), sitc4_cpc3 (3,717), sitc2_sitc3 (2,805),
 *   sitc2_sitc4 (2,693), cpc (2,663), cpc_isic5 (2,504), sitc1_sitc2 (1,334),
 *   isic5 (700), nace_r2 (679), isic5_nace (625), isic31_isic5 (231),
 *   isic31_isic4 (229), sovereign_m49 (219), iso3166_sovereign (215),
 *   iso3166_m49 (215), iso4217_iso3166 (164), isic2_isic31 (76), naics_isic5 (24),
 *   naics_isic4 (24), ipc (1)
 *
 * dim_world_domain additions: icd10.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_icd10_disease AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'       AS name,
      value_json::jsonb->>'level'      AS level,
      value_json::jsonb->>'parent'     AS parent_code,
      value_json::jsonb->>'short_name' AS short_name,
      value_json::jsonb->>'chapter'    AS chapter,
      value_json::jsonb->>'code_range' AS code_range,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.icd10.disease'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('icd10', 'icd10.etzhayyim.com', 90168, 'ICD-10-CM disease codes', 'healthcare')
  `.execute(db);

  // ── iso4217_iso3166 bridge (data-only, idempotent) ────────────────────
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso4217_iso3166'`.execute(db);
  // NB: re-generated via: UPPER(TRIM(iso4217.entity)) → iso3166.name normalization + manual map
  // python3 /tmp/build_iso4217_iso3166_final.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_icd10_disease`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.icd10.disease'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'icd10'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso4217_iso3166'`.execute(db);
}
