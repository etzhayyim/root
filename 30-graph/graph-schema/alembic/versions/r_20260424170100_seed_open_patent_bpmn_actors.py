"""Captured from Kysely migration 20260424170100_seed_open_patent_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424170100_seed_open_patent_bpmn_actors"
down_revision = 'r_20260424170000_vertex_open_patent'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-register-patent-v1',
                 'did:web:open-patent.etzhayyim.com',
                 'open_patent_register_patent',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_patent_register_patent"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-patent"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_register_patent" name="特許登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="verification 決定">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if noveltyScore &gt;= 0.9 then '
                 '&quot;authoritative&quot; else if noveltyScore &gt;= 0.5 then '
                 '&quot;community&quot; else &quot;candidate&quot;" target="verification"/>\n'
                 '          <zeebe:output source="=noveltyScore &lt; 0.5" '
                 'target="requireReview"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="patent 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_patent_patent&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, office_org_id: officeOrgId,\n'
                 '              patent_number: patentNumber, jurisdiction: jurisdiction,\n'
                 '              title: title, inventor_names: inventorNames,\n'
                 '              assignee_did: assigneeDid, ipc_classes: ipcClasses,\n'
                 '              filing_date: filingDate, grant_date: grantDate,\n'
                 '              priority_date: priorityDate, novelty_score: noveltyScore,\n'
                 '              verification: verification,\n'
                 '              status: if grantDate = null then &quot;filed&quot; else '
                 '&quot;granted&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid,\n'
                 '              sensitivity_ord: 1, org_id: officeOrgId,\n'
                 '              user_id: callerDid, actor_id: &quot;sys.bpmn.open-patent&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Auto">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Review</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Auto</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Review" sourceRef="Gate" '
                 'targetRef="Task_AuditReview">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=requireReview '
                 '= true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Auto" sourceRef="Gate" '
                 'targetRef="Task_AuditAuto"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditReview" name="audit '
                 'patent.register.reviewPending">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;openPatent.patent.register.reviewPending&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, patentNumber: patentNumber, '
                 'jurisdiction: jurisdiction, verification: verification}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Review</bpmn:incoming><bpmn:outgoing>Flow_ER</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ER" sourceRef="Task_AuditReview" '
                 'targetRef="End_R"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAuto" name="audit patent.register.accept">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPatent.patent.register.accept&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, patentNumber: patentNumber, '
                 'jurisdiction: jurisdiction, verification: verification}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Auto</bpmn:incoming><bpmn:outgoing>Flow_EA</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EA" sourceRef="Task_AuditAuto" '
                 'targetRef="End_A"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_A"><bpmn:incoming>Flow_EA</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_R"><bpmn:incoming>Flow_ER</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5225,
                 '00-contracts/bpmn/ai/gftd/open-patent/registerPatent.bpmn',
                 '2026-04-24T17:30:00Z',
                 'did:web:open-patent.etzhayyim.com',
                 'did:web:open-patent.etzhayyim.com',
                 'sys.bpmn.seed.open-patent',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-register-patent-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-record-citation-v1',
                 'did:web:open-patent.etzhayyim.com',
                 'open_patent_record_citation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_patent_record_citation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-patent"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_record_citation" name="特許引用記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="citation 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_patent_citation&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, citing_patent: citingPatent, cited_patent: '
                 'citedPatent,\n'
                 '              citation_type: citationType, confidence: confidence, source: '
                 'source,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-patent&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit citation.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPatent.citation.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, citingPatent: citingPatent, '
                 'citedPatent: citedPatent, citationType: citationType}" target="payload"/>\n'
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
                 2575,
                 '00-contracts/bpmn/ai/gftd/open-patent/recordCitation.bpmn',
                 '2026-04-24T17:30:00Z',
                 'did:web:open-patent.etzhayyim.com',
                 'did:web:open-patent.etzhayyim.com',
                 'sys.bpmn.seed.open-patent',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-record-citation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-registerPatent-v1',
                 'did:web:open-patent.etzhayyim.com',
                 'ai.gftd.apps.openPatent.registerPatent',
                 'open_patent_register_patent',
                 30000,
                 '2026-04-24T17:30:00Z',
                 'did:web:open-patent.etzhayyim.com',
                 'did:web:open-patent.etzhayyim.com',
                 'sys.bpmn.seed.open-patent',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-registerPatent-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-recordCitation-v1',
                 'did:web:open-patent.etzhayyim.com',
                 'ai.gftd.apps.openPatent.recordCitation',
                 'open_patent_record_citation',
                 15000,
                 '2026-04-24T17:30:00Z',
                 'did:web:open-patent.etzhayyim.com',
                 'did:web:open-patent.etzhayyim.com',
                 'sys.bpmn.seed.open-patent',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-recordCitation-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-registerPatent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-patent-recordCitation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-register-patent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-patent-record-citation-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
