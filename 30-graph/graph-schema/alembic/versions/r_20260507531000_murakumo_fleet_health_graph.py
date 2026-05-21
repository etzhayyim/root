"""Captured from Kysely migration 20260507531000_murakumo_fleet_health_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507531000_murakumo_fleet_health_graph"
down_revision = 'r_20260507530000_seed_myco_yeast_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_murakumo_fleet_health (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR NOT NULL,\n'
         '      status VARCHAR NOT NULL,\n'
         '      value_json TEXT NOT NULL,\n'
         '      indexed_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2,\n'
         '      epoch_ms BIGINT NOT NULL DEFAULT 0,\n'
         '      health_pct INTEGER NOT NULL DEFAULT 0,\n'
         '      nodes_healthy INTEGER NOT NULL DEFAULT 0,\n'
         '      nodes_total INTEGER NOT NULL DEFAULT 0,\n'
         '      litellm_reachable BOOLEAN NOT NULL DEFAULT false,\n'
         '      litellm_latency_ms INTEGER NOT NULL DEFAULT 0,\n'
         '      litellm_version VARCHAR,\n'
         '      litellm_error TEXT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_murakumo_fleet_node_health (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      from_vertex_id VARCHAR NOT NULL,\n'
         '      to_vertex_id VARCHAR NOT NULL,\n'
         '      node_name VARCHAR NOT NULL,\n'
         '      node_ip VARCHAR,\n'
         '      healthy BOOLEAN NOT NULL DEFAULT false,\n'
         '      model VARCHAR,\n'
         '      snapshot_ts VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    SELECT EXISTS (\n'
         '      SELECT 1 FROM information_schema.tables\n'
         '      WHERE table_schema = current_schema()\n'
         "        AND table_name = 'vertex_murakumo_record'\n"
         '    ) AS exists\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_health_status_time\n'
         '      ON vertex_murakumo_fleet_health (status, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_health_reachable_time\n'
         '      ON vertex_murakumo_fleet_health (litellm_reachable, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_node_health_node_time\n'
         '      ON edge_murakumo_fleet_node_health (node_name, snapshot_ts DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_murakumo_fleet_node_health_healthy\n'
         '      ON edge_murakumo_fleet_node_health (healthy, snapshot_ts DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_murakumo_fleet_health_latest AS\n'
         '    SELECT *\n'
         '    FROM vertex_murakumo_fleet_health\n'
         '    WHERE indexed_at = (SELECT MAX(indexed_at) FROM vertex_murakumo_fleet_health)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_murakumo_node_health_counts AS\n'
         '    SELECT node_name, COUNT(*) AS sample_count, COUNT(*) FILTER (WHERE healthy) AS '
         'healthy_count, MAX(snapshot_ts) AS latest_snapshot_ts\n'
         '    FROM edge_murakumo_fleet_node_health\n'
         '    GROUP BY node_name\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1, $4,\n'
         "      CAST($5 AS integer), $6, 'active', $7,\n"
         "      100, $8, $9, 'sys.bpmn.seed.murakumo',\n"
         "      $10, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/murakumo-fleet-health-check-v1',
                 'did:web:murakumo.etzhayyim.com',
                 'murakumo_fleet_health_check',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  murakumo.fleetHealthCheck — scheduled LiteLLM/Mac Mini fleet sampler.\n'
                 '\n'
                 '  CF Worker remains the OpenAI-compatible request gateway. This BPMN process\n'
                 '  moves the periodic health sampling loop to Zeebe/PyZeebe so K8s owns cron,\n'
                 '  retry, and worker lifecycle.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.murakumo.fleetHealthCheck\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_murakumo_fleet_health_check"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/murakumo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="murakumo_fleet_health_check" name="murakumo '
                 'fleetHealthCheck" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.murakumo.fleetHealthCheck", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 5m">\n'
                 '      <bpmn:outgoing>Flow_ToCheck</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_5m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCheck" sourceRef="Start" '
                 'targetRef="Task_Check"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Check" name="sample fleet health">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="murakumo.fleet.healthCheck"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if litellmUrl = null then &quot;&quot; else '
                 'string(litellmUrl)" target="litellmUrl"/>\n'
                 '          <zeebe:input source="=false" target="flush"/>\n'
                 '          <zeebe:output source="=uri" target="fleetHealthUri"/>\n'
                 '          <zeebe:output source="=healthPct" target="healthPct"/>\n'
                 '          <zeebe:output source="=nodesHealthy" target="nodesHealthy"/>\n'
                 '          <zeebe:output source="=nodesTotal" target="nodesTotal"/>\n'
                 '          <zeebe:output source="=litellmReachable" target="litellmReachable"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCheck</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Check" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2448,
                 '00-contracts/bpmn/ai/gftd/murakumo/fleetHealthCheck.bpmn',
                 '2026-05-07T06:31:00Z',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/murakumo-fleet-health-check-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    VALUES (\n'
         '      $1, $2, $3, $4, 1,\n'
         "      60000, 'vertex_murakumo_fleet_health,edge_murakumo_fleet_node_health',\n"
         "      'active', $5, 100, $6, $7,\n"
         "      'sys.bpmn.seed.murakumo', $8, 'anon'\n"
         '    )\n'
         '    ON CONFLICT (vertex_id) DO UPDATE SET\n'
         '      write_table_allowlist = EXCLUDED.write_table_allowlist,\n'
         '      status = EXCLUDED.status\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/murakumo-fleet-health-check-v1',
                 'did:web:murakumo.etzhayyim.com',
                 'ai.gftd.apps.murakumo.fleetHealthCheck',
                 'murakumo_fleet_health_check',
                 '2026-05-07T06:31:00Z',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/murakumo-fleet-health-check-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/murakumo-fleet-health-check-v1']},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_murakumo_node_health_counts', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_murakumo_fleet_health_latest', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_murakumo_fleet_node_health', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_murakumo_fleet_health', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
