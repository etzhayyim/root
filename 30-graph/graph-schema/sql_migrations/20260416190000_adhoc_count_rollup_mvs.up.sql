CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_app_total_count AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_app
    WHERE did IS NOT NULL;

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
    WHERE repo IS NOT NULL;


CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_ip_address_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_ip_address;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_page_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_page;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_job_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_collection_job;

DROP VIEW IF EXISTS view_page_count_by_domain;

CREATE VIEW view_page_count_by_domain AS
    SELECT domain, COUNT(*)::bigint AS cnt
    FROM vertex_page
    WHERE domain IS NOT NULL
    GROUP BY domain;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_wet_chunk_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_wet_chunk;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_wat_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_wat;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_site_screenshot_total AS
    SELECT COUNT(*)::bigint AS cnt
    FROM vertex_screenshot;
