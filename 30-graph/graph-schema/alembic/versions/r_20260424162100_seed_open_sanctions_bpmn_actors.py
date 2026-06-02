"""Captured from Kysely migration 20260424162100_seed_open_sanctions_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424162100_seed_open_sanctions_bpmn_actors"
down_revision = 'r_20260424162000_vertex_open_sanctions'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-record-entry-v1',
                 'did:web:open-sanctions.etzhayyim.com',
                 'open_sanctions_record_entry',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_sanctions_record_entry"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-sanctions"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_sanctions_record_entry" name="制裁リスト エントリ記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="sanctions entry 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_sanctions_entry&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, program: program, list_id: listId,\n'
                 '              entity_name: entityName, entity_type: entityType,\n'
                 '              country: country, sanction_type: sanctionType,\n'
                 '              aliases: aliases, listed_at: listedAt,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-sanctions&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-sanctions.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSanctions.entry.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, program: program, listId: '
                 'listId, entityName: entityName, entityType: entityType}" target="payload"/>\n'
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
                 2682,
                 '00-contracts/bpmn/com/etzhayyim/open-sanctions/recordSanctionsEntry.bpmn',
                 '2026-04-24T16:30:00Z',
                 'did:web:open-sanctions.etzhayyim.com',
                 'did:web:open-sanctions.etzhayyim.com',
                 'sys.bpmn.seed.open-sanctions',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-record-entry-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-screen-entity-v1',
                 'did:web:open-sanctions.etzhayyim.com',
                 'open_sanctions_screen_entity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_sanctions_screen_entity"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-sanctions"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_sanctions_screen_entity" name="制裁スクリーニング" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Decide"/>\n'
                 '\n'
                 '    <!--\n'
                 '      decision:\n'
                 '        block         : matchScore >= 0.9\n'
                 '        manual-review : matchScore >= 0.5\n'
                 '        pass          : < 0.5\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Decide" name="decision 判定">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if matchScore &gt;= 0.9 then &quot;block&quot; '
                 'else if matchScore &gt;= 0.5 then &quot;manual-review&quot; else '
                 '&quot;pass&quot;" target="decision"/>\n'
                 '          <zeebe:output source="=matchScore &gt;= 0.5" '
                 'target="requireManualReview"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Decide" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="screening 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_sanctions_screening&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, caller_org_id: callerOrgId,\n'
                 '              candidate_name: candidateName, candidate_country: '
                 'candidateCountry,\n'
                 '              candidate_lei: candidateLei,\n'
                 '              best_match_name: bestMatchName, best_match_program: '
                 'bestMatchProgram,\n'
                 '              match_score: matchScore, decision: decision,\n'
                 '              require_manual_review: requireManualReview,\n'
                 '              screened_at: screenedAt, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 2,\n'
                 '              org_id: callerOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-sanctions&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Pass">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Block</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Pass</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Block" sourceRef="Gate" '
                 'targetRef="Task_AuditBlock">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=decision = '
                 '"block"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Gate" '
                 'targetRef="Task_AuditManual">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=decision = '
                 '"manual-review"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Pass" sourceRef="Gate" '
                 'targetRef="Task_AuditPass"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditBlock" name="audit screen.block">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-sanctions.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSanctions.screen.block&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, candidateName: '
                 'candidateName, matchScore: matchScore, bestMatchProgram: bestMatchProgram}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Block</bpmn:incoming><bpmn:outgoing>Flow_EB</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EB" sourceRef="Task_AuditBlock" '
                 'targetRef="End_B"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditManual" name="audit screen.manualReview">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-sanctions.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSanctions.screen.manualReview&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, candidateName: '
                 'candidateName, matchScore: matchScore}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Manual</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditManual" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditPass" name="audit screen.pass">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-sanctions.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSanctions.screen.pass&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, candidateName: '
                 'candidateName, matchScore: matchScore}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Pass</bpmn:incoming><bpmn:outgoing>Flow_EP</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EP" sourceRef="Task_AuditPass" '
                 'targetRef="End_P"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_P"><bpmn:incoming>Flow_EP</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EM</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_B"><bpmn:incoming>Flow_EB</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6327,
                 '00-contracts/bpmn/com/etzhayyim/open-sanctions/screenEntity.bpmn',
                 '2026-04-24T16:30:00Z',
                 'did:web:open-sanctions.etzhayyim.com',
                 'did:web:open-sanctions.etzhayyim.com',
                 'sys.bpmn.seed.open-sanctions',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-screen-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-recordSanctionsEntry-v1',
                 'did:web:open-sanctions.etzhayyim.com',
                 'com.etzhayyim.apps.openSanctions.recordSanctionsEntry',
                 'open_sanctions_record_entry',
                 15000,
                 '2026-04-24T16:30:00Z',
                 'did:web:open-sanctions.etzhayyim.com',
                 'did:web:open-sanctions.etzhayyim.com',
                 'sys.bpmn.seed.open-sanctions',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-recordSanctionsEntry-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-screenEntity-v1',
                 'did:web:open-sanctions.etzhayyim.com',
                 'com.etzhayyim.apps.openSanctions.screenEntity',
                 'open_sanctions_screen_entity',
                 30000,
                 '2026-04-24T16:30:00Z',
                 'did:web:open-sanctions.etzhayyim.com',
                 'did:web:open-sanctions.etzhayyim.com',
                 'sys.bpmn.seed.open-sanctions',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-screenEntity-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-recordSanctionsEntry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-sanctions-screenEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-record-entry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-sanctions-screen-entity-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
