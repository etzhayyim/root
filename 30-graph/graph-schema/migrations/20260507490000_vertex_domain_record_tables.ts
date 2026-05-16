import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: C

async function createDomainRecordTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_kind VARCHAR,
      record_key VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
      indexed_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createDomainRecordTable(db, "vertex_handotai_record");
  await createDomainRecordTable(db, "vertex_organizer_record");
  await createDomainRecordTable(db, "vertex_kenkyusha_record");
  await createDomainRecordTable(db, "vertex_os_record");
  await createDomainRecordTable(db, "vertex_gov_record");
  await createDomainRecordTable(db, "vertex_projector_record");
  await createDomainRecordTable(db, "vertex_wellbecoming_record");
  await createDomainRecordTable(db, "vertex_magatama_record");
  await createDomainRecordTable(db, "vertex_murakumo_record");

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pds_domain_coverage_expansion (
      vertex_id VARCHAR PRIMARY KEY,
      tick_id VARCHAR,
      ok BOOLEAN,
      http_status BIGINT,
      domain VARCHAR,
      app_did VARCHAR,
      knowledge_edges BIGINT,
      post_written BOOLEAN,
      error TEXT,
      value_json TEXT,
      observed_at VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pds_operation_tick (
      vertex_id VARCHAR PRIMARY KEY,
      tick_id VARCHAR,
      operation_kind VARCHAR,
      ok BOOLEAN,
      http_status BIGINT,
      metric_primary BIGINT,
      metric_secondary BIGINT,
      error TEXT,
      value_json TEXT,
      observed_at VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_graph_consume_tick (
      vertex_id VARCHAR PRIMARY KEY,
      tick_id VARCHAR,
      ok BOOLEAN,
      http_status BIGINT,
      processed BIGINT,
      last_seq BIGINT,
      error TEXT,
      value_json TEXT,
      observed_at VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_agent (
      vertex_id VARCHAR PRIMARY KEY,
      agent_id VARCHAR,
      did VARCHAR,
      app_id VARCHAR,
      name VARCHAR,
      status VARCHAR,
      config_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_agent_event (
      vertex_id VARCHAR PRIMARY KEY,
      agent_id VARCHAR,
      event VARCHAR,
      target VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_os_agent_event (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      agent_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_consent_request (
      vertex_id VARCHAR PRIMARY KEY,
      request_id VARCHAR,
      agent_did VARCHAR,
      action VARCHAR,
      risk_tier VARCHAR,
      estimated_cost DOUBLE PRECISION,
      context_json TEXT,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_consent_response (
      vertex_id VARCHAR PRIMARY KEY,
      request_id VARCHAR,
      verdict VARCHAR,
      reason TEXT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_os_consent_response (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      request_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_budget_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      agent_id VARCHAR,
      amount DOUBLE PRECISION,
      expires_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_os_budget_agent (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      agent_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_directory_entry (
      vertex_id VARCHAR PRIMARY KEY,
      did VARCHAR,
      name VARCHAR,
      tags_json TEXT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_sync_event (
      vertex_id VARCHAR PRIMARY KEY,
      direction VARCHAR,
      path TEXT,
      data_size BIGINT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_os_window_event (
      vertex_id VARCHAR PRIMARY KEY,
      window_id VARCHAR,
      event VARCHAR,
      app_id VARCHAR,
      title VARCHAR,
      content_type VARCHAR,
      content_url TEXT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_os_agent_state AS
    SELECT a.agent_id, a.did, a.app_id, a.name, a.status AS state, a.created_at, COALESCE(e.latest_event_at, a.updated_at) AS updated_at
    FROM vertex_os_agent a
    LEFT JOIN (
      SELECT agent_id, MAX(created_at) AS latest_event_at
      FROM vertex_os_agent_event
      GROUP BY agent_id
    ) e ON a.agent_id = e.agent_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_os_consent_pending AS
    SELECT r.*
    FROM vertex_os_consent_request r
    LEFT JOIN vertex_os_consent_response s ON r.request_id = s.request_id
    WHERE r.status = 'pending' AND s.request_id IS NULL
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_os_budget_balance AS
    SELECT agent_id, SUM(amount) AS balance
    FROM vertex_os_budget_allocation
    GROUP BY agent_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_os_window_state AS
    SELECT window_id, MAX(created_at) AS updated_at
    FROM vertex_os_window_event
    GROUP BY window_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_os_window_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_os_budget_balance`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_os_consent_pending`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_os_agent_state`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_window_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_sync_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_directory_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_os_budget_agent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_budget_allocation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_os_consent_response`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_consent_response`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_consent_request`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_os_agent_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_agent_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_agent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_graph_consume_tick`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pds_operation_tick`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pds_domain_coverage_expansion`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_murakumo_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_magatama_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wellbecoming_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_os_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_organizer_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_record`.execute(db);
}
