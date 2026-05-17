import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * RisingWave SQL UDFs — DID normalization + safe division.
 *
 * Motivation: three MVs (mv_actor_repo_stats, mv_profile_page_stats,
 * mv_domain_coverage_live) repeat the same inline expressions 12+ times.
 * Extracting them to IMMUTABLE SQL UDFs:
 *   - eliminates copy-paste drift between migrations
 *   - lets RisingWave's optimizer inline and fold constants once
 *   - makes future MV changes a 1-line diff instead of 4-CTE cascade
 *
 * UDF inventory:
 *   did_web_root(varchar) → varchar
 *     Simple 3-segment root extraction: did:web:host:path → did:web:host
 *     Used by: mv_actor_repo_stats (0016 tree-oriented hierarchy)
 *
 *   normalize_actor_did(varchar) → varchar
 *     Full normalization with site.etzhayyim.com aliasing:
 *       did:web:site.etzhayyim.com:appname → did:web:appname.etzhayyim.com
 *       did:web:host:subpath         → did:web:host
 *       anything else                → unchanged
 *     Used by: mv_profile_page_stats (profile page counters)
 *
 *   safe_divide(double precision, double precision, double precision) → double precision
 *     Zero-safe division: numerator / denominator, returns fallback when denominator = 0.
 *     Used by: mv_domain_coverage_live (coverage / delta ratio columns)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── did_web_root ──────────────────────────────────────────────────────────
  // Extract the root DID from a hierarchical did:web path.
  // Equivalent to: split_part(v,':',1)||':'||split_part(v,':',2)||':'||split_part(v,':',3)
  // Non-did:web values are returned unchanged.
  await sql`DROP FUNCTION IF EXISTS did_web_root(varchar)`.execute(db);
  await sql`
    CREATE FUNCTION did_web_root(did varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN did LIKE 'did:web:%'
          THEN CONCAT(
            SPLIT_PART(did, ':', 1), ':',
            SPLIT_PART(did, ':', 2), ':',
            SPLIT_PART(did, ':', 3)
          )
        ELSE did
      END
    $$
  `.execute(db);

  // ── normalize_actor_did ───────────────────────────────────────────────────
  // Normalize a DID for profile aggregation.
  //
  // site.etzhayyim.com sub-DIDs use a reverse-alias convention:
  //   did:web:site.etzhayyim.com:foo → did:web:foo.etzhayyim.com
  // All other did:web paths are reduced to root host DID:
  //   did:web:foo.etzhayyim.com:bar → did:web:foo.etzhayyim.com
  // Non-did:web DIDs are passed through unchanged.
  await sql`DROP FUNCTION IF EXISTS normalize_actor_did(varchar)`.execute(db);
  await sql`
    CREATE FUNCTION normalize_actor_did(did varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN did LIKE 'did:web:site.etzhayyim.com:%'
          THEN CONCAT(
            'did:web:',
            SPLIT_PART(SPLIT_PART(did, 'did:web:site.etzhayyim.com:', 2), ':', 1),
            '.etzhayyim.com'
          )
        WHEN did LIKE 'did:web:%'
          THEN CONCAT(
            'did:web:',
            SPLIT_PART(SPLIT_PART(did, ':', 3), '/', 1)
          )
        ELSE did
      END
    $$
  `.execute(db);

  // ── safe_divide ───────────────────────────────────────────────────────────
  // Zero-safe floating-point division.
  // Returns fallback (default 0.0) when denominator is 0 or NULL.
  await sql`DROP FUNCTION IF EXISTS safe_divide(double precision, double precision, double precision)`.execute(db);
  await sql`
    CREATE FUNCTION safe_divide(
      numerator   double precision,
      denominator double precision,
      fallback    double precision
    )
    RETURNS double precision
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN denominator IS NOT NULL AND denominator > 0
          THEN numerator / denominator
        ELSE fallback
      END
    $$
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS safe_divide(double precision, double precision, double precision)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS normalize_actor_did(varchar)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS did_web_root(varchar)`.execute(db);
}
