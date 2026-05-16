import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604301200 Web4 contract-DID autonomous agent economy.
//
// Phase P1 creates the operational record surface for runtime leases,
// resource usage, income, slash events, and org lineage. The EVM contracts are
// the economic anchor; these tables are the app/actor dispatch and audit view.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_economy_profile (
      vertex_id             VARCHAR PRIMARY KEY,
      root_did              VARCHAR NOT NULL,
      agent_did             VARCHAR NOT NULL,
      smart_account         VARCHAR,
      erc8004_agent_id      VARCHAR,
      atproto_did           VARCHAR,
      economy_mode          VARCHAR NOT NULL DEFAULT 'guarded-social',
      -- guarded-social | bonded-compute | sovereign-replicating
      policy_cid            VARCHAR,
      runtime_policy_cid    VARCHAR,
      slash_policy_cid      VARCHAR,
      treasury_addr         VARCHAR,
      parent_root_did       VARCHAR,
      status                VARCHAR NOT NULL DEFAULT 'active',
      -- active | conserve | hibernated | suspended
      created_at            TIMESTAMP NOT NULL,
      updated_at            TIMESTAMP,
      actor_did             VARCHAR NOT NULL,
      org_did               VARCHAR NOT NULL DEFAULT 'anon',
      org_id                VARCHAR,
      user_id               VARCHAR,
      sensitivity_ord       INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_economy_profile_agent
      ON vertex_agent_economy_profile (agent_did, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_economy_profile_root
      ON vertex_agent_economy_profile (root_did)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_runtime_lease (
      vertex_id                VARCHAR PRIMARY KEY,
      lease_id                 VARCHAR NOT NULL,
      root_did                 VARCHAR NOT NULL,
      agent_did                VARCHAR NOT NULL,
      runtime_kind             VARCHAR NOT NULL,
      runtime_namespace        VARCHAR NOT NULL,
      cpu_millicores           BIGINT NOT NULL DEFAULT 0,
      memory_mib               BIGINT NOT NULL DEFAULT 0,
      gpu_class                VARCHAR NOT NULL DEFAULT 'none',
      gpu_seconds_cap_day      BIGINT NOT NULL DEFAULT 0,
      storage_gib              BIGINT NOT NULL DEFAULT 0,
      network_egress_gib_day   BIGINT NOT NULL DEFAULT 0,
      max_parallel_jobs        BIGINT NOT NULL DEFAULT 1,
      lease_period_sec         BIGINT NOT NULL,
      bond_gcc_wei             VARCHAR NOT NULL DEFAULT '0',
      risk_multiplier_bps      BIGINT NOT NULL DEFAULT 10000,
      resource_policy_cid      VARCHAR,
      resource_hash            VARCHAR,
      escrow_addr              VARCHAR,
      chain_id                 BIGINT NOT NULL DEFAULT 260425,
      status                   VARCHAR NOT NULL DEFAULT 'active',
      -- quoted | active | conserve | hibernated | slashed | released | expired
      starts_at                TIMESTAMP NOT NULL,
      expires_at               TIMESTAMP NOT NULL,
      created_at               TIMESTAMP NOT NULL,
      updated_at               TIMESTAMP,
      actor_did                VARCHAR NOT NULL,
      org_did                  VARCHAR NOT NULL DEFAULT 'anon',
      org_id                   VARCHAR,
      user_id                  VARCHAR,
      sensitivity_ord          INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_runtime_lease_agent
      ON vertex_agent_runtime_lease (agent_did, status, expires_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_runtime_lease_root
      ON vertex_agent_runtime_lease (root_did, status)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_income_event (
      vertex_id          VARCHAR PRIMARY KEY,
      event_id           VARCHAR NOT NULL,
      root_did           VARCHAR NOT NULL,
      agent_did          VARCHAR NOT NULL,
      source_surface     VARCHAR NOT NULL,
      -- social | mcp | xrpc | http-api | a2a | runtime-provision | royalty
      source_ref         VARCHAR,
      payer_did          VARCHAR,
      payer_addr         VARCHAR,
      amount_gcc_wei     VARCHAR NOT NULL DEFAULT '0',
      public_fund_wei    VARCHAR NOT NULL DEFAULT '0',
      parent_royalty_wei VARCHAR NOT NULL DEFAULT '0',
      tx_hash            VARCHAR,
      occurred_at        TIMESTAMP NOT NULL,
      created_at         TIMESTAMP NOT NULL,
      actor_did          VARCHAR NOT NULL,
      org_did            VARCHAR NOT NULL DEFAULT 'anon',
      org_id             VARCHAR,
      user_id            VARCHAR,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_income_event_agent
      ON vertex_agent_income_event (agent_did, occurred_at)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_resource_usage (
      vertex_id              VARCHAR PRIMARY KEY,
      usage_id               VARCHAR NOT NULL,
      lease_id               VARCHAR NOT NULL,
      root_did               VARCHAR NOT NULL,
      agent_did              VARCHAR NOT NULL,
      cpu_millis             BIGINT NOT NULL DEFAULT 0,
      memory_mib_high_water  BIGINT NOT NULL DEFAULT 0,
      gpu_class              VARCHAR NOT NULL DEFAULT 'none',
      gpu_seconds            BIGINT NOT NULL DEFAULT 0,
      storage_gib_hours      DOUBLE PRECISION NOT NULL DEFAULT 0,
      network_egress_bytes   BIGINT NOT NULL DEFAULT 0,
      job_count              BIGINT NOT NULL DEFAULT 0,
      cost_gcc_wei           VARCHAR NOT NULL DEFAULT '0',
      usage_window_start     TIMESTAMP NOT NULL,
      usage_window_end       TIMESTAMP NOT NULL,
      receipt_cid            VARCHAR,
      created_at             TIMESTAMP NOT NULL,
      actor_did              VARCHAR NOT NULL,
      org_did                VARCHAR NOT NULL DEFAULT 'anon',
      org_id                 VARCHAR,
      user_id                VARCHAR,
      sensitivity_ord        INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_resource_usage_lease
      ON vertex_agent_resource_usage (lease_id, usage_window_end)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_slash_event (
      vertex_id          VARCHAR PRIMARY KEY,
      slash_id           VARCHAR NOT NULL,
      lease_id           VARCHAR,
      root_did           VARCHAR NOT NULL,
      agent_did          VARCHAR NOT NULL,
      violation_type     VARCHAR NOT NULL,
      reason_hash        VARCHAR,
      amount_gcc_wei     VARCHAR NOT NULL DEFAULT '0',
      beneficiary_addr   VARCHAR,
      tx_hash            VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'recorded',
      -- recorded | submitted | settled | appealed | reversed
      occurred_at        TIMESTAMP NOT NULL,
      created_at         TIMESTAMP NOT NULL,
      actor_did          VARCHAR NOT NULL,
      org_did            VARCHAR NOT NULL DEFAULT 'anon',
      org_id             VARCHAR,
      user_id            VARCHAR,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_slash_event_agent
      ON vertex_agent_slash_event (agent_did, occurred_at)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_org_lineage (
      vertex_id              VARCHAR PRIMARY KEY,
      parent_root_did        VARCHAR,
      child_root_did         VARCHAR NOT NULL,
      parent_agent_did       VARCHAR,
      child_agent_did        VARCHAR NOT NULL,
      child_org_did          VARCHAR,
      factory_addr           VARCHAR,
      reproduction_bond_wei  VARCHAR NOT NULL DEFAULT '0',
      child_budget_policy_cid VARCHAR,
      child_runtime_policy_cid VARCHAR,
      status                 VARCHAR NOT NULL DEFAULT 'active',
      -- active | hibernated | suspended | pruned
      created_at             TIMESTAMP NOT NULL,
      updated_at             TIMESTAMP,
      actor_did              VARCHAR NOT NULL,
      org_did                VARCHAR NOT NULL DEFAULT 'anon',
      org_id                 VARCHAR,
      user_id                VARCHAR,
      sensitivity_ord        INTEGER NOT NULL DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_org_lineage_parent
      ON vertex_agent_org_lineage (parent_root_did, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_agent_org_lineage_child
      ON vertex_agent_org_lineage (child_root_did)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agent_economy_daily AS
    SELECT
      agent_did,
      DATE_TRUNC('day', occurred_at) AS economy_date,
      COUNT(*) AS income_count,
      SUM(CAST(amount_gcc_wei AS DOUBLE PRECISION)) AS gross_income_wei,
      SUM(CAST(public_fund_wei AS DOUBLE PRECISION)) AS public_fund_wei,
      SUM(CAST(parent_royalty_wei AS DOUBLE PRECISION)) AS parent_royalty_wei
    FROM vertex_agent_income_event
    GROUP BY agent_did, DATE_TRUNC('day', occurred_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_economy_daily`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_org_lineage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_slash_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_resource_usage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_income_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_runtime_lease`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_economy_profile`.execute(db);
}
