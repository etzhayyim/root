DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_personnel;

DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_service;

DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_currency;

FLUSH;

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_currency AS
      SELECT
        COALESCE(root_did, source_did)                                  AS source_did,
        COALESCE(counterparty_root_did, counterparty_did, 'independent') AS counterparty_did,
        source_did                                                       AS source_facade_did,
        COALESCE(counterparty_did, 'independent')                        AS counterparty_facade_did,
        fiscal_period,
        flow_type,
        currency,
        industry_code,
        amount_bucket,
        SUM(COALESCE(amount, 0))   AS amount_sum,
        COUNT(*)                   AS event_count
      FROM vertex_resource_flow_currency
      GROUP BY
        COALESCE(root_did, source_did),
        COALESCE(counterparty_root_did, counterparty_did, 'independent'),
        source_did,
        COALESCE(counterparty_did, 'independent'),
        fiscal_period, flow_type, currency, industry_code, amount_bucket;

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_service AS
      SELECT
        COALESCE(root_did, source_did)                                  AS source_did,
        COALESCE(counterparty_root_did, counterparty_did, 'independent') AS counterparty_did,
        source_did                                                       AS source_facade_did,
        COALESCE(counterparty_did, 'independent')                        AS counterparty_facade_did,
        fiscal_period,
        service_class,
        service_unit,
        industry_code,
        SUM(service_count)               AS total_count,
        SUM(COALESCE(revenue, 0))        AS revenue_sum,
        COUNT(*)                         AS event_count
      FROM vertex_resource_flow_service
      GROUP BY
        COALESCE(root_did, source_did),
        COALESCE(counterparty_root_did, counterparty_did, 'independent'),
        source_did,
        COALESCE(counterparty_did, 'independent'),
        fiscal_period, service_class, service_unit, industry_code;

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_personnel AS
      SELECT
        COALESCE(root_did, source_did)                                  AS source_did,
        COALESCE(counterparty_root_did, counterparty_did, 'independent') AS counterparty_did,
        source_did                                                       AS source_facade_did,
        COALESCE(counterparty_did, 'independent')                        AS counterparty_facade_did,
        fiscal_period,
        flow_type,
        industry_code,
        SUM(headcount_delta)  AS headcount_sum,
        COUNT(*)              AS event_count
      FROM vertex_resource_flow_personnel
      GROUP BY
        COALESCE(root_did, source_did),
        COALESCE(counterparty_root_did, counterparty_did, 'independent'),
        source_did,
        COALESCE(counterparty_did, 'independent'),
        fiscal_period, flow_type, industry_code;

FLUSH;
