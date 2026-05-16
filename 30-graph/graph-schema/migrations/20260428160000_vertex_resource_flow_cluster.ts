import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 10 — cluster-wide resource-flow projection (ADR-0028).
//
// resource-flow.gftd.ai consumes the firehose for the 3 private-sector
// flow NSIDs and materializes them into 3 vertex tables + 3 sankey-ready
// MVs. Tables are intentionally cluster-wide (not yadoya-specific) so
// future emitters (mangaka revenue, ohsi service, kaisya personnel etc.)
// land in the same store with no schema fanout.
//
// PII invariants (ADR-0018): cohort_id may be NULL (single-event
// emission); when set, cohort_size >= 5 is enforced at write time by the
// Worker. Tables therefore allow NULL cohort_id but reject inserts with
// cohort_size < 5 via the consumer (we do not put a CHECK constraint
// because RisingWave does not support CHECK; the contract is enforced
// upstream).

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_resource_flow_currency (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      flow_type          varchar NOT NULL,
      amount             double precision,
      amount_bucket      varchar,
      currency           varchar NOT NULL,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_resource_flow_service (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      service_class      varchar NOT NULL,
      service_count      integer NOT NULL,
      service_unit       varchar NOT NULL,
      revenue            double precision,
      revenue_currency   varchar,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_resource_flow_personnel (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      flow_type          varchar NOT NULL,
      headcount_delta    integer NOT NULL,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  // Sankey-ready aggregations: (source × counterparty × period × bucket / class).
  // Independent counterparties bucket as 'independent' so the visualization
  // root has a single legible node.
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_sankey_currency AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        flow_type,
        currency,
        industry_code,
        amount_bucket,
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
        fiscal_period,
        service_class,
        service_unit,
        industry_code,
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
        fiscal_period,
        flow_type,
        industry_code,
        SUM(headcount_delta) AS headcount_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_personnel
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, flow_type, industry_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_personnel`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_service`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_sankey_currency`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resource_flow_personnel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resource_flow_service`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resource_flow_currency`.execute(db);
}
