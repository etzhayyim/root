DROP MATERIALIZED VIEW IF EXISTS mv_malak_dashboard_counts;

CREATE MATERIALIZED VIEW mv_malak_dashboard_counts AS
    SELECT 'threatActors'::varchar AS metric, COUNT(*)::bigint AS cnt
    FROM vertex_threat
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'btcRiskSignals'::varchar, COUNT(*)::bigint
    FROM vertex_risk_signal
    WHERE chain = 'btc';

FLUSH;
