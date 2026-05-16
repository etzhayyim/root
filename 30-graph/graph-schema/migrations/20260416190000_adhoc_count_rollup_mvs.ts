import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Additional count rollup MVs for remaining ad hoc COUNT(*) queries identified
 * across the repo. Replaces per-request full-table scans with streaming MV reads.
 *
 * All single-row total MVs are safe: no GROUP BY, no MAX(varchar), backfill = 1 row.
 * view_page_count_by_domain is a plain VIEW (not MV) because domain cardinality in
 * vertex_page (985M rows) could exceed 500k distinct keys → MV OOM risk per CLAUDE.md.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_app total (repo.ts: com.atproto.sync.listHosts) ──────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_app_total_count AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_app
    WHERE did IS NOT NULL
  `.execute(db);

  // ── collector dashboard counts (collector app: cmdGetDashboard) ──────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_collector_dashboard_counts AS
    SELECT 'collectorRuns'::varchar AS metric, COUNT(*)::bigint AS cnt
    FROM vertex_collector_run
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'dnsObservations'::varchar, COUNT(*)::bigint
    FROM vertex_dns_observation
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'btcAddresses'::varchar, COUNT(*)::bigint
    FROM vertex_blockchain_actor
    WHERE chain = 'btc'

    UNION ALL

    SELECT 'ethAddresses'::varchar, COUNT(*)::bigint
    FROM vertex_blockchain_actor
    WHERE chain = 'eth'

    UNION ALL

    SELECT 'scanResults'::varchar, COUNT(*)::bigint
    FROM vertex_scan_result
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'archiveSnapshots'::varchar, COUNT(*)::bigint
    FROM vertex_blockchain_actor
    WHERE repo IS NOT NULL
  `.execute(db);

  // ── malak dashboard counts (malak app: cmdGetDashboard) ─────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_dashboard_counts AS
    SELECT 'threatActors'::varchar AS metric, COUNT(*)::bigint AS cnt
    FROM vertex_threat
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'btcRiskSignals'::varchar, COUNT(*)::bigint
    FROM vertex_risk_signal
    WHERE chain = 'btc'
  `.execute(db);

  // ── vertex_ip_address total (ipaddress app: cmdGetRirStats) ─────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_ip_address_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_ip_address
  `.execute(db);

  // ── vertex_page total (site app: cmdGetStats — CRITICAL: 985M rows) ─────────
  // Single COUNT(*) MV = 1 streaming counter row, safe even at 985M rows.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_page_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_page
  `.execute(db);

  // ── vertex_collection_job total (site app: cmdGetStats) ─────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_job_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_collection_job
  `.execute(db);

  // ── per-domain page count VIEW (site app: getDomainOverview + seedForProject)
  // Plain VIEW (not MV) — domain cardinality in vertex_page is unknown and may
  // exceed 500k distinct values. Plain VIEW avoids OOM; caller must cache.
  // Note: RisingWave does not support CREATE OR REPLACE VIEW — use DROP + CREATE.
  await sql`DROP VIEW IF EXISTS view_page_count_by_domain`.execute(db);
  await sql`
    CREATE VIEW view_page_count_by_domain AS
    SELECT domain, COUNT(*)::bigint AS cnt
    FROM vertex_page
    WHERE domain IS NOT NULL
    GROUP BY domain
  `.execute(db);

  // ── vertex_wet_chunk total (site app: cmdGetCrawlOutputStats) ───────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_wet_chunk_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_wet_chunk
  `.execute(db);

  // ── vertex_wat total (site app: cmdGetCrawlOutputStats) ─────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_wat_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_wat
  `.execute(db);

  // ── vertex_screenshot total (site app: cmdGetCrawlOutputStats) ──────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_screenshot_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_screenshot
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_site_screenshot_total`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_site_wat_total`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_site_wet_chunk_total`.execute(db);
  await sql`DROP VIEW IF EXISTS view_page_count_by_domain`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_site_job_total`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_site_page_total`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_ip_address_total`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_dashboard_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_collector_dashboard_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_app_total_count`.execute(db);
}
