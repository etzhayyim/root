"""Captured from Kysely migration 20260424180100_seed_jpn_jma_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424180100_seed_jpn_jma_bpmn_actors"
down_revision = 'r_20260424180000_vertex_jpn_jma'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-report-earthquake-v1',
                 'did:web:jpn-jma.gftd.ai',
                 'jpn_jma_report_earthquake',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_jma_report_earthquake"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-jma"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_jma_report_earthquake" name="JMA 地震情報" '
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
                 '          <zeebe:output source="=if magnitude &gt;= 7 or list '
                 'contains([&quot;6+&quot;,&quot;7&quot;], maxIntensity) or tsunamiPossibility = '
                 '&quot;major&quot; then &quot;severe&quot;\n'
                 '                                else if magnitude &gt;= 5.5 or list '
                 'contains([&quot;5-&quot;,&quot;5+&quot;,&quot;6-&quot;], maxIntensity) then '
                 '&quot;strong&quot;\n'
                 '                                else if magnitude &gt;= 4 then '
                 '&quot;moderate&quot;\n'
                 '                                else &quot;weak&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=magnitude &gt;= 5.5 or list '
                 'contains([&quot;5-&quot;,&quot;5+&quot;,&quot;6-&quot;,&quot;6+&quot;,&quot;7&quot;], '
                 'maxIntensity) or tsunamiPossibility != &quot;none&quot;" '
                 'target="requireEmergencyNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="earthquake 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_jma_earthquake&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, event_id: eventId, origin_time: originTime,\n'
                 '              epicenter_lat: epicenterLat, epicenter_lon: epicenterLon,\n'
                 '              magnitude: magnitude, depth_km: depthKm,\n'
                 '              max_intensity: maxIntensity, tsunami_possibility: '
                 'tsunamiPossibility,\n'
                 '              severity: severity, require_emergency_notice: '
                 'requireEmergencyNotice,\n'
                 '              status: &quot;published&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-jma&quot;\n'
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
                 'xsi:type="bpmn:tFormalExpression">=requireEmergencyNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnJma.earthquake.emergency">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jma.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJma.earthquake.emergency&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, eventId: eventId, '
                 'magnitude: magnitude, maxIntensity: maxIntensity, severity: severity, '
                 'tsunamiPossibility: tsunamiPossibility}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit '
                 'jpnJma.earthquake.routine">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jma.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJma.earthquake.routine&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, eventId: eventId, '
                 'magnitude: magnitude, maxIntensity: maxIntensity, severity: severity, '
                 'tsunamiPossibility: tsunamiPossibility}" target="payload"/>\n'
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
                 5597,
                 '00-contracts/bpmn/ai/gftd/jpn-jma/reportEarthquake.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jma.gftd.ai',
                 'did:web:jpn-jma.gftd.ai',
                 'sys.bpmn.seed.jpn-jma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-report-earthquake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-issue-weather-warning-v1',
                 'did:web:jpn-jma.gftd.ai',
                 'jpn_jma_issue_weather_warning',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_jma_issue_weather_warning"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-jma"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_jma_issue_weather_warning" name="JMA 気象警報" '
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
                 '          <zeebe:output source="=if warningType = &quot;special-warning&quot; '
                 'then &quot;critical&quot;\n'
                 '                                else if warningType = &quot;warning&quot; then '
                 '&quot;high&quot;\n'
                 '                                else &quot;medium&quot;" target="priority"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;special-warning&quot;,&quot;warning&quot;], warningType)" '
                 'target="requireBroadcast"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="warning 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_jma_weather_warning&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, warning_code: warningCode, warning_type: '
                 'warningType,\n'
                 '              area_code: areaCode, area_name: areaName,\n'
                 '              effective_from: effectiveFrom, effective_until: effectiveUntil,\n'
                 '              priority: priority, require_broadcast: requireBroadcast,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-jma&quot;\n'
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
                 'xsi:type="bpmn:tFormalExpression">=requireBroadcast = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnJma.warning.broadcast">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jma.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJma.warning.broadcast&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, warningCode: warningCode, '
                 'warningType: warningType, areaCode: areaCode, priority: priority}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit jpnJma.warning.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jma.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJma.warning.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, warningCode: warningCode, '
                 'warningType: warningType, areaCode: areaCode, priority: priority}" '
                 'target="payload"/>\n'
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
                 5100,
                 '00-contracts/bpmn/ai/gftd/jpn-jma/issueWeatherWarning.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jma.gftd.ai',
                 'did:web:jpn-jma.gftd.ai',
                 'sys.bpmn.seed.jpn-jma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-issue-weather-warning-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-reportEarthquake-v1',
                 'did:web:jpn-jma.gftd.ai',
                 'ai.gftd.apps.jpnJma.reportEarthquake',
                 'jpn_jma_report_earthquake',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jma.gftd.ai',
                 'did:web:jpn-jma.gftd.ai',
                 'sys.bpmn.seed.jpn-jma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-reportEarthquake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-issueWeatherWarning-v1',
                 'did:web:jpn-jma.gftd.ai',
                 'ai.gftd.apps.jpnJma.issueWeatherWarning',
                 'jpn_jma_issue_weather_warning',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jma.gftd.ai',
                 'did:web:jpn-jma.gftd.ai',
                 'sys.bpmn.seed.jpn-jma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-issueWeatherWarning-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-reportEarthquake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-jma-issueWeatherWarning-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-report-earthquake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-jma-issue-weather-warning-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
