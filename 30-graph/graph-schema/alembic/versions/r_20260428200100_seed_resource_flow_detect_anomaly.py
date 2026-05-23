"""Captured from Kysely migration 20260428200100_seed_resource_flow_detect_anomaly."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428200100_seed_resource_flow_detect_anomaly"
down_revision = 'r_20260428200000_vertex_telecom_optical'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-detect-anomaly-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_detect_anomaly',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  resource-flow.detectAnomaly — timer-started anomaly cron (ADR-0028 + '
                 'ADR-0046).\n'
                 '\n'
                 '  Daily R/PT24H sweep of mv_resource_flow_sankey_{currency,service,personnel}.\n'
                 '  Actual comparison + anomaly write + social emission runs in pyzeebe task\n'
                 '  resource-flow.detect.anomaly (pymagatama/primitives/resource_flow.py).\n'
                 '  CF Worker XRPC endpoint is a thin dispatcher stub only.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.resourceFlow.detectAnomaly\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-detect-anomaly-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_resource_flow_detect_anomaly"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/resource-flow"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="resource_flow_detect_anomaly" name="resource-flow '
                 'detectAnomaly" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.resourceFlow.detectAnomaly", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="daily">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_24h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Detect"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Detect" name="scan + flag + alert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="resource-flow.detect.anomaly"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;all&quot;"  target="flowClass"/>\n'
                 '          <zeebe:input source="=30"    target="windowDays"/>\n'
                 '          <zeebe:input source="=3.0"   target="thresholdFactor"/>\n'
                 '          <zeebe:input source="=3"     target="minBaselineSamples"/>\n'
                 '          <zeebe:input source="=true"  target="post"/>\n'
                 '          <zeebe:output source="=runId"   target="runId"/>\n'
                 '          <zeebe:output source="=scanned" target="scanned"/>\n'
                 '          <zeebe:output source="=flagged" target="flagged"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_S</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Detect" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:resource-flow.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;resource-flow.anomaly.scan&quot;"     '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, scanned: scanned, flagged: '
                 'flagged}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_A</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" '
                 'name="done"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3330,
                 '00-contracts/bpmn/ai/gftd/resource-flow/detectAnomaly.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-anomaly',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-detect-anomaly-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-detectAnomaly-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'ai.gftd.apps.resourceFlow.detectAnomaly',
                 'resource_flow_detect_anomaly',
                 60000,
                 '2026-04-28T20:01:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-anomaly',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-detectAnomaly-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-detectAnomaly-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-detect-anomaly-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
