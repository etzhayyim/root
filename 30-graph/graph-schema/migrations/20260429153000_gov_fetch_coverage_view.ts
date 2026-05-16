import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Canonical read model for government website fetch coverage.
 *
 * Counts are kept in SQL so dashboards and scripts share the same definition.
 * Percentages remain in callers to avoid DB-specific numeric rounding behavior.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE VIEW IF NOT EXISTS view_gov_fetch_coverage AS
    SELECT
      domain_code,
      COUNT(*)::INT AS total,
      COUNT(*) FILTER (WHERE COALESCE(website, '') <> '')::INT AS with_website,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
      )::INT AS fetch_checked,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
          AND (
            COALESCE(last_content_hash, '') <> ''
            OR COALESCE(last_fetch_status, '') IN ('direct_ok', 'proxy_ok', 'wet_chunk')
          )
      )::INT AS reachable,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND (
            COALESCE(last_content_hash, '') <> ''
            OR COALESCE(last_fetch_status, '') IN ('direct_ok', 'proxy_ok', 'wet_chunk')
          )
      )::INT AS hashable,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_content_hash, '') <> ''
      )::INT AS hashed,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
          AND COALESCE(last_content_hash, '') = ''
          AND COALESCE(last_fetch_status, '') NOT IN ('direct_ok', 'proxy_ok', 'wet_chunk')
      )::INT AS unreachable
    FROM vertex_gov_org
    GROUP BY domain_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_gov_fetch_coverage`.execute(db);
}
