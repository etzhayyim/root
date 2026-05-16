"""Captured from Kysely migration 20260424132100_seed_open_network_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424132100_seed_open_network_bpmn_actors"
down_revision = 'r_20260424132000_vertex_open_network'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-define-link-v1',
                 'did:web:open-network.gftd.ai:core',
                 'open_network_define_link',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_network_define_link"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-network"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_network_define_link" name="リンク 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveLink"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveLink" name="link 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_network_link&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              operator_org_id:  operatorOrgId,\n'
                 '              from_vertex_id:   fromVertexId,\n'
                 '              to_vertex_id:     toVertexId,\n'
                 '              capacity_mbps:    capacityMbps,\n'
                 '              media:            media,\n'
                 '              installed_at:     installedAt,\n'
                 '              status:           &quot;active&quot;,\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           operatorOrgId,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-network&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_EF</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EF" sourceRef="Task_SaveLink" '
                 'targetRef="Task_EdgeFrom"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeFrom" name="endpoint edge (from)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_network_link_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:from&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   fromVertexId,\n'
                 '              role:      &quot;from&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    operatorOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-network&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_EF</bpmn:incoming><bpmn:outgoing>Flow_ET</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ET" sourceRef="Task_EdgeFrom" '
                 'targetRef="Task_EdgeTo"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeTo" name="endpoint edge (to)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_network_link_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:to&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   toVertexId,\n'
                 '              role:      &quot;to&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    operatorOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-network&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_ET</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_EdgeTo" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit link.define">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-network.gftd.ai:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNetwork.link.define&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, operatorOrgId: '
                 'operatorOrgId, capacityMbps: capacityMbps, media: media, fromVertexId: '
                 'fromVertexId, toVertexId: toVertexId}" target="payload"/>\n'
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
                 5053,
                 '00-contracts/bpmn/ai/gftd/open-network/defineLink.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-network.gftd.ai:core',
                 'did:web:open-network.gftd.ai:core',
                 'sys.bpmn.seed.open-network',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-define-link-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-request-change-v1',
                 'did:web:open-network.gftd.ai:core',
                 'open_network_request_change',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_network_request_change"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-network"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_network_request_change" name="変更申請" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_ClassifyRisk"/>\n'
                 '\n'
                 '    <!--\n'
                 '      risk:\n'
                 '        high   = changeType in {emergency-patch, retire} OR affectedCustomers >= '
                 '1000\n'
                 '        medium = 100..999\n'
                 '        low    = < 100\n'
                 '      requireCabApproval = risk = "high"\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_ClassifyRisk" name="risk 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if list '
                 'contains([&quot;emergency-patch&quot;,&quot;retire&quot;], changeType) or '
                 'affectedCustomers &gt;= 1000 then &quot;high&quot;\n'
                 '                                else if affectedCustomers &gt;= 100 then '
                 '&quot;medium&quot;\n'
                 '                                else &quot;low&quot;" target="risk"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;emergency-patch&quot;,&quot;retire&quot;], changeType) or '
                 'affectedCustomers &gt;= 1000" target="requireCabApproval"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_ClassifyRisk" '
                 'targetRef="Task_SaveChange"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveChange" name="change 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_network_change&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:             vertexId,\n'
                 '              operator_org_id:       operatorOrgId,\n'
                 '              target_vertex_id:      targetVertexId,\n'
                 '              change_type:           changeType,\n'
                 '              narrative:             narrative,\n'
                 '              affected_customers:    affectedCustomers,\n'
                 '              risk:                  risk,\n'
                 '              require_cab_approval:  requireCabApproval,\n'
                 '              status:                &quot;requested&quot;,\n'
                 '              requested_at:          requestedAt,\n'
                 '              created_at:            string(now()),\n'
                 '              owner_did:             callerDid,\n'
                 '              sensitivity_ord:       1,\n'
                 '              org_id:                operatorOrgId,\n'
                 '              user_id:               callerDid,\n'
                 '              actor_id:              &quot;sys.bpmn.open-network&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_SaveChange" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" name="CAB必要?" default="Flow_AutoApprove">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Cab</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_AutoApprove</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Cab" sourceRef="Gate" '
                 'targetRef="Task_CabAudit">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requireCabApproval = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_AutoApprove" sourceRef="Gate" '
                 'targetRef="Task_AutoAudit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_CabAudit" name="audit change.cab.request">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-network.gftd.ai:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNetwork.change.cabRequest&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, risk: risk, changeType: '
                 'changeType, affectedCustomers: affectedCustomers}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Cab</bpmn:incoming><bpmn:outgoing>Flow_EndC</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndC" sourceRef="Task_CabAudit" '
                 'targetRef="End_C"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AutoAudit" name="audit change.autoApprove">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-network.gftd.ai:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNetwork.change.autoApprove&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, risk: risk, changeType: '
                 'changeType}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_AutoApprove</bpmn:incoming><bpmn:outgoing>Flow_EndA</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndA" sourceRef="Task_AutoAudit" '
                 'targetRef="End_A"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_A"><bpmn:incoming>Flow_EndA</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_C"><bpmn:incoming>Flow_EndC</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5753,
                 '00-contracts/bpmn/ai/gftd/open-network/requestChange.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-network.gftd.ai:core',
                 'did:web:open-network.gftd.ai:core',
                 'sys.bpmn.seed.open-network',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-request-change-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-defineLink-v1',
                 'did:web:open-network.gftd.ai:core',
                 'ai.gftd.apps.openNetwork.defineLink',
                 'open_network_define_link',
                 15000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-network.gftd.ai:core',
                 'did:web:open-network.gftd.ai:core',
                 'sys.bpmn.seed.open-network',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-defineLink-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-requestChange-v1',
                 'did:web:open-network.gftd.ai:core',
                 'ai.gftd.apps.openNetwork.requestChange',
                 'open_network_request_change',
                 30000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-network.gftd.ai:core',
                 'did:web:open-network.gftd.ai:core',
                 'sys.bpmn.seed.open-network',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-requestChange-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-defineLink-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-network-requestChange-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-define-link-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-network-request-change-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
