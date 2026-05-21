"""Captured from Kysely migration 20260424144100_seed_open_swift_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424144100_seed_open_swift_bpmn_actors"
down_revision = 'r_20260424144000_vertex_open_swift'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-register-institution-v1',
                 'did:web:open-swift.etzhayyim.com:core',
                 'open_swift_register_institution',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_swift_register_institution"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-swift"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_swift_register_institution" name="SWIFT institution 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="institution 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_swift_institution&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, bic: bic, institution_did: institutionDid,\n'
                 '              legal_name: legalName, country: country, settlement_agent: '
                 'settlementAgent,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 2,\n'
                 '              org_id: institutionDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-swift&quot;\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit institution.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-swift.etzhayyim.com:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSwift.institution.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, bic: bic, country: '
                 'country}" target="payload"/>\n'
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
                 2552,
                 '00-contracts/bpmn/ai/gftd/open-swift/registerInstitution.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-swift.etzhayyim.com:core',
                 'did:web:open-swift.etzhayyim.com:core',
                 'sys.bpmn.seed.open-swift',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-register-institution-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-send-customer-credit-transfer-v1',
                 'did:web:open-swift.etzhayyim.com:core',
                 'open_swift_send_customer_credit_transfer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_swift_send_customer_credit_transfer"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-swift"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_swift_send_customer_credit_transfer" name="pacs.008 送信" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Screen"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Settlement screening (FATF-aligned high-risk list):\n'
                 '        block        : senderCountry/receiverCountry in {IRN, PRK, RUS, MMR, '
                 'SYR}\n'
                 '        manual-review: amount >= 1000000 OR senderCountry/receiverCountry in '
                 '{AFG, CUB, YEM, LBY, ZWE}\n'
                 '        auto-pass    : otherwise\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Screen" name="screening">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if list '
                 'contains([&quot;IRN&quot;,&quot;PRK&quot;,&quot;RUS&quot;,&quot;MMR&quot;,&quot;SYR&quot;], '
                 'senderCountry) or list '
                 'contains([&quot;IRN&quot;,&quot;PRK&quot;,&quot;RUS&quot;,&quot;MMR&quot;,&quot;SYR&quot;], '
                 'receiverCountry) then &quot;block&quot;\n'
                 '                                else if amount &gt;= 1000000 or list '
                 'contains([&quot;AFG&quot;,&quot;CUB&quot;,&quot;YEM&quot;,&quot;LBY&quot;,&quot;ZWE&quot;], '
                 'senderCountry) or list '
                 'contains([&quot;AFG&quot;,&quot;CUB&quot;,&quot;YEM&quot;,&quot;LBY&quot;,&quot;ZWE&quot;], '
                 'receiverCountry) then &quot;manual-review&quot;\n'
                 '                                else &quot;auto-pass&quot;" '
                 'target="screeningDecision"/>\n'
                 '          <zeebe:output source="=amount &gt;= 1000000 or list '
                 'contains([&quot;AFG&quot;,&quot;CUB&quot;,&quot;YEM&quot;,&quot;LBY&quot;,&quot;ZWE&quot;], '
                 'senderCountry) or list '
                 'contains([&quot;AFG&quot;,&quot;CUB&quot;,&quot;YEM&quot;,&quot;LBY&quot;,&quot;ZWE&quot;], '
                 'receiverCountry)" target="requireManualReview"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Screen" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="message 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_swift_message&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, uetr: uetr, message_type: '
                 '&quot;pacs.008&quot;,\n'
                 '              sender_vid: senderVid, receiver_vid: receiverVid,\n'
                 '              debtor_name: debtorName, creditor_name: creditorName,\n'
                 '              amount: amount, currency: currency, value_date: valueDate,\n'
                 '              screening_decision: screeningDecision, require_manual_review: '
                 'requireManualReview,\n'
                 '              status: &quot;submitted&quot;, submitted_at: string(now()), '
                 'created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 2,\n'
                 '              org_id: senderVid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-swift&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_ES</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ES" sourceRef="Task_Save" '
                 'targetRef="Task_EdgeSender"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeSender" name="edge (sender)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_swift_message_party&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:sender&quot;,\n'
                 '              src_vid: vertexId, dst_vid: senderVid, role: &quot;sender&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '2,\n'
                 '              org_id: senderVid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-swift&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_ES</bpmn:incoming><bpmn:outgoing>Flow_ER</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ER" sourceRef="Task_EdgeSender" '
                 'targetRef="Task_EdgeReceiver"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeReceiver" name="edge (receiver)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_swift_message_party&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:receiver&quot;,\n'
                 '              src_vid: vertexId, dst_vid: receiverVid, role: '
                 '&quot;receiver&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '2,\n'
                 '              org_id: senderVid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-swift&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_ER</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_EdgeReceiver" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_AutoPass">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Block</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_AutoPass</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Block" sourceRef="Gate" '
                 'targetRef="Task_AuditBlock">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=screeningDecision = '
                 '"block"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Gate" '
                 'targetRef="Task_AuditManual">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=screeningDecision = '
                 '"manual-review"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_AutoPass" sourceRef="Gate" '
                 'targetRef="Task_AuditAuto"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditBlock" name="audit screening.block">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-swift.etzhayyim.com:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSwift.screening.block&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, uetr: uetr, amount: amount, '
                 'currency: currency, senderCountry: senderCountry, receiverCountry: '
                 'receiverCountry}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Block</bpmn:incoming><bpmn:outgoing>Flow_EB</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EB" sourceRef="Task_AuditBlock" '
                 'targetRef="End_B"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditManual" name="audit '
                 'screening.manualReview">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-swift.etzhayyim.com:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSwift.screening.manualReview&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, uetr: uetr, amount: amount, '
                 'currency: currency}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Manual</bpmn:incoming><bpmn:outgoing>Flow_EMR</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EMR" sourceRef="Task_AuditManual" '
                 'targetRef="End_MR"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAuto" name="audit screening.autoPass">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-swift.etzhayyim.com:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSwift.screening.autoPass&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, uetr: uetr, amount: amount, '
                 'currency: currency}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_AutoPass</bpmn:incoming><bpmn:outgoing>Flow_EA</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EA" sourceRef="Task_AuditAuto" '
                 'targetRef="End_A"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_A"><bpmn:incoming>Flow_EA</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_MR"><bpmn:incoming>Flow_EMR</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_B"><bpmn:incoming>Flow_EB</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 9305,
                 '00-contracts/bpmn/ai/gftd/open-swift/sendCustomerCreditTransfer.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-swift.etzhayyim.com:core',
                 'did:web:open-swift.etzhayyim.com:core',
                 'sys.bpmn.seed.open-swift',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-send-customer-credit-transfer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-registerInstitution-v1',
                 'did:web:open-swift.etzhayyim.com:core',
                 'ai.gftd.apps.openSwift.registerInstitution',
                 'open_swift_register_institution',
                 15000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-swift.etzhayyim.com:core',
                 'did:web:open-swift.etzhayyim.com:core',
                 'sys.bpmn.seed.open-swift',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-registerInstitution-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-sendCustomerCreditTransfer-v1',
                 'did:web:open-swift.etzhayyim.com:core',
                 'ai.gftd.apps.openSwift.sendCustomerCreditTransfer',
                 'open_swift_send_customer_credit_transfer',
                 30000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-swift.etzhayyim.com:core',
                 'did:web:open-swift.etzhayyim.com:core',
                 'sys.bpmn.seed.open-swift',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-sendCustomerCreditTransfer-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-registerInstitution-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-swift-sendCustomerCreditTransfer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-register-institution-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-swift-send-customer-credit-transfer-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
