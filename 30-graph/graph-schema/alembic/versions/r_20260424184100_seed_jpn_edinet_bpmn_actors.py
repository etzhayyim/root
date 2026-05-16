"""Captured from Kysely migration 20260424184100_seed_jpn_edinet_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424184100_seed_jpn_edinet_bpmn_actors"
down_revision = 'r_20260424184000_vertex_jpn_edinet'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-submit-securities-filing-v1',
                 'did:web:jpn-edinet.gftd.ai',
                 'jpn_edinet_submit_securities_filing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_edinet_submit_securities_filing"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-edinet"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_edinet_submit_securities_filing" name="金融庁 EDINET 有報" '
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
                 '          <zeebe:output source="=if docTypeCode = &quot;130&quot; then '
                 '&quot;extraordinary&quot;\n'
                 '                                else if list '
                 'contains([&quot;120&quot;,&quot;140&quot;,&quot;160&quot;], docTypeCode) then '
                 '&quot;periodic&quot;\n'
                 '                                else &quot;routine&quot;" '
                 'target="disclosureTier"/>\n'
                 '          <zeebe:output source="=docTypeCode = &quot;130&quot;" '
                 'target="requireMarketNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="filing 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_edinet_securities_filing&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, doc_id: docId, edinet_code: edinetCode,\n'
                 '              issuer_name: issuerName, doc_type_code: docTypeCode,\n'
                 '              doc_description: docDescription, fiscal_year_end: fiscalYearEnd,\n'
                 '              submitted_at: submittedAt, period_covered: periodCovered,\n'
                 '              disclosure_tier: disclosureTier, require_market_notice: '
                 'requireMarketNotice,\n'
                 '              status: &quot;published&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: edinetCode, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-edinet&quot;\n'
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
                 'xsi:type="bpmn:tFormalExpression">=requireMarketNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnEdinet.filing.marketNotice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-edinet.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnEdinet.filing.marketNotice&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, docId: docId, edinetCode: '
                 'edinetCode, docTypeCode: docTypeCode, disclosureTier: disclosureTier}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit jpnEdinet.filing.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-edinet.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnEdinet.filing.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, docId: docId, edinetCode: '
                 'edinetCode, docTypeCode: docTypeCode, disclosureTier: disclosureTier}" '
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
                 5257,
                 '00-contracts/bpmn/ai/gftd/jpn-edinet/submitSecuritiesFiling.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-edinet.gftd.ai',
                 'did:web:jpn-edinet.gftd.ai',
                 'sys.bpmn.seed.jpn-edinet',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-submit-securities-filing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-record-material-event-v1',
                 'did:web:jpn-edinet.gftd.ai',
                 'jpn_edinet_record_material_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_edinet_record_material_event"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/jpn-edinet"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_edinet_record_material_event" name="金融庁 EDINET 臨報" '
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
                 '          <zeebe:output source="=if list '
                 'contains([&quot;delisting&quot;,&quot;insider-trading&quot;,&quot;tob&quot;], '
                 'eventType) then &quot;critical&quot;\n'
                 '                                else if list '
                 'contains([&quot;merger&quot;,&quot;financial-restatement&quot;], eventType) then '
                 '&quot;high&quot;\n'
                 '                                else if list '
                 'contains([&quot;litigation&quot;,&quot;subsidiary-change&quot;,&quot;management-change&quot;], '
                 'eventType) then &quot;medium&quot;\n'
                 '                                else &quot;low&quot;" target="priority"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;delisting&quot;,&quot;insider-trading&quot;,&quot;tob&quot;], '
                 'eventType)" target="requireTradingHalt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_edinet_material_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, event_id: eventId, edinet_code: edinetCode,\n'
                 '              issuer_name: issuerName, event_type: eventType, narrative: '
                 'narrative,\n'
                 '              occurred_at: occurredAt, reported_at: reportedAt,\n'
                 '              priority: priority, require_trading_halt: requireTradingHalt,\n'
                 '              status: &quot;reported&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: edinetCode, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-edinet&quot;\n'
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
                 'xsi:type="bpmn:tFormalExpression">=requireTradingHalt = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnEdinet.event.tradingHalt">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-edinet.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnEdinet.event.tradingHalt&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, eventId: eventId, '
                 'edinetCode: edinetCode, eventType: eventType, priority: priority}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit jpnEdinet.event.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-edinet.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnEdinet.event.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, eventId: eventId, '
                 'edinetCode: edinetCode, eventType: eventType, priority: priority}" '
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
                 5420,
                 '00-contracts/bpmn/ai/gftd/jpn-edinet/recordMaterialEvent.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-edinet.gftd.ai',
                 'did:web:jpn-edinet.gftd.ai',
                 'sys.bpmn.seed.jpn-edinet',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-record-material-event-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-submitSecuritiesFiling-v1',
                 'did:web:jpn-edinet.gftd.ai',
                 'ai.gftd.apps.jpnEdinet.submitSecuritiesFiling',
                 'jpn_edinet_submit_securities_filing',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-edinet.gftd.ai',
                 'did:web:jpn-edinet.gftd.ai',
                 'sys.bpmn.seed.jpn-edinet',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-submitSecuritiesFiling-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-recordMaterialEvent-v1',
                 'did:web:jpn-edinet.gftd.ai',
                 'ai.gftd.apps.jpnEdinet.recordMaterialEvent',
                 'jpn_edinet_record_material_event',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-edinet.gftd.ai',
                 'did:web:jpn-edinet.gftd.ai',
                 'sys.bpmn.seed.jpn-edinet',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-recordMaterialEvent-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-submitSecuritiesFiling-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/jpn-edinet-recordMaterialEvent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-submit-securities-filing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/jpn-edinet-record-material-event-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
