import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:murakumo.etzhayyim.com";
const createdAt = "2026-05-07T06:31:00Z";
const nsid = "com.etzhayyim.apps.murakumo.fleetHealthCheck";
const bpmnProcessId = "murakumo_fleet_health_check";
const sourcePath = "00-contracts/bpmn/com/etzhayyim/murakumo/fleetHealthCheck.bpmn";
const processVid = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/murakumo-fleet-health-check-v1";
const bindingVid = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/murakumo-fleet-health-check-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_murakumo_fleet_health (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      epoch_ms BIGINT NOT NULL DEFAULT 0,
      health_pct INTEGER NOT NULL DEFAULT 0,
      nodes_healthy INTEGER NOT NULL DEFAULT 0,
      nodes_total INTEGER NOT NULL DEFAULT 0,
      litellm_reachable BOOLEAN NOT NULL DEFAULT false,
      litellm_latency_ms INTEGER NOT NULL DEFAULT 0,
      litellm_version VARCHAR,
      litellm_error TEXT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_murakumo_fleet_node_health (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      node_name VARCHAR NOT NULL,
      node_ip VARCHAR,
      healthy BOOLEAN NOT NULL DEFAULT false,
      model VARCHAR,
      snapshot_ts VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    )
  `.execute(db);

  const oldTable = await sql<{ exists: boolean }>`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = current_schema()
        AND table_name = 'vertex_murakumo_record'
    ) AS exists
  `.execute(db);

  if (oldTable.rows[0]?.exists) {
    await sql`
      INSERT INTO vertex_murakumo_fleet_health (
        vertex_id, record_key, status, value_json, indexed_at, created_at,
        updated_at, actor_did, org_did, owner_did, sensitivity_ord,
        epoch_ms, health_pct, nodes_healthy, nodes_total, litellm_reachable,
        litellm_latency_ms, litellm_version, litellm_error
      )
      SELECT
        vertex_id,
        record_key,
        CASE WHEN COALESCE((value_json::jsonb #>> '{litellm,reachable}')::boolean, false)
          THEN 'ok' ELSE 'degraded' END,
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer),
        COALESCE((value_json::jsonb ->> 'epoch')::bigint, 0),
        COALESCE((value_json::jsonb ->> 'healthPct')::integer, 0),
        COALESCE((value_json::jsonb ->> 'nodesHealthy')::integer, 0),
        COALESCE((value_json::jsonb ->> 'nodesTotal')::integer, 0),
        COALESCE((value_json::jsonb #>> '{litellm,reachable}')::boolean, false),
        COALESCE((value_json::jsonb #>> '{litellm,latencyMs}')::integer, 0),
        value_json::jsonb #>> '{litellm,version}',
        value_json::jsonb #>> '{litellm,error}'
      FROM vertex_murakumo_record
      WHERE record_kind = 'fleetHealth'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_health_status_time
      ON vertex_murakumo_fleet_health (status, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_health_reachable_time
      ON vertex_murakumo_fleet_health (litellm_reachable, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_node_health_node_time
      ON edge_murakumo_fleet_node_health (node_name, snapshot_ts DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_node_health_healthy
      ON edge_murakumo_fleet_node_health (healthy, snapshot_ts DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_murakumo_fleet_health_latest AS
    SELECT *
    FROM vertex_murakumo_fleet_health
    WHERE indexed_at = (SELECT MAX(indexed_at) FROM vertex_murakumo_fleet_health)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_murakumo_node_health_counts AS
    SELECT node_name, COUNT(*) AS sample_count, COUNT(*) FILTER (WHERE healthy) AS healthy_count, MAX(snapshot_ts) AS latest_snapshot_ts
    FROM edge_murakumo_fleet_node_health
    GROUP BY node_name
  `.execute(db);

  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, actor_did, org_did
    )
    SELECT
      ${processVid}, ${ownerDid}, ${bpmnProcessId}, 1, ${xml},
      CAST(${size} AS integer), ${sourcePath}, 'active', ${createdAt},
      100, ${ownerDid}, ${ownerDid}, 'sys.bpmn.seed.murakumo',
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, write_table_allowlist, status, created_at,
      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
    )
    VALUES (
      ${bindingVid}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      60000, 'vertex_murakumo_fleet_health,edge_murakumo_fleet_node_health',
      'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid},
      'sys.bpmn.seed.murakumo', ${ownerDid}, 'anon'
    )
    ON CONFLICT (vertex_id) DO UPDATE SET
      write_table_allowlist = EXCLUDED.write_table_allowlist,
      status = EXCLUDED.status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid}`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_murakumo_node_health_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_murakumo_fleet_health_latest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_murakumo_fleet_node_health`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_murakumo_fleet_health`.execute(db);
}
