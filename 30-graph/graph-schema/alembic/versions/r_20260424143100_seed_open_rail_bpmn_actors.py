"""Captured from Kysely migration 20260424143100_seed_open_rail_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424143100_seed_open_rail_bpmn_actors"
down_revision = 'r_20260424143000_vertex_open_rail'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-define-line-v1',
                 'did:web:open-rail.gftd.ai:ops',
                 'open_rail_define_line',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_rail_define_line"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-rail"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rail_define_line" name="路線 登録" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="line 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_rail_line&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, operator_org_id: operatorOrgId,\n'
                 '              line_code: lineCode, name: name, gauge_mm: gaugeMm, length_km: '
                 'lengthKm,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: operatorOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rail&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit line.define">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-rail.gftd.ai:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openRail.line.define&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, lineCode: lineCode, '
                 'operatorOrgId: operatorOrgId}" target="payload"/>\n'
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
                 2490,
                 '00-contracts/bpmn/ai/gftd/open-rail/defineLine.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-rail.gftd.ai:ops',
                 'did:web:open-rail.gftd.ai:ops',
                 'sys.bpmn.seed.open-rail',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-define-line-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-report-incident-v1',
                 'did:web:open-rail.gftd.ai:ops',
                 'open_rail_report_incident',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_rail_report_incident"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-rail"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rail_report_incident" name="鉄道事故 報告" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      major   : category in {derailment, collision, fatality} OR delayMinutes >= '
                 '60\n'
                 '      moderate: delayMinutes in [15, 59] OR category = signal-failure\n'
                 '      minor   : otherwise\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="severity 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if list '
                 'contains([&quot;derailment&quot;,&quot;collision&quot;,&quot;fatality&quot;], '
                 'category) or delayMinutes &gt;= 60 then &quot;major&quot;\n'
                 '                                else if delayMinutes &gt;= 15 or category = '
                 '&quot;signal-failure&quot; then &quot;moderate&quot;\n'
                 '                                else &quot;minor&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;derailment&quot;,&quot;collision&quot;,&quot;fatality&quot;], '
                 'category) or delayMinutes &gt;= 60" target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="incident 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_rail_incident&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, operator_org_id: operatorOrgId,\n'
                 '              line_vid: lineVid, run_vid: runVid,\n'
                 '              category: category, narrative: narrative, delay_minutes: '
                 'delayMinutes,\n'
                 '              severity: severity, require_public_notice: requirePublicNotice,\n'
                 '              status: &quot;open&quot;, reported_at: reportedAt, created_at: '
                 'string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: operatorOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rail&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
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
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit incident.major">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-rail.gftd.ai:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openRail.incident.major&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'lineVid: lineVid, category: category}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSilent" name="audit incident.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-rail.gftd.ai:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openRail.incident.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'lineVid: lineVid, category: category}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Silent</bpmn:incoming><bpmn:outgoing>Flow_ES</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ES" sourceRef="Task_AuditSilent" '
                 'targetRef="End_S"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_S"><bpmn:incoming>Flow_ES</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5425,
                 '00-contracts/bpmn/ai/gftd/open-rail/reportIncident.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-rail.gftd.ai:ops',
                 'did:web:open-rail.gftd.ai:ops',
                 'sys.bpmn.seed.open-rail',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-report-incident-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-defineLine-v1',
                 'did:web:open-rail.gftd.ai:ops',
                 'ai.gftd.apps.openRail.defineLine',
                 'open_rail_define_line',
                 15000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-rail.gftd.ai:ops',
                 'did:web:open-rail.gftd.ai:ops',
                 'sys.bpmn.seed.open-rail',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-defineLine-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-reportIncident-v1',
                 'did:web:open-rail.gftd.ai:ops',
                 'ai.gftd.apps.openRail.reportIncident',
                 'open_rail_report_incident',
                 30000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-rail.gftd.ai:ops',
                 'did:web:open-rail.gftd.ai:ops',
                 'sys.bpmn.seed.open-rail',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-reportIncident-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-defineLine-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-rail-reportIncident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-define-line-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-rail-report-incident-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
