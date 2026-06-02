"""Captured from Kysely migration 20260424131100_seed_open_power_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424131100_seed_open_power_bpmn_actors"
down_revision = 'r_20260424131000_vertex_open_power'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-define-feeder-v1',
                 'did:web:open-power.etzhayyim.com:grid',
                 'open_power_define_feeder',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_power_define_feeder"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-power"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_power_define_feeder" name="配電線 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveFeeder"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveFeeder" name="feeder 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_power_feeder&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              utility_org_id:   utilityOrgId,\n'
                 '              from_vertex_id:   fromVertexId,\n'
                 '              to_vertex_id:     toVertexId,\n'
                 '              voltage_kv:       voltageKv,\n'
                 '              capacity_amps:    capacityAmps,\n'
                 '              length_km:        lengthKm,\n'
                 '              installed_at:     installedAt,\n'
                 '              status:           &quot;active&quot;,\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           utilityOrgId,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-power&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_EF</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EF" sourceRef="Task_SaveFeeder" '
                 'targetRef="Task_EdgeFrom"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeFrom" name="endpoint edge (from)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_power_feeder_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:from&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   fromVertexId,\n'
                 '              role:      &quot;from&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    utilityOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-power&quot;\n'
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
                 '          <zeebe:input source="=&quot;edge_open_power_feeder_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:to&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   toVertexId,\n'
                 '              role:      &quot;to&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    utilityOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-power&quot;\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit feeder.define">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-power.etzhayyim.com:grid&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPower.feeder.define&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, utilityOrgId: utilityOrgId, '
                 'voltageKv: voltageKv, fromVertexId: fromVertexId, toVertexId: toVertexId}" '
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
                 5073,
                 '00-contracts/bpmn/com/etzhayyim/open-power/defineFeeder.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-power.etzhayyim.com:grid',
                 'did:web:open-power.etzhayyim.com:grid',
                 'sys.bpmn.seed.open-power',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-define-feeder-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-report-outage-v1',
                 'did:web:open-power.etzhayyim.com:grid',
                 'open_power_report_outage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_power_report_outage"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-power"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_power_report_outage" name="停電 報告" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      major    : customersAffected >= 1000 OR cause = "storm"\n'
                 '      moderate : 100..999\n'
                 '      minor    : < 100\n'
                 '      public notice: severity = major\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="severity 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if customersAffected &gt;= 1000 or cause = '
                 '&quot;storm&quot; then &quot;major&quot;\n'
                 '                                else if customersAffected &gt;= 100 then '
                 '&quot;moderate&quot;\n'
                 '                                else &quot;minor&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=customersAffected &gt;= 1000 or cause = '
                 '&quot;storm&quot;" target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_SaveOutage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveOutage" name="outage 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_power_outage&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:             vertexId,\n'
                 '              utility_org_id:        utilityOrgId,\n'
                 '              feeder_vertex_id:      feederVertexId,\n'
                 '              cause:                 cause,\n'
                 '              customers_affected:    customersAffected,\n'
                 '              severity:              severity,\n'
                 '              require_public_notice: requirePublicNotice,\n'
                 '              status:                &quot;open&quot;,\n'
                 '              reported_at:           reportedAt,\n'
                 '              created_at:            string(now()),\n'
                 '              owner_did:             callerDid,\n'
                 '              sensitivity_ord:       1,\n'
                 '              org_id:                utilityOrgId,\n'
                 '              user_id:               callerDid,\n'
                 '              actor_id:              &quot;sys.bpmn.open-power&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_SaveOutage" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" name="公衆周知?" default="Flow_Silent">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Notice</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Silent</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Notice" sourceRef="Gate" '
                 'targetRef="Task_Notice">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Silent" sourceRef="Gate" '
                 'targetRef="Task_AuditSilent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Notice" name="公衆周知 post">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;" target="type"/>\n'
                 '          <zeebe:input source="={\n'
                 '              text: &quot;[open-power] 停電公衆周知: feeder=&quot; + '
                 'string(feederVertexId)\n'
                 '                    + &quot; affected=&quot; + string(customersAffected)\n'
                 '                    + &quot; cause=&quot; + string(cause),\n'
                 '              createdAt: string(now())\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_AM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AM" sourceRef="Task_Notice" '
                 'targetRef="Task_AuditMajor"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit outage.notice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-power.etzhayyim.com:grid&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPower.outage.publicNotice&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'feederVertexId: feederVertexId, customersAffected: customersAffected}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_AM</bpmn:incoming><bpmn:outgoing>Flow_EndM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSilent" name="audit outage.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-power.etzhayyim.com:grid&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPower.outage.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'feederVertexId: feederVertexId}" target="payload"/>\n'
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
                 6409,
                 '00-contracts/bpmn/com/etzhayyim/open-power/reportOutage.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-power.etzhayyim.com:grid',
                 'did:web:open-power.etzhayyim.com:grid',
                 'sys.bpmn.seed.open-power',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-report-outage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-defineFeeder-v1',
                 'did:web:open-power.etzhayyim.com:grid',
                 'com.etzhayyim.apps.openPower.defineFeeder',
                 'open_power_define_feeder',
                 15000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-power.etzhayyim.com:grid',
                 'did:web:open-power.etzhayyim.com:grid',
                 'sys.bpmn.seed.open-power',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-defineFeeder-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-reportOutage-v1',
                 'did:web:open-power.etzhayyim.com:grid',
                 'com.etzhayyim.apps.openPower.reportOutage',
                 'open_power_report_outage',
                 30000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-power.etzhayyim.com:grid',
                 'did:web:open-power.etzhayyim.com:grid',
                 'sys.bpmn.seed.open-power',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-reportOutage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-defineFeeder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-power-reportOutage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-define-feeder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-power-report-outage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
