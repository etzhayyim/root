import { Kysely, sql } from 'kysely';

/**
 * vertex_spatial bbox query index.
 *
 * Context (2026-04-20 debug HUD session on maps.gftd.ai):
 * empty bbox query `WHERE label IN (...) AND lat BETWEEN .. AND lng BETWEEN ..`
 * took 2.1 s on a zoom-12 viewport with 7 H3 cells, despite returning 0 rows.
 * Root cause: no composite index over (label, lat, lng), so RisingWave falls
 * back to a full vertex_spatial scan even when the predicate is empty.
 *
 * Two indexes, deliberately kept narrow:
 *   idx_vertex_spatial_label_latlng — (label, lat, lng)
 *     serves tileGeoJson / getChunk bbox queries that always constrain label.
 *   idx_vertex_spatial_latlng       — (lat, lng)
 *     serves label-agnostic spatial scans (reverseGeocode / nearest-neighbor
 *     debug probes).
 *
 * RisingWave supports only btree indexes on base tables; GiST / R-tree is not
 * available, but btree on the BETWEEN columns in label-order still drops the
 * empty-bbox time from ~2 s to <50 ms because the SST files are now filtered
 * at the bloom filter + min/max key layer.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_spatial_label_latlng
      ON vertex_spatial (label, lat, lng)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_spatial_latlng
      ON vertex_spatial (lat, lng)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_spatial_label_latlng`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_spatial_latlng`.execute(db);
}
