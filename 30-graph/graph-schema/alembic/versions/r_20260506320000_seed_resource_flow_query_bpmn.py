"""Captured from Kysely migration 20260506320000_seed_resource_flow_query_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506320000_seed_resource_flow_query_bpmn"
down_revision = 'r_20260506310000_seed_yadoya_catalog_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-sankey-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_get_sankey',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_resource_flow_get_sankey" '
                 'targetNamespace="https://etzhayyim.com/bpmn/resource-flow" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_get_sankey" name="resource-flow getSankey" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="query sankey edges">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="resource-flow.get.sankey"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=flowClass" target="flowClass"/>\n'
                 '          <zeebe:output source="=edges" target="edges"/>\n'
                 '          <zeebe:output source="=nodes" target="nodes"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=message" target="message"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Query" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1410,
                 '00-contracts/bpmn/ai/gftd/resource-flow/getSankey.bpmn',
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-sankey-v1']},
 {'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-actor-labels-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_get_actor_labels',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_resource_flow_get_actor_labels" '
                 'targetNamespace="https://etzhayyim.com/bpmn/resource-flow" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_get_actor_labels" name="resource-flow '
                 'getActorLabels" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="resolve actor labels">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="resource-flow.get.actor-labels"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=labels" target="labels"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=message" target="message"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Query" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1315,
                 '00-contracts/bpmn/ai/gftd/resource-flow/getActorLabels.bpmn',
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-actor-labels-v1']},
 {'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-flows-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_list_flows',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_resource_flow_list_flows" '
                 'targetNamespace="https://etzhayyim.com/bpmn/resource-flow" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_list_flows" name="resource-flow listFlows" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="list projected flows">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="resource-flow.list.flows"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=flowClass" target="flowClass"/>\n'
                 '          <zeebe:output source="=flows" target="flows"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '          <zeebe:output source="=offset" target="offset"/>\n'
                 '          <zeebe:output source="=limit" target="limit"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=message" target="message"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Query" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1528,
                 '00-contracts/bpmn/ai/gftd/resource-flow/listFlows.bpmn',
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-flows-v1']},
 {'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-anomalies-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_list_anomalies',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_resource_flow_list_anomalies" '
                 'targetNamespace="https://etzhayyim.com/bpmn/resource-flow" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_list_anomalies" name="resource-flow '
                 'listAnomalies" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="list anomalies">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="resource-flow.list.anomalies"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=anomalies" target="anomalies"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '          <zeebe:output source="=offset" target="offset"/>\n'
                 '          <zeebe:output source="=limit" target="limit"/>\n'
                 '          <zeebe:output source="=reviewed" target="reviewed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Query" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1426,
                 '00-contracts/bpmn/ai/gftd/resource-flow/listAnomalies.bpmn',
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-anomalies-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getSankey-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'ai.gftd.apps.resourceFlow.getSankey',
                 'resource_flow_get_sankey',
                 30000,
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getSankey-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getActorLabels-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'ai.gftd.apps.resourceFlow.getActorLabels',
                 'resource_flow_get_actor_labels',
                 30000,
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getActorLabels-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listFlows-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'ai.gftd.apps.resourceFlow.listFlows',
                 'resource_flow_list_flows',
                 30000,
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listFlows-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listAnomalies-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'ai.gftd.apps.resourceFlow.listAnomalies',
                 'resource_flow_list_anomalies',
                 30000,
                 '2026-05-06T23:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-query',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listAnomalies-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getSankey-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-getActorLabels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listFlows-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/resource-flow-listAnomalies-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-sankey-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-get-actor-labels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-flows-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/resource-flow-list-anomalies-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
