DROP MATERIALIZED VIEW IF EXISTS mv_malak_dashboard_counts;

CREATE MATERIALIZED VIEW mv_malak_dashboard_counts AS
    SELECT 'threatActors'::varchar AS metric, COUNT(*)::bigint AS cnt
    FROM vertex_threat
    WHERE repo = 'did:web:malak.gftd.ai' AND label = 'ThreatActor'

    UNION ALL

    SELECT 'walletAddresses'::varchar, COUNT(*)::bigint
    FROM vertex_malak_wallet_address

    UNION ALL

    SELECT 'btcRiskSignals'::varchar, COUNT(*)::bigint
    FROM vertex_risk_signal
    WHERE chain = 'btc'

    UNION ALL

    SELECT 'threatOrgs'::varchar, COUNT(*)::bigint
    FROM vertex_threat
    WHERE repo = 'did:web:malak.gftd.ai' AND label = 'ThreatOrg';

FLUSH;
