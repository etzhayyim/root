// Extends mv_malak_dashboard_counts with walletAddresses + threatOrgs metrics
// now that vertex_malak_wallet_address exists (20260428150000).
//
// Requires DROP + CREATE because RisingWave does not support ALTER MATERIALIZED VIEW.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_dashboard_counts`.execute(db);
  await sql`
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
    WHERE repo = 'did:web:malak.gftd.ai' AND label = 'ThreatOrg'
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_dashboard_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_malak_dashboard_counts AS
    SELECT 'threatActors'::varchar AS metric, COUNT(*)::bigint AS cnt
    FROM vertex_threat
    WHERE repo IS NOT NULL

    UNION ALL

    SELECT 'btcRiskSignals'::varchar, COUNT(*)::bigint
    FROM vertex_risk_signal
    WHERE chain = 'btc'
  `.execute(db);
  await sql`FLUSH`.execute(db);
}
