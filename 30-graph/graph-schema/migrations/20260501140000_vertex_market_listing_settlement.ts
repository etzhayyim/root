import { Kysely, sql } from "kysely";

// ADR 2605011300 — capital flow market lane primary tables.
// tier: B
//
// Two vertex tables + one narrow MV. All Phase 1 lanes (vault/sashiosae/
// lawfirm/bpmn/murakumo) write via these. Mokuteki upper gate
// (ADR-2604291800) is enforced at handler-time; floor-failed rows still
// land here for audit but mokuteki_floor_pass=false marks them as
// excluded from supply-side counting in mv_market_vacuum_score.
//
// RisingWave constraints respected:
//   - DOUBLE PRECISION for monetary (no NUMERIC(p,s))
//   - VARCHAR JSON, no JSONB
//   - GROUP BY in MV is bounded (lane × signalKind × created_date) ~50 rows/day
//   - No streaming MAX(varchar) over high-cardinality keys
//   - No ON CONFLICT (PK implicit upsert, ADR-2604251220)

export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_market_listing — published offers (information surface S) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_market_listing (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      listing_id           VARCHAR NOT NULL,
      lane                 VARCHAR NOT NULL,
      issuer_did           VARCHAR NOT NULL,
      title                VARCHAR,
      description          VARCHAR,
      price_unit           DOUBLE PRECISION NOT NULL,
      settlement_currency  VARCHAR NOT NULL,
      min_quantity         DOUBLE PRECISION,
      max_quantity         DOUBLE PRECISION,
      terms_uri            VARCHAR,
      status               VARCHAR NOT NULL DEFAULT 'active',
      mokuteki_floor_pass  BOOLEAN NOT NULL DEFAULT TRUE,
      spirit_separation_delta DOUBLE PRECISION,
      published_at         VARCHAR NOT NULL,
      created_at           VARCHAR NOT NULL,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR,
      actor_did            VARCHAR,
      org_did              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_listing_lane_status
      ON vertex_market_listing (lane, status, published_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_listing_issuer
      ON vertex_market_listing (issuer_did, status)
  `.execute(db);

  // ── vertex_market_settlement — 5-tuple commercial event (amplitude²) ──
  // (issuer did:erc725, lxm, quantity, unit_price, settlement_tx_hash)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_market_settlement (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      invoice_id           VARCHAR NOT NULL,
      listing_id           VARCHAR NOT NULL,
      lane                 VARCHAR NOT NULL,
      issuer_did           VARCHAR NOT NULL,
      payer_did            VARCHAR NOT NULL,
      lxm                  VARCHAR NOT NULL,
      quantity             DOUBLE PRECISION NOT NULL,
      unit_price           DOUBLE PRECISION NOT NULL,
      total_price          DOUBLE PRECISION NOT NULL,
      settlement_currency  VARCHAR NOT NULL,
      settlement_tx_hash   VARCHAR,
      bundle_queue_id      VARCHAR,
      mokuteki_floor_pass  BOOLEAN NOT NULL DEFAULT TRUE,
      status               VARCHAR NOT NULL DEFAULT 'pending',
      memo                 VARCHAR,
      enqueued_at          VARCHAR NOT NULL,
      mined_at             VARCHAR,
      created_at           VARCHAR NOT NULL,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR,
      actor_did            VARCHAR,
      org_did              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_settlement_lane_status
      ON vertex_market_settlement (lane, status, enqueued_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_settlement_bundle
      ON vertex_market_settlement (bundle_queue_id, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_settlement_tx
      ON vertex_market_settlement (settlement_tx_hash)
  `.execute(db);

  // ── vertex_market_demand_signal — ∇φ source rows ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_market_demand_signal (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      signal_kind          VARCHAR NOT NULL,
      lane                 VARCHAR NOT NULL,
      demand_hash          VARCHAR,
      magnitude            DOUBLE PRECISION NOT NULL DEFAULT 1.0,
      observed_at          VARCHAR NOT NULL,
      created_at           VARCHAR NOT NULL,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR,
      actor_did            VARCHAR,
      org_did              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_market_demand_lane_kind_date
      ON vertex_market_demand_signal (lane, signal_kind, created_date)
  `.execute(db);

  // ── mv_market_vacuum_score — daily ∇φ aggregation ──
  // GROUP BY (lane × created_date) — bounded by ~5 lanes × ~365 days ≈ 1825 rows.
  // Safe for streaming MV (well below the 500K cardinality guardrail).
  // vacuum_score = demand_total − supply_settled (Mokuteki-passed only)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_market_vacuum_score AS
    SELECT
      d.lane                                      AS lane,
      d.created_date                              AS observed_date,
      COALESCE(SUM(d.magnitude), 0.0)             AS demand_total,
      COALESCE((
        SELECT SUM(s.total_price)
        FROM vertex_market_settlement s
        WHERE s.lane = d.lane
          AND s.created_date = d.created_date
          AND s.mokuteki_floor_pass = TRUE
          AND s.status = 'settled'
      ), 0.0)                                      AS supply_settled,
      COALESCE(SUM(d.magnitude), 0.0)
        - COALESCE((
          SELECT SUM(s.total_price)
          FROM vertex_market_settlement s
          WHERE s.lane = d.lane
            AND s.created_date = d.created_date
            AND s.mokuteki_floor_pass = TRUE
            AND s.status = 'settled'
        ), 0.0)                                    AS vacuum_score,
      COUNT(*)                                     AS demand_observation_count
    FROM vertex_market_demand_signal d
    GROUP BY d.lane, d.created_date
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_market_vacuum_score`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_demand_lane_kind_date`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_market_demand_signal`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_settlement_tx`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_settlement_bundle`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_settlement_lane_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_market_settlement`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_listing_issuer`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_market_listing_lane_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_market_listing`.execute(db);
}
