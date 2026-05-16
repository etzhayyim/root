-- Malak dashboard counts: union of threat actor / wallet / risk signal / threat org counts.
MODEL (
  name dev.mv_malak_dashboard_counts,
  kind FULL,
  dialect postgres,
  description 'Per metric: count for malak dashboard (threatActors, walletAddresses, btcRiskSignals, threatOrgs).',
  grain [metric],
  tags [malak, dashboard, counts]
);

SELECT 'threatActors'::VARCHAR AS metric, COUNT(*)::BIGINT AS cnt
FROM vertex_threat
WHERE repo = 'did:web:malak.gftd.ai' AND label = 'ThreatActor'
UNION ALL
SELECT 'walletAddresses'::VARCHAR, COUNT(*)::BIGINT
FROM vertex_malak_wallet_address
UNION ALL
SELECT 'btcRiskSignals'::VARCHAR, COUNT(*)::BIGINT
FROM vertex_risk_signal
WHERE chain = 'btc'
UNION ALL
SELECT 'threatOrgs'::VARCHAR, COUNT(*)::BIGINT
FROM vertex_threat
WHERE repo = 'did:web:malak.gftd.ai' AND label = 'ThreatOrg'
