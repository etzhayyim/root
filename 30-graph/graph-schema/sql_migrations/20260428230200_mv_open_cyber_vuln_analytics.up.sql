CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_vuln_cve_severity AS
    SELECT
      severity_tier,
      vendor,
      COUNT(*) AS cve_count,
      MAX(created_at) AS last_cve_at
    FROM vertex_open_cyber_vuln_cve
    WHERE status = 'published'
    GROUP BY severity_tier, vendor;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_kev_remediation_lag AS
    SELECT
      exploitation_maturity,
      product_category,
      COUNT(*) AS entry_count,
      MAX(added_at) AS latest_added_at
    FROM vertex_open_kev_catalog
    WHERE status = 'active'
    GROUP BY exploitation_maturity, product_category;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_soc_alert_daily AS
    SELECT
      severity,
      triage_tier,
      COUNT(*) AS alert_count,
      MAX(fired_at) AS latest_fired_at
    FROM vertex_open_cyber_soc_alert
    WHERE status = 'triaged'
    GROUP BY severity, triage_tier;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_cyber_threat_actor_capability AS
    SELECT
      attribution,
      capability_tier,
      suspected_nexus,
      COUNT(*) AS actor_count,
      MAX(first_observed) AS latest_observed
    FROM vertex_open_cyber_threat_actor
    WHERE status = 'tracked'
    GROUP BY attribution, capability_tier, suspected_nexus;
