import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * RisingWave SQL UDF — maps source dispatch resolver (ADR-0044 SQL UDF tier).
 *
 * Maps a (source_did, label) pair to the consumer-dispatch kind. The
 * `runCoverageJob` XRPC handler branches on the returned string; the
 * `runPendingCoverageJobs.bpmn` timer uses it to pre-filter pending jobs
 * so multi-instance fan-out skips rows it can't handle yet.
 *
 * Returns:
 *   'overpass'     — OSM Overpass QL (any infrastructure.* source, any Place/Road/Airport/...)
 *   'gleif'        — GLEIF Level 1 REST API (registry:gleif source + LegalEntity)
 *   'wikidata'     — Wikidata SPARQL (registry:wikidata source)
 *   'stac'         — STAC search (satellite source + SatelliteScene/TerrainPatch)
 *   'seismic'      — USGS earthquake feed
 *   'web_crawl'    — site.etzhayyim.com WET/WAT geo extraction (cross-actor)
 *   'unsupported'  — no consumer wired yet; runCoverageJob marks the job error
 *
 * Design: plan-time inlined CASE — no per-row language boundary. Used in
 * both the Worker (runCoverageJob dispatch) and the BPMN (where clause
 * on vertex_maps_job pending-job select) so both sides see the same
 * routing table without duplicating TS/XML logic.
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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'    THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata' THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'        THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'         THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'           THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'       THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'    THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'              THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                   THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
}
