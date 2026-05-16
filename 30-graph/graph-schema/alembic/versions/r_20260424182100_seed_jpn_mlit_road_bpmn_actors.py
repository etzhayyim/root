"""Captured from Kysely migration 20260424182100_seed_jpn_mlit_road_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424182100_seed_jpn_mlit_road_bpmn_actors"
down_revision = 'r_20260424182000_vertex_jpn_mlit_road'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-register-construction-v1',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'jpn_mlit_road_register_construction',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_mlit_road_register_construction"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-mlit-road"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_mlit_road_register_construction" name="MLIT 道路工事届" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="construction 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_mlit_road_construction&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, construction_id: constructionId, road_code: '
                 'roadCode,\n'
                 '              section_from: sectionFrom, section_to: sectionTo,\n'
                 '              work_type: workType, contractor_org_id: contractorOrgId,\n'
                 '              start_date: startDate, end_date: endDate, expected_impact: '
                 'expectedImpact,\n'
                 '              status: &quot;scheduled&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-mlit-road&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit '
                 'jpnMlitRoad.construction.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-mlit-road.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnMlitRoad.construction.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, constructionId: '
                 'constructionId, roadCode: roadCode, workType: workType, expectedImpact: '
                 'expectedImpact}" target="payload"/>\n'
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
                 2798,
                 '00-contracts/bpmn/ai/gftd/jpn-mlit-road/registerConstruction.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'sys.bpmn.seed.jpn-mlit-road',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-register-construction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-issue-traffic-restriction-v1',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'jpn_mlit_road_issue_traffic_restriction',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_mlit_road_issue_traffic_restriction"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-mlit-road"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_mlit_road_issue_traffic_restriction" name="MLIT 交通規制" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if restrictionType = &quot;full-closure&quot; '
                 'then &quot;major&quot;\n'
                 '                                else if list '
                 'contains([&quot;detour&quot;,&quot;weight&quot;], restrictionType) then '
                 '&quot;moderate&quot;\n'
                 '                                else &quot;minor&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;full-closure&quot;,&quot;detour&quot;], restrictionType)" '
                 'target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="restriction 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_mlit_road_restriction&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, restriction_id: restrictionId, road_code: '
                 'roadCode,\n'
                 '              restriction_type: restrictionType, reason: reason,\n'
                 '              section_from: sectionFrom, section_to: sectionTo,\n'
                 '              effective_from: effectiveFrom, effective_until: effectiveUntil,\n'
                 '              severity: severity, require_public_notice: requirePublicNotice,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-mlit-road&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Log">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Major</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Log</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Major" sourceRef="Gate" '
                 'targetRef="Task_AuditMajor">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnMlitRoad.restriction.publicNotice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-mlit-road.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;jpnMlitRoad.restriction.publicNotice&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, restrictionId: '
                 'restrictionId, roadCode: roadCode, restrictionType: restrictionType, severity: '
                 'severity}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit '
                 'jpnMlitRoad.restriction.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-mlit-road.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnMlitRoad.restriction.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, restrictionId: '
                 'restrictionId, roadCode: roadCode, restrictionType: restrictionType, severity: '
                 'severity}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Log</bpmn:incoming><bpmn:outgoing>Flow_EL</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EL" sourceRef="Task_AuditLog" '
                 'targetRef="End_L"/>\n'
                 '    <bpmn:endEvent '
                 'id="End_L"><bpmn:incoming>Flow_EL</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5340,
                 '00-contracts/bpmn/ai/gftd/jpn-mlit-road/issueTrafficRestriction.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'sys.bpmn.seed.jpn-mlit-road',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-issue-traffic-restriction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-registerConstruction-v1',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'ai.gftd.apps.jpnMlitRoad.registerConstruction',
                 'jpn_mlit_road_register_construction',
                 15000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'sys.bpmn.seed.jpn-mlit-road',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-registerConstruction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-issueTrafficRestriction-v1',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'ai.gftd.apps.jpnMlitRoad.issueTrafficRestriction',
                 'jpn_mlit_road_issue_traffic_restriction',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'did:web:jpn-mlit-road.gftd.ai',
                 'sys.bpmn.seed.jpn-mlit-road',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-issueTrafficRestriction-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-registerConstruction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-mlit-road-issueTrafficRestriction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-register-construction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-mlit-road-issue-traffic-restriction-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
