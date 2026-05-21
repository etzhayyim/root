"""Captured from Kysely migration 20260424141100_seed_open_gas_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424141100_seed_open_gas_bpmn_actors"
down_revision = 'r_20260424141000_vertex_open_gas'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-define-pipe-segment-v1',
                 'did:web:open-gas.etzhayyim.com:network',
                 'open_gas_define_pipe_segment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_gas_define_pipe_segment"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-gas"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_gas_define_pipe_segment" name="ガス管 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="segment 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_gas_segment&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, utility_org_id: utilityOrgId,\n'
                 '              from_vertex_id: fromVertexId, to_vertex_id: toVertexId,\n'
                 '              diameter_mm: diameterMm, material: material, length_m: lengthM,\n'
                 '              maop_kpa: maopKpa, installed_at: installedAt,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: utilityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-gas&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_EF</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EF" sourceRef="Task_Save" '
                 'targetRef="Task_EdgeFrom"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeFrom" name="endpoint edge (from)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_gas_segment_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:from&quot;,\n'
                 '              src_vid: vertexId, dst_vid: fromVertexId, role: &quot;from&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: utilityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-gas&quot;\n'
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
                 '          <zeebe:input source="=&quot;edge_open_gas_segment_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:to&quot;,\n'
                 '              src_vid: vertexId, dst_vid: toVertexId, role: &quot;to&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: utilityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-gas&quot;\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit segment.define">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-gas.etzhayyim.com:network&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openGas.segment.define&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, utilityOrgId: utilityOrgId, '
                 'diameterMm: diameterMm, material: material, lengthM: lengthM}" '
                 'target="payload"/>\n'
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
                 4648,
                 '00-contracts/bpmn/ai/gftd/open-gas/definePipeSegment.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-gas.etzhayyim.com:network',
                 'did:web:open-gas.etzhayyim.com:network',
                 'sys.bpmn.seed.open-gas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-define-pipe-segment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-report-leak-v1',
                 'did:web:open-gas.etzhayyim.com:network',
                 'open_gas_report_leak',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_gas_report_leak"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-gas"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_gas_report_leak" name="ガス漏れ 報告" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      DOT 49 CFR 192.703 aligned:\n'
                 '        class 1: concentration >= 80% LEL OR nearIgnition = true  → immediate\n'
                 '        class 2: 20..79% LEL  → repair within 6 months\n'
                 '        class 3: < 20% LEL    → monitor\n'
                 '      requirePublicNotice = class 1\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="class 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if concentrationLelPct &gt;= 80 or nearIgnition '
                 '= true then 1\n'
                 '                                else if concentrationLelPct &gt;= 20 then 2 else '
                 '3" target="leakClass"/>\n'
                 '          <zeebe:output source="=concentrationLelPct &gt;= 80 or nearIgnition = '
                 'true" target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_SaveLeak"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveLeak" name="leak 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_gas_leak&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, utility_org_id: utilityOrgId,\n'
                 '              segment_vertex_id: segmentVertexId,\n'
                 '              latitude: latitude, longitude: longitude,\n'
                 '              concentration_lel_pct: concentrationLelPct, near_ignition: '
                 'nearIgnition,\n'
                 '              leak_class: leakClass, require_public_notice: '
                 'requirePublicNotice,\n'
                 '              status: &quot;open&quot;, reported_at: reportedAt, created_at: '
                 'string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: utilityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-gas&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_SaveLeak" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Silent">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Notice</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Silent</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Notice" sourceRef="Gate" '
                 'targetRef="Task_AuditMajor">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Silent" sourceRef="Gate" '
                 'targetRef="Task_AuditSilent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit leak.class1">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-gas.etzhayyim.com:network&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openGas.leak.class1&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, leakClass: leakClass, '
                 'segmentVertexId: segmentVertexId}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_EndM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSilent" name="audit leak.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-gas.etzhayyim.com:network&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openGas.leak.log&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, leakClass: leakClass, '
                 'segmentVertexId: segmentVertexId}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Silent</bpmn:incoming><bpmn:outgoing>Flow_EndS</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndS" sourceRef="Task_AuditSilent" '
                 'targetRef="End_S"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_S"><bpmn:incoming>Flow_EndS</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EndM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5290,
                 '00-contracts/bpmn/ai/gftd/open-gas/reportLeak.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-gas.etzhayyim.com:network',
                 'did:web:open-gas.etzhayyim.com:network',
                 'sys.bpmn.seed.open-gas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-report-leak-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-definePipeSegment-v1',
                 'did:web:open-gas.etzhayyim.com:network',
                 'ai.gftd.apps.openGas.definePipeSegment',
                 'open_gas_define_pipe_segment',
                 15000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-gas.etzhayyim.com:network',
                 'did:web:open-gas.etzhayyim.com:network',
                 'sys.bpmn.seed.open-gas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-definePipeSegment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-reportLeak-v1',
                 'did:web:open-gas.etzhayyim.com:network',
                 'ai.gftd.apps.openGas.reportLeak',
                 'open_gas_report_leak',
                 30000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-gas.etzhayyim.com:network',
                 'did:web:open-gas.etzhayyim.com:network',
                 'sys.bpmn.seed.open-gas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-reportLeak-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-definePipeSegment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-gas-reportLeak-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-define-pipe-segment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-gas-report-leak-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
