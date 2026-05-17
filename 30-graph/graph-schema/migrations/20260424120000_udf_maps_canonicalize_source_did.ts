import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * RisingWave SQL UDF — maps source DID canonicalization (ADR-0044 SQL tier).
 *
 * Observed during first auto-run (2026-04-24):
 *   mv_maps_collected_per_source_label surfaces ~3000+ rows under
 *   `did:web:uqpel6i6.etzhayyim.com:*` (nanoid hostname) and
 *   `did:web:uqpel6i6:*` (colon-less legacy form), while the coverage
 *   frontier seed uses the vanity hostname `did:web:maps.etzhayyim.com:*`.
 *   refreshCoverageStats can't match them → collected_count stays 0 even
 *   though the data is already in the graph.
 *
 * Fix: canonicalize both nanoid hostname variants onto the vanity hostname
 * before GROUP BY. Plan-time inlined, zero per-row cost (CASE + STRING).
 *
 *   'did:web:uqpel6i6.etzhayyim.com:infrastructure' → 'did:web:maps.etzhayyim.com:infrastructure'
 *   'did:web:uqpel6i6:infrastructure'         → 'did:web:maps.etzhayyim.com:infrastructure'
 *   'did:web:maps.etzhayyim.com:infrastructure'     → (unchanged)
 *   any other did                             → (unchanged)
 *
 * Also creates `mv_maps_collected_per_source_label_canonical` — same as
 * the raw MV but with canonical source_did, so refreshCoverageStats sees
 * every (source_did, label) pair under one key.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_canonicalize_source_did(varchar)`.execute(db);
  await sql`
    CREATE FUNCTION maps_canonicalize_source_did(source_did varchar)
      RETURNS varchar
      LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN source_did LIKE 'did:web:uqpel6i6.etzhayyim.com:%'
          THEN 'did:web:maps.etzhayyim.com' || SUBSTRING(source_did FROM 25)
        WHEN source_did LIKE 'did:web:uqpel6i6:%'
          THEN 'did:web:maps.etzhayyim.com' || SUBSTRING(source_did FROM 17)
        WHEN source_did = 'did:web:uqpel6i6.etzhayyim.com'
          THEN 'did:web:maps.etzhayyim.com'
        WHEN source_did = 'did:web:uqpel6i6'
          THEN 'did:web:maps.etzhayyim.com'
        ELSE source_did
      END
    $$
  `.execute(db);

  // Canonical MV — same shape as mv_maps_collected_per_source_label but
  // GROUP BY canonical source_did, so refreshCoverageStats matches both
  // hostname variants under one frontier row.
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label_canonical`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_maps_collected_per_source_label_canonical AS
    SELECT
      maps_canonicalize_source_did(source_did) AS source_did,
      label,
      COUNT(*)::bigint AS collected_count
    FROM vertex_spatial
    WHERE source_did IS NOT NULL AND label IS NOT NULL
    GROUP BY maps_canonicalize_source_did(source_did), label
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label_canonical`.execute(db);
  await sql`DROP FUNCTION IF EXISTS maps_canonicalize_source_did(varchar)`.execute(db);
}
