import { Kysely, sql } from 'kysely';

/**
 * Migration 0077: WHO ATC (Anatomical Therapeutic Chemical) classification.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 5 continued).
 *
 * ## New taxonomy master
 *
 * | Collection                  | Rows  | Source                                     |
 * |-----------------------------|-------|--------------------------------------------|
 * | app.etzhayyim.apps.atc.substance  | 6,440 | WHO ATC-DDD 2021-12-03 (github.com/fabkury) |
 *
 * ### WHO ATC Classification (Anatomical Therapeutic Chemical)
 * 6,440 unique codes across 5 levels:
 *   14 anatomical main groups / 94 therapeutic subgroups /
 *   269 pharmacological subgroups / 909 chemical subgroups /
 *   5,154 chemical substances
 *
 * Source: WHO Collaborating Centre for Drug Statistics Methodology (WHOCC).
 * ATC DDD 2021-12-03 edition. The ATC system is the global standard for
 * drug classification, used by OECD, WHO, IMS/IQVIA, national pharmacovigilance.
 *
 * Additional fields stored per code:
 * - ddd: Defined Daily Dose (numeric string)
 * - uom: unit of measurement (mg, g, ml, etc.)
 * - adm_r: route of administration (O=oral, P=parenteral, N=nasal, etc.)
 *
 * ### Hierarchy topology (0 orphans)
 * All parent references validated: each ATC code points to its prefix parent
 * (e.g. A01AA → A01A, A01AA01 → A01AA). 0 dangling references.
 *
 * ## New view
 *
 * - view_atc_substance: projection of app.etzhayyim.apps.atc.substance
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes in app.etzhayyim.apps.atc.substance.
 * No new concordance edges (ATC is a standalone hierarchy).
 * ATC→ICD-11 concordance is possible via drug→indication mapping (future work).
 *
 * dim_world_domain addition: atc.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── view ───────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_atc_substance AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      value_json::jsonb->>'ddd'    AS ddd,
      value_json::jsonb->>'uom'    AS uom,
      value_json::jsonb->>'adm_r'  AS adm_r,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.atc.substance'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('atc', 'atc.etzhayyim.com', 6440, 'drug substances', 'pharma')
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_atc_substance`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.atc.substance'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'atc'`.execute(db);
}
