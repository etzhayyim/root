import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B (public market data + educational proposals;
// no PII, no execution). All sources are public delayed/EOD feeds.
//
// arbitrage cluster (arb.gftd.ai) — proposes cross-venue / cross-asset
// arbitrage signals across stocks, real estate, futures, commodities, FX,
// crypto. EDUCATIONAL ONLY — no broker bindings, no execution paths.
//
// 4 vertex + 1 edge + 1 MV. Worker-direct Hyperdrive write per ADR-0036.
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_arb_quote (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      asset_class     varchar NOT NULL,
      venue           varchar NOT NULL,
      symbol          varchar NOT NULL,
      ts              varchar NOT NULL,
      bid             double precision,
      ask             double precision,
      mid             double precision,
      currency        varchar,
      src_url         varchar,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_arb_proposal (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      proposal_id     varchar NOT NULL,
      asset_class     varchar NOT NULL,
      leg_a           varchar NOT NULL,
      leg_b           varchar NOT NULL,
      spread_bps      integer NOT NULL,
      edge_bps        integer NOT NULL,
      confidence      double precision,
      rationale       varchar,
      expires_at      varchar,
      executed        boolean NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_arb_score (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      proposal_id     varchar NOT NULL,
      score           double precision NOT NULL,
      risk_notes      varchar,
      llm_model       varchar,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_arb_publication (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      proposal_id     varchar NOT NULL,
      post_uri        varchar NOT NULL,
      mentions        varchar,
      disclaimer      varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_arb_proposal_leg (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      side            varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_arb_active_opps AS
      SELECT p.vertex_id,
             p.proposal_id,
             p.asset_class,
             p.leg_a,
             p.leg_b,
             p.spread_bps,
             p.edge_bps,
             p.confidence,
             p.expires_at,
             s.score,
             s.risk_notes
      FROM vertex_arb_proposal p
      LEFT JOIN vertex_arb_score s ON s.proposal_id = p.proposal_id
      WHERE p.executed = false
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_arb_active_opps`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_arb_proposal_leg`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arb_publication`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arb_score`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arb_proposal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arb_quote`.execute(db);
}
