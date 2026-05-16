import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * UDF: route `did:web:maps.gftd.ai:wikivoyage` + `:wikivoyage:*` → 'wikivoyage'.
 * Seed: 3 Wikivoyage language frontier rows (en/de/fr — largest 3 langs).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
  await sql`
    CREATE FUNCTION maps_source_dispatch_kind(
      source_did varchar,
      label      varchar
    ) RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:gleif'       THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata'    THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata:%'  THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:%'           THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia'            THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia:%'          THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage'           THEN 'wikivoyage'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage:%'         THEN 'wikivoyage'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons'              THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons:%'            THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist'          THEN 'inaturalist'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist:%'        THEN 'inaturalist'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif'                 THEN 'gbif'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif:%'               THEN 'gbif'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite'            THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite:%'          THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic'              THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic:%'            THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:street_view'          THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:infrastructure'       THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:geocode'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:weather'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:gtfs'                 THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.gftd.ai'                      THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);

  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    ["did:web:maps.gftd.ai:wikivoyage",    "Spot", 30_000, 0.3, 168.0],  // en
    ["did:web:maps.gftd.ai:wikivoyage:de", "Spot", 15_000, 0.3, 168.0],
    ["did:web:maps.gftd.ai:wikivoyage:fr", "Spot", 10_000, 0.3, 168.0],
  ];
  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.gftd\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/${sourceSlug.replace(/[.:]/g, "-")}:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, ${label}, ${worldTotal}, ${priority},
        ${ttl}, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
}
