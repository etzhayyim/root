"""Captured from Kysely migration 20260425165000_seed_kouza_bpmn_actor."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425165000_seed_kouza_bpmn_actor"
down_revision = 'r_20260425163000_vertex_atrecord_kouza'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/kouza-sync-due-connections-v1',
                 'did:web:kouza.etzhayyim.com',
                 'kouza_sync_due_connections',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  kouza resident sync scheduler.\n'
                 '\n'
                 '  Zeebe owns the cadence. Python owns the due-connection scan and sync_run\n'
                 '  audit write. This intentionally does not claim external bank/provider sync\n'
                 '  success; provider adapters can later replace the placeholder status while\n'
                 '  preserving the same resident process boundary.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_kouza_sync_due_connections"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kouza"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="kouza_sync_due_connections" name="kouza sync due '
                 'connections" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every 30min">\n'
                 '      <bpmn:outgoing>Flow_1</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_30m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_SyncDue"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SyncDue" name="scan and mark due kouza '
                 'connections">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ai.gftd.kouza.syncDueConnections"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if maxConnections = null then 25 else '
                 'maxConnections" target="maxConnections"/>\n'
                 '          <zeebe:input source="=if staleMinutes = null then 60 else '
                 'staleMinutes" target="staleMinutes"/>\n'
                 '          <zeebe:input source="=if ownerDid = null then &quot;&quot; else '
                 'ownerDid" target="ownerDid"/>\n'
                 '          <zeebe:input source="=if dryRun = null then false else dryRun" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok" target="kouzaSyncOk"/>\n'
                 '          <zeebe:output source="=connectionsScanned" '
                 'target="kouzaConnectionsScanned"/>\n'
                 '          <zeebe:output source="=syncRunsCreated" '
                 'target="kouzaSyncRunsCreated"/>\n'
                 '          <zeebe:output source="=syncRunDids" target="kouzaSyncRunDids"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_SyncDue" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit kouza resident sync">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kouza.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kouza.syncDueConnections&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={connectionsScanned: kouzaConnectionsScanned, '
                 'syncRunsCreated: kouzaSyncRunsCreated}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3253,
                 '00-contracts/bpmn/ai/gftd/kouza/syncDueConnections.bpmn',
                 '2026-04-25T16:50:00Z',
                 'did:web:kouza.etzhayyim.com',
                 'did:web:kouza.etzhayyim.com',
                 'sys.bpmn.seed.kouza',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/kouza-sync-due-connections-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/kouza-syncDueConnections-v1',
                 'did:web:kouza.etzhayyim.com',
                 'ai.gftd.apps.kouza.syncDueConnections',
                 'kouza_sync_due_connections',
                 120000,
                 '2026-04-25T16:50:00Z',
                 'did:web:kouza.etzhayyim.com',
                 'did:web:kouza.etzhayyim.com',
                 'sys.bpmn.seed.kouza',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/kouza-syncDueConnections-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/kouza-syncDueConnections-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/kouza-sync-due-connections-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
