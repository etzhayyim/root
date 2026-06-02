"""Captured from Kysely migration 20260428160100_seed_resource_flow_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428160100_seed_resource_flow_bpmn"
down_revision = 'r_20260428160000_vertex_telecom_ntn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/resource-flow-register-emitter-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_register_emitter',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_resource_flow_register_emitter" '
                 'targetNamespace="https://etzhayyim.com/bpmn/resource-flow" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_register_emitter" name="registerEmitter" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Follow"/>\n'
                 '    <bpmn:serviceTask id="Task_Follow" name="follow emitter DID">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.graph.follow&quot;" '
                 'target="type"/>\n'
                 '          <zeebe:input source="={did: emitterDid}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_R</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_R" sourceRef="Task_Follow" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="record emitter registration">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <bpmn:documentation>Records the registration so the heartbeat job can '
                 'detect emitters\n'
                 '          that have stopped emitting (no commits in N days). vertex_profile\n'
                 '          is the canonical actor table — we only insert here if the emitter\n'
                 "          isn't already projected.</bpmn:documentation>\n"
                 '          <zeebe:input source="=&quot;vertex_profile&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: &quot;at://&quot; + emitterDid + '
                 '&quot;/app.bsky.actor.profile/self&quot;, sensitivity_ord: 1, owner_did: '
                 '&quot;did:web:resource-flow.etzhayyim.com&quot;, did: emitterDid, repo: emitterDid, '
                 'handle: emitterHandle, display_name: emitterDisplayName, description: '
                 'emitterDescription, collection: &quot;app.bsky.actor.profile&quot;, rkey: '
                 '&quot;self&quot;, created_at: createdAt}" target="row"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_R</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:resource-flow.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;resource-flow.emitter.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={emitterDid: emitterDid, industryCode: '
                 'industryCode}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3212,
                 '00-contracts/bpmn/com/etzhayyim/resource-flow/registerEmitter.bpmn',
                 '2026-04-28T16:01:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/resource-flow-register-emitter-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/resource-flow-registerEmitter-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'com.etzhayyim.apps.resourceFlow.registerEmitter',
                 'resource_flow_register_emitter',
                 30000,
                 '2026-04-28T16:01:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/resource-flow-registerEmitter-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/resource-flow-registerEmitter-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/resource-flow-register-emitter-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
