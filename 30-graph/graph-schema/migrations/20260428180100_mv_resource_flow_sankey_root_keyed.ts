import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0074 — rebuild the 3 cluster-wide sankey MVs so the canonical
// aggregation key is `root_did` (ERC725) when populated, falling back
// to `source_did` / `counterparty_did` (facade) only while migration is
// in progress. This satisfies the 2026-04-27 operational correction:
// "RisingWave ERC725 projections and vector search keys must use the
// canonical ERC725 root DID/hash."
//
// We keep the facade fields in the projection so the AppView can still
// render legible labels via a JOIN to vertex_profile / vertex_erc725_root_identity.
// The MV continues to live in `mv_resource_flow_sankey_*` (DROP+CREATE).

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_personnel`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_service`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_currency`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
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
        fiscal_period, flow_type, currency, industry_code, amount_bucket
  `.execute(db);

  await sql`
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
        fiscal_period, service_class, service_unit, industry_code
  `.execute(db);

  await sql`
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
        fiscal_period, flow_type, industry_code
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_personnel`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_service`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_currency`.execute(db);
  // Restore the facade-only MVs from 20260428160000_vertex_resource_flow_cluster.
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_sankey_currency AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period, flow_type, currency, industry_code, amount_bucket,
        SUM(COALESCE(amount, 0)) AS amount_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_currency
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, flow_type, currency, industry_code, amount_bucket
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_sankey_service AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period, service_class, service_unit, industry_code,
        SUM(service_count) AS total_count,
        SUM(COALESCE(revenue, 0)) AS revenue_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_service
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, service_class, service_unit, industry_code
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_sankey_personnel AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period, flow_type, industry_code,
        SUM(headcount_delta) AS headcount_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_personnel
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, flow_type, industry_code
  `.execute(db);
  await sql`FLUSH`.execute(db);
}
