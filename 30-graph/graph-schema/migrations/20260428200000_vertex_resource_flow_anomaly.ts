import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 13 — resource-flow anomaly detection (ADR-0028 + ADR-0046).
// tier: A (public aggregate alert; no PII)
//
// Cron BPMN timer-start `R/PT24H` runs detectAnomaly which compares the
// current-period event_count for every (source × counterparty × period)
// triple against the rolling 30-day baseline computed from
// `mv_resource_flow_sankey_currency`. Triples where the observed count
// exceeds the baseline by `THRESHOLD` (default 3.0) get a row in
// `vertex_resource_flow_anomaly` and an `app.bsky.feed.post` to the
// `rf-anomaly` channel.
//
// We persist the alert row so downstream consumers (yoro / news /
// kaisya audit) can subscribe to anomalies via Follow without re-running
// the comparison. The schema mirrors the columns on
// `mv_resource_flow_sankey_currency` plus the threshold + observed
// metrics, so the alert is self-contained.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_resource_flow_anomaly (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      anomaly_id             varchar NOT NULL,
      flow_class             varchar NOT NULL,
      source_did             varchar NOT NULL,
      counterparty_did       varchar,
      fiscal_period          varchar NOT NULL,
      industry_code          varchar,
      currency               varchar,
      service_class          varchar,
      observed_value         double precision NOT NULL,
      baseline_avg           double precision NOT NULL,
      baseline_window_days   integer NOT NULL,
      baseline_sample_count  integer NOT NULL,
      threshold_factor       double precision NOT NULL,
      severity               varchar NOT NULL,
      observed_at            varchar NOT NULL,
      detection_run_id       varchar NOT NULL,
      post_uri               varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_run        ON vertex_resource_flow_anomaly (detection_run_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_source     ON vertex_resource_flow_anomaly (source_did, fiscal_period)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_severity   ON vertex_resource_flow_anomaly (severity, observed_at)`.execute(db);
  await sql`FLUSH`.execute(db);

  // mv_resource_flow_anomaly_recent — rolling 7-day pane keyed by
  // (severity, source). Bounded GROUP BY (severity × source × class),
  // safe per the §MV Memory Safety Guardrails.
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_anomaly_recent AS
      SELECT
        severity,
        flow_class,
        source_did,
        COUNT(*) AS anomaly_count
      FROM vertex_resource_flow_anomaly
      GROUP BY severity, flow_class, source_did
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_anomaly_recent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_resource_flow_anomaly_severity`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_resource_flow_anomaly_source`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_resource_flow_anomaly_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resource_flow_anomaly`.execute(db);
  await sql`FLUSH`.execute(db);
}
