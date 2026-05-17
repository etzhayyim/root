import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (yadoya hotel = public catalog; reservation has Tier-3 PII fields:
// guest_summary_signal_v1 = signal:v1: envelope ciphertext, amount_jpy raw is
// caller-side only — graph stores amount_bucket, not raw value).
//
// yadoya Phase 1 — hotel catalog + reservation lifecycle (ADR-0036
// Worker-direct Hyperdrive write). Bridges to hospitality cluster
// (ADR-0028) via edge_yadoya_property_to_chain → vertex_profile of
// did:web:hospitality.etzhayyim.com:actor:chain:* and :actor:property:*.
//
// 4 tables + 2 edges + 1 MV. No external dependencies on PDS commit
// stream — domain rows are inserted by yadoya Worker via Hyperdrive
// directly per ADR-0036.
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_yadoya_hotel (
      vertex_id           varchar PRIMARY KEY,
      _seq                bigint,
      created_date        date,
      sensitivity_ord     int,
      owner_did           varchar,
      hotel_slug          varchar NOT NULL,
      osm_id              varchar,
      chain_did           varchar,
      property_did        varchar,
      name                varchar NOT NULL,
      country             varchar NOT NULL,
      region              varchar,
      city                varchar,
      lat                 double precision,
      lon                 double precision,
      isic_code           varchar NOT NULL,
      price_jpy_min       integer,
      price_jpy_max       integer,
      capacity_rooms      integer,
      lang_codes          varchar,
      source_url          varchar,
      status              varchar NOT NULL,
      created_at          varchar,
      org_id              varchar,
      user_id             varchar,
      actor_id            varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_yadoya_reservation (
      vertex_id                 varchar PRIMARY KEY,
      _seq                      bigint,
      created_date              date,
      sensitivity_ord           int,
      owner_did                 varchar,
      reservation_id            varchar NOT NULL,
      hotel_vid                 varchar NOT NULL,
      guest_did                 varchar NOT NULL,
      guest_summary_signal_v1   varchar,
      checkin                   varchar NOT NULL,
      checkout                  varchar NOT NULL,
      guests                    integer NOT NULL,
      nights                    integer,
      amount_bucket             varchar,
      currency                  varchar,
      channel                   varchar NOT NULL,
      status                    varchar NOT NULL,
      cancelled_at              varchar,
      cancel_reason             varchar,
      created_at                varchar,
      org_id                    varchar,
      user_id                   varchar,
      actor_id                  varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_yadoya_property_to_chain (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE edge_yadoya_reservation_for_hotel (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_yadoya_catalog_coverage AS
      SELECT country, region, isic_code, status,
             COUNT(*) AS hotel_count
      FROM vertex_yadoya_hotel
      GROUP BY country, region, isic_code, status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yadoya_catalog_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yadoya_reservation_for_hotel`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yadoya_property_to_chain`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yadoya_reservation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yadoya_hotel`.execute(db);
}
