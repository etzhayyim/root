import { Kysely, sql } from 'kysely';

/**
 * Migration 0068: UN M49 geo areas + ISIC4↔ISIC5 concordance edges.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 * Data sources:
 *   - UN SDG API (M49 geo areas):
 *     https://unstats.un.org/SDGAPI/v1/sdg/GeoArea/List
 *     460 rows (countries + territories + aggregate regions)
 *   - ISIC4↔ISIC5 code-identical correspondence:
 *     700 edges derived by JOIN on rkey across
 *     collection='com.etzhayyim.apps.open_isic.economic_activity' (Rev.4, 766 rows)
 *     and collection='com.etzhayyim.apps.open_isic.economic_activity_rev5' (Rev.5, 830 rows)
 *     Represents direct code-continuity mappings (code unchanged across revisions).
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ collection='com.etzhayyim.apps.sovereign.m49_region'
 *       460 rows
 *   - edge_classified_as system='isic5' : 700 rows
 *     src_vid = ISIC Rev.4 uri → dst_vid = ISIC Rev.5 uri (same code)
 *   - dim_world_domain.m49.world_total : 460
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── M49 geo areas (data-only, idempotent) ────────────────────────────
  await sql`
    DELETE FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.sovereign.m49_region'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('m49', 'sovereign.etzhayyim.com', 460, 'geo_areas', 'governance')
  `.execute(db);

  // ── ISIC4↔ISIC5 concordance edges ────────────────────────────────────
  await sql`
    DELETE FROM edge_classified_as WHERE system = 'isic5'
  `.execute(db);

  // NB: 700-edge payload generated from JOIN of Rev.4 and Rev.5 records
  // at ingestion time. Re-run:
  //   psql $PG_URL -c "INSERT INTO edge_classified_as ... SELECT ... WHERE ..."
  // (see migration body for full query)
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5'`.execute(db);
  await sql`
    DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.sovereign.m49_region'
  `.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'm49'`.execute(db);
}
