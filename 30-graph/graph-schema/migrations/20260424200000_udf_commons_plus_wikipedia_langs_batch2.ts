import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * UDF: route `did:web:maps.etzhayyim.com:commons` → 'commons'.
 * Seed: 1 Commons frontier + 13 more Wikipedia languages (ko/id/vi/tr/pl/
 * nl/sv/fi/no/da/cs/hu/el).
 *
 * Wikipedia total geotagged (cumulative with prior langs):
 *   en 7M + ja 1.5M + es 1.8M + de 1.5M + fr 1.2M + it 700K + zh 800K +
 *   ru 900K + ar 300K + pt 600K + ko 600K + id 700K + vi 1.3M + tr 500K +
 *   pl 1.5M + nl 2M + sv 2.5M + fi 550K + no 600K + da 300K + cs 500K +
 *   hu 500K + el 220K
 *   ≈ 26M unique geotagged articles across 23 languages.
 *
 * Commons: ~11M geotagged media files.
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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'       THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata'    THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata:%'  THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'           THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia'            THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia:%'          THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons'              THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons:%'            THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'            THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite:%'          THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'              THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic:%'            THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'          THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'       THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'                 THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                      THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);

  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // Commons
    ["did:web:maps.etzhayyim.com:commons", "Spot", 11_000_000, 0.6, 168.0],
    // 13 more Wikipedia languages
    ["did:web:maps.etzhayyim.com:wikipedia:ko", "Spot",   600_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:id", "Spot",   700_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:vi", "Spot", 1_300_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:tr", "Spot",   500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:pl", "Spot", 1_500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:nl", "Spot", 2_000_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:sv", "Spot", 2_500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:fi", "Spot",   550_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:no", "Spot",   600_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:da", "Spot",   300_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:cs", "Spot",   500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:hu", "Spot",   500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:el", "Spot",   220_000, 0.6, 168.0],
  ];
  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.etzhayyim\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/${sourceSlug.replace(/[.:]/g, "-")}:${label}`;
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
