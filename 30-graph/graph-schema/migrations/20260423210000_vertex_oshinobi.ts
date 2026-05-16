import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * oshinobi.gftd.ai — creator subscription platform schema (Phase 1).
 *
 * Principles:
 *   - AT Repo carries Tier 1 metadata (creator handle, tier name, post slug).
 *   - All monetary values are BIGINT USD cents (no NUMERIC(p,s), no float — RW + Lexicon constraint).
 *   - PII / raw card data NEVER stored (payment_token_ref + payout_provider_ref only).
 *   - body_cipher stores signal:v1:{ciphertext} when tier-gated (contentLabel != 'safe').
 *   - content_label ∈ {safe, suggestive, adult} drives entitlement + social dispatch.
 *   - vertex_id = AT URI convention (content-addressed for subscription/entitlement
 *     per ADR-0041 to prevent createRecord race).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // creator profile — one per creator DID
  await sql`
    CREATE TABLE vertex_oshinobi_creator (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      creator_did           varchar NOT NULL,
      display_name          varchar NOT NULL,
      bio                   varchar,
      content_policy        varchar NOT NULL,
      verified              boolean,
      age_verification_ref  varchar,
      age_verified_at       varchar,
      payout_provider_ref   varchar,
      payout_status         varchar NOT NULL,
      preferred_currency    varchar,
      suspended_at          varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_creator_did ON vertex_oshinobi_creator (creator_did)`.execute(db);

  // subscription tier — N per creator
  await sql`
    CREATE TABLE vertex_oshinobi_tier (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      creator_did        varchar NOT NULL,
      tier_id            varchar NOT NULL,
      name               varchar NOT NULL,
      description        varchar,
      price_usd_cents    bigint NOT NULL,
      billing_period     varchar NOT NULL,
      benefits_json      varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_tier_creator ON vertex_oshinobi_tier (creator_did, status)`.execute(db);

  // subscription — one per (subscriber, creator, tier)
  // vertex_id = content-addressed: "{subscriberDid}:{creatorDid}:{tierId}"
  await sql`
    CREATE TABLE vertex_oshinobi_subscription (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      subscription_id        varchar NOT NULL,
      subscriber_did         varchar NOT NULL,
      creator_did            varchar NOT NULL,
      tier_id                varchar NOT NULL,
      status                 varchar NOT NULL,
      period_start           varchar NOT NULL,
      period_end             varchar NOT NULL,
      auto_renew             boolean,
      payment_provider       varchar NOT NULL,
      payment_token_ref      varchar,
      last_charge_at         varchar,
      last_charge_cents      bigint,
      cancelled_at           varchar,
      cancel_reason          varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_sub_subscriber ON vertex_oshinobi_subscription (subscriber_did, status)`.execute(db);
  await sql`CREATE INDEX idx_oshinobi_sub_creator ON vertex_oshinobi_subscription (creator_did, status)`.execute(db);

  // post — N per creator. content_label + tier_required drive access.
  await sql`
    CREATE TABLE vertex_oshinobi_post (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      post_id            varchar NOT NULL,
      creator_did        varchar NOT NULL,
      tier_required      varchar,
      content_label      varchar NOT NULL,
      title              varchar,
      teaser             varchar,
      body_plain         varchar,
      body_cipher        varchar,
      media_cids_json    varchar,
      price_usd_cents    bigint,
      teaser_post_uri    varchar,
      published_at       varchar NOT NULL,
      takedown_at        varchar,
      takedown_reason    varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_post_creator ON vertex_oshinobi_post (creator_did, published_at)`.execute(db);
  await sql`CREATE INDEX idx_oshinobi_post_label ON vertex_oshinobi_post (content_label, published_at)`.execute(db);

  // entitlement — projection, one per (subscriber, post). Derived on publishPost
  // (for tier subscribers at that moment) and on subscribe (backfill).
  await sql`
    CREATE TABLE vertex_oshinobi_entitlement (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      subscriber_did   varchar NOT NULL,
      post_uri         varchar NOT NULL,
      creator_did      varchar NOT NULL,
      granted_via      varchar NOT NULL,
      granted_at       varchar NOT NULL,
      expires_at       varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_ent_sub ON vertex_oshinobi_entitlement (subscriber_did, post_uri)`.execute(db);

  // tip — one-off payment, optionally post-targeted. message is signal:v1 encrypted.
  await sql`
    CREATE TABLE vertex_oshinobi_tip (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint,
      created_date      date,
      sensitivity_ord   int,
      owner_did         varchar,
      tip_id            varchar NOT NULL,
      from_did          varchar NOT NULL,
      to_did            varchar NOT NULL,
      post_uri          varchar,
      amount_usd_cents  bigint NOT NULL,
      payment_provider  varchar NOT NULL,
      payment_token_ref varchar,
      status            varchar NOT NULL,
      message_cipher    varchar,
      captured_at       varchar,
      created_at        varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_tip_to ON vertex_oshinobi_tip (to_did, captured_at)`.execute(db);

  // payout ledger — monthly rollup per creator. BPMN writes delta rows; a future
  // batch closes the period and flips status to 'scheduled' / 'paid'.
  await sql`
    CREATE TABLE vertex_oshinobi_payout_ledger (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint,
      created_date      date,
      sensitivity_ord   int,
      owner_did         varchar,
      entry_id          varchar NOT NULL,
      creator_did       varchar NOT NULL,
      period            varchar NOT NULL,
      source_kind       varchar NOT NULL,
      source_uri        varchar,
      gross_cents       bigint NOT NULL,
      platform_fee_bps  int NOT NULL,
      net_cents         bigint NOT NULL,
      status            varchar NOT NULL,
      payout_ref        varchar,
      paid_at           varchar,
      created_at        varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_payout_creator ON vertex_oshinobi_payout_ledger (creator_did, period)`.execute(db);

  // user report — moderation queue source.
  await sql`
    CREATE TABLE vertex_oshinobi_report (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      report_id        varchar NOT NULL,
      reporter_did     varchar NOT NULL,
      target_uri       varchar NOT NULL,
      target_kind      varchar NOT NULL,
      category         varchar NOT NULL,
      reason           varchar,
      severity         varchar NOT NULL,
      status           varchar NOT NULL,
      triage_json      varchar,
      resolved_at      varchar,
      resolved_by_did  varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_report_target ON vertex_oshinobi_report (target_uri)`.execute(db);
  await sql`CREATE INDEX idx_oshinobi_report_severity ON vertex_oshinobi_report (severity, status)`.execute(db);

  // edges — GraphAr-native relationship projection.
  await sql`
    CREATE TABLE edge_oshinobi_subscribes_to (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      tier_id         varchar NOT NULL,
      status          varchar NOT NULL,
      period_end      varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_edge_sub_src ON edge_oshinobi_subscribes_to (src_vid, status)`.execute(db);
  await sql`CREATE INDEX idx_oshinobi_edge_sub_dst ON edge_oshinobi_subscribes_to (dst_vid, status)`.execute(db);

  await sql`
    CREATE TABLE edge_oshinobi_entitled_to (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      granted_via     varchar NOT NULL,
      expires_at      varchar,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_oshinobi_edge_ent_src ON edge_oshinobi_entitled_to (src_vid)`.execute(db);

  // Narrow streaming MV — active subscriptions per creator.
  // GROUP BY creator_did (bounded: ~creators count, low cardinality).
  // No MAX(varchar); COUNT + SUM only. Safe under MV memory guardrails.
  await sql`
    CREATE MATERIALIZED VIEW mv_oshinobi_active_subscriptions_by_creator AS
    SELECT
      creator_did,
      COUNT(*)                            AS active_subscriber_count,
      SUM(last_charge_cents)              AS last_period_gross_cents
    FROM vertex_oshinobi_subscription
    WHERE status = 'active'
    GROUP BY creator_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_oshinobi_active_subscriptions_by_creator`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshinobi_entitled_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_oshinobi_subscribes_to`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_report`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_payout_ledger`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_tip`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_entitlement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_post`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_tier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshinobi_creator`.execute(db);
}
