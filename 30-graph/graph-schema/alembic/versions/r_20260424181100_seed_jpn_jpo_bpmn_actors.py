"""Captured from Kysely migration 20260424181100_seed_jpn_jpo_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424181100_seed_jpn_jpo_bpmn_actors"
down_revision = 'r_20260424181000_vertex_jpn_jpo'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-file-application-v1',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'jpn_jpo_file_application',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_jpo_file_application"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jpn-jpo"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_jpo_file_application" name="JPO 出願受理" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="application 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_jpo_application&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, application_number: applicationNumber,\n'
                 '              applicant_did: applicantDid, inventor_names: inventorNames,\n'
                 '              ipc_classes: ipcClasses, title: title,\n'
                 '              filing_date: filingDate, priority_date: priorityDate,\n'
                 '              examination_requested: examinationRequested,\n'
                 '              status: &quot;filed&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: applicantDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-jpo&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit jpnJpo.application.file">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jpo.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJpo.application.file&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, applicationNumber: '
                 'applicationNumber, filingDate: filingDate}" target="payload"/>\n'
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
                 2698,
                 '00-contracts/bpmn/com/etzhayyim/jpn-jpo/fileApplication.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'sys.bpmn.seed.jpn-jpo',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-file-application-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-record-examination-v1',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'jpn_jpo_record_examination',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jpn_jpo_record_examination"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jpn-jpo"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="jpn_jpo_record_examination" name="JPO 審査記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="examination 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_jpn_jpo_examination&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, application_number: applicationNumber,\n'
                 '              decision: decision, decision_date: decisionDate,\n'
                 '              examiner_id: examinerId, rejection_grounds: rejectionGrounds,\n'
                 '              cited_art: citedArt, next_action: nextAction,\n'
                 '              status: &quot;recorded&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.jpn-jpo&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit jpnJpo.examination.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:jpn-jpo.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;jpnJpo.examination.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, applicationNumber: '
                 'applicationNumber, decision: decision}" target="payload"/>\n'
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
                 2647,
                 '00-contracts/bpmn/com/etzhayyim/jpn-jpo/recordExamination.bpmn',
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'sys.bpmn.seed.jpn-jpo',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-record-examination-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-fileApplication-v1',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'com.etzhayyim.apps.jpnJpo.fileApplication',
                 'jpn_jpo_file_application',
                 15000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'sys.bpmn.seed.jpn-jpo',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-fileApplication-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-recordExamination-v1',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'com.etzhayyim.apps.jpnJpo.recordExamination',
                 'jpn_jpo_record_examination',
                 15000,
                 '2026-04-24T18:30:00Z',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'did:web:jpn-jpo.etzhayyim.com',
                 'sys.bpmn.seed.jpn-jpo',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-recordExamination-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-fileApplication-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jpn-jpo-recordExamination-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-file-application-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jpn-jpo-record-examination-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
