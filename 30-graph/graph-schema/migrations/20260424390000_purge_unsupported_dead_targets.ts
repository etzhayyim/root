import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 64 — purge 11 unsupported 0-row coverage targets.
 *
 * Dispatch kinds routed by UDF but not implemented in Worker:
 *   - registry_other (openaddresses, osm, uk-ch, eu-br, jp-moj, jp-nta,
 *     us-edgar, opencorporates): no handler
 *   - gtfs: no handler (MLIT GTFS-JP bulk download doesn't fit bbox model)
 *   - mapillary: token-required, removed from dispatch iter 10
 *   - opensky: handler exists but 0 rows ever (ADS-B bbox tiles drift)
 *
 * These top the gap-ranked view (gap_score 4.8 / 2.4 / 1.4) because of
 * NULL last_fetched_at, forcing cmdAdvanceCoverage to waste SELECT
 * scans before the dispatchable IN-filter skips them. Removing them
 * reduces view cardinality 423 → 412 and should modestly speed up
 * advance-pick latency.
 *
 * If / when a handler gets wired up for any of these, re-seed with a
 * dedicated migration.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const deadSourceDids = [
    "did:web:maps.gftd.ai:registry:openaddresses",
    "did:web:maps.gftd.ai:registry:osm",
    "did:web:maps.gftd.ai:registry:uk-ch",
    "did:web:maps.gftd.ai:registry:eu-br",
    "did:web:maps.gftd.ai:registry:jp-moj",
    "did:web:maps.gftd.ai:registry:jp-nta",
    "did:web:maps.gftd.ai:registry:us-edgar",
    "did:web:maps.gftd.ai:registry:opencorporates",
    "did:web:maps.gftd.ai:gtfs",
    "did:web:maps.gftd.ai:street_view",
    "did:web:maps.gftd.ai:opensky",
  ];
  for (const sd of deadSourceDids) {
    await sql`DELETE FROM vertex_maps_coverage_target WHERE source_did = ${sd}`.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: re-seed via the original migration if needed.
}
