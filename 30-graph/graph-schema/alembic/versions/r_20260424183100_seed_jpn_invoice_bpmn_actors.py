"""Captured from Kysely migration 20260424183100_seed_jpn_invoice_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424183100_seed_jpn_invoice_bpmn_actors"
down_revision = 'r_20260424183000_vertex_jpn_invoice'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-register-issuer-v1',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'jpn_invoice_register_issuer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_invoice_register_issuer"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jpn-invoice"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_invoice_register_issuer" name="国税庁 インボイス登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="issuer 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_invoice_issuer&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, registration_number: registrationNumber,\n'
                 '              name_ja: nameJa, issuer_type: issuerType, corporate_number: '
                 'corporateNumber,\n'
                 '              registered_address: registeredAddress, registration_date: '
                 'registrationDate,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: corporateNumber, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-invoice&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit jpnInvoice.issuer.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-invoice.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnInvoice.issuer.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, registrationNumber: '
                 'registrationNumber, issuerType: issuerType, corporateNumber: corporateNumber}" '
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
                 2700,
                 '00-contracts/bpmn/ai/gftd/jpn-invoice/registerInvoiceIssuer.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'sys.bpmn.seed.jpn-invoice',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-register-issuer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-record-corporate-tax-filing-v1',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'jpn_invoice_record_corporate_tax_filing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_invoice_record_corporate_tax_filing"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jpn-invoice"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_invoice_record_corporate_tax_filing" name="国税庁 法人税申告" '
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
                 '          <zeebe:output source="=if taxableIncome &gt;= 1000000000 then '
                 '&quot;large&quot;\n'
                 '                                else if taxableIncome &gt;= 100000000 then '
                 '&quot;medium&quot;\n'
                 '                                else &quot;small&quot;" target="sizeTier"/>\n'
                 '          <zeebe:output source="=taxableIncome &gt;= 1000000000" '
                 'target="requireAudit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="tax 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_invoice_corporate_tax&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, filer_corporate_number: '
                 'filerCorporateNumber,\n'
                 '              fiscal_year: fiscalYear, taxable_income: taxableIncome,\n'
                 '              tax_payable: taxPayable, filing_type: filingType,\n'
                 '              filed_at: filedAt, size_tier: sizeTier, require_audit: '
                 'requireAudit,\n'
                 '              status: &quot;accepted&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 2,\n'
                 '              org_id: filerCorporateNumber, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-invoice&quot;\n'
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
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=requireAudit '
                 '= true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Log" sourceRef="Gate" '
                 'targetRef="Task_AuditLog"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit '
                 'jpnInvoice.tax.auditRequired">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-invoice.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnInvoice.tax.auditRequired&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, filerCorporateNumber: '
                 'filerCorporateNumber, fiscalYear: fiscalYear, sizeTier: sizeTier, taxPayable: '
                 'taxPayable}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Major</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditLog" name="audit jpnInvoice.tax.accept">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-invoice.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnInvoice.tax.accept&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, filerCorporateNumber: '
                 'filerCorporateNumber, fiscalYear: fiscalYear, sizeTier: sizeTier, taxPayable: '
                 'taxPayable}" target="payload"/>\n'
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
                 5142,
                 '00-contracts/bpmn/ai/gftd/jpn-invoice/recordCorporateTaxFiling.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'sys.bpmn.seed.jpn-invoice',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-record-corporate-tax-filing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-registerInvoiceIssuer-v1',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'app.etzhayyim.apps.jpnInvoice.registerInvoiceIssuer',
                 'jpn_invoice_register_issuer',
                 15000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'sys.bpmn.seed.jpn-invoice',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-registerInvoiceIssuer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-recordCorporateTaxFiling-v1',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'app.etzhayyim.apps.jpnInvoice.recordCorporateTaxFiling',
                 'jpn_invoice_record_corporate_tax_filing',
                 30000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'did:web:jpn-invoice.etzhayyim.com',
                 'sys.bpmn.seed.jpn-invoice',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-recordCorporateTaxFiling-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-registerInvoiceIssuer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/jpn-invoice-recordCorporateTaxFiling-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-register-issuer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/jpn-invoice-record-corporate-tax-filing-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
