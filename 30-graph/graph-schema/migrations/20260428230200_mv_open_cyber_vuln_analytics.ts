import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Streaming MVs for cyber vulnerability analytics cluster.
 *
 * All 4 source tables start with 0 rows (populated after Gap-1 seed activates
 * BPMN dispatch via migration 20260428230100). Cardinality pre-check:
 *   mv_open_cyber_vuln_cve_severity:        severity_tier(4) × vendor(N)  — safe
 *   mv_open_kev_remediation_lag:            maturity(~8) × category(~30)  — safe
 *   mv_open_cyber_soc_alert_daily:          severity(4) × triage_tier(4)  — 16 max
 *   mv_open_cyber_threat_actor_capability:  attribution(~6) × tier(5)     — 30 max
 *
 * Applied inline (not out-of-band) because tables are empty at creation time.
 * ADR-2604241342 out-of-band path applies only when kysely migrator is blocked
 * by existing corruption — not the case here.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // CVSS severity bucket × vendor distribution
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_vuln_cve_severity AS
    SELECT
      severity_tier,
      vendor,
      COUNT(*) AS cve_count,
      MAX(created_at) AS last_cve_at
    FROM vertex_open_cyber_vuln_cve
    WHERE status = 'published'
    GROUP BY severity_tier, vendor
  `.execute(db);

  // CISA KEV — active entries grouped by exploitation maturity × product category
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_kev_remediation_lag AS
    SELECT
      exploitation_maturity,
      product_category,
      COUNT(*) AS entry_count,
      MAX(added_at) AS latest_added_at
    FROM vertex_open_kev_catalog
    WHERE status = 'active'
    GROUP BY exploitation_maturity, product_category
  `.execute(db);

  // SOC alert volume — severity × triage disposition
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_soc_alert_daily AS
    SELECT
      severity,
      triage_tier,
      COUNT(*) AS alert_count,
      MAX(fired_at) AS latest_fired_at
    FROM vertex_open_cyber_soc_alert
    WHERE status = 'triaged'
    GROUP BY severity, triage_tier
  `.execute(db);

  // Threat actor inventory — attribution × capability tier × suspected nexus
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_threat_actor_capability AS
    SELECT
      attribution,
      capability_tier,
      suspected_nexus,
      COUNT(*) AS actor_count,
      MAX(first_observed) AS latest_observed
    FROM vertex_open_cyber_threat_actor
    WHERE status = 'tracked'
    GROUP BY attribution, capability_tier, suspected_nexus
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_cyber_threat_actor_capability`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_cyber_soc_alert_daily`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_kev_remediation_lag`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_cyber_vuln_cve_severity`.execute(db);
}
