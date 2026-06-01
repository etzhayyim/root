"""Captured from Kysely migration 20260424174100_seed_open_naics_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424174100_seed_open_naics_bpmn_actors"
down_revision = 'r_20260424174000_vertex_open_naics'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-classify-entity-v1',
                 'did:web:open-naics.etzhayyim.com',
                 'open_naics_classify_entity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_naics_classify_entity"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-naics"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_naics_classify_entity" name="NAICS 分類" '
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
                 '          <zeebe:output source="=if confidence &gt;= 0.9 then '
                 '&quot;authoritative&quot; else if confidence &gt;= 0.5 then '
                 '&quot;community&quot; else &quot;candidate&quot;" target="verification"/>\n'
                 '          <zeebe:output source="=confidence &lt; 0.5" target="requireReview"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="classification 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_naics_classification&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, entity_did: entityDid, naics_code: '
                 'naicsCode,\n'
                 '              entity_name: entityName, country: country, evidence_url: '
                 'evidenceUrl,\n'
                 '              confidence: confidence, verification: verification,\n'
                 '              status: &quot;confirmed&quot;, classified_at: classifiedAt,\n'
                 '              created_at: string(now()), owner_did: callerDid,\n'
                 '              sensitivity_ord: 1, org_id: callerDid,\n'
                 '              user_id: callerDid, actor_id: &quot;sys.bpmn.open-naics&quot;\n'
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
                 'classify.reviewPending">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-naics.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNaics.classify.reviewPending&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, entityDid: entityDid, '
                 'naicsCode: naicsCode, verification: verification}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Review</bpmn:incoming><bpmn:outgoing>Flow_ER</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ER" sourceRef="Task_AuditReview" '
                 'targetRef="End_R"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAuto" name="audit classify.accept">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-naics.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNaics.classify.accept&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, entityDid: entityDid, '
                 'naicsCode: naicsCode, verification: verification}" target="payload"/>\n'
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
                 4951,
                 '00-contracts/bpmn/ai/gftd/open-naics/classifyEntity.bpmn',
                 '2026-04-24T17:30:00Z',
                 'did:web:open-naics.etzhayyim.com',
                 'did:web:open-naics.etzhayyim.com',
                 'sys.bpmn.seed.open-naics',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-classify-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-record-concordance-v1',
                 'did:web:open-naics.etzhayyim.com',
                 'open_naics_record_concordance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_naics_record_concordance"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-naics"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_naics_record_concordance" name="NAICS concordance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="concordance 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_naics_concordance&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, naics_code: naicsCode,\n'
                 '              other_taxonomy: otherTaxonomy, other_code: otherCode,\n'
                 '              relation: relation, confidence: confidence, source: source,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-naics&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit concordance.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-naics.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openNaics.concordance.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, naicsCode: naicsCode, '
                 'otherTaxonomy: otherTaxonomy, otherCode: otherCode, relation: relation}" '
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
                 2623,
                 '00-contracts/bpmn/ai/gftd/open-naics/recordConcordance.bpmn',
                 '2026-04-24T17:30:00Z',
                 'did:web:open-naics.etzhayyim.com',
                 'did:web:open-naics.etzhayyim.com',
                 'sys.bpmn.seed.open-naics',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-record-concordance-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-classifyEntity-v1',
                 'did:web:open-naics.etzhayyim.com',
                 'app.etzhayyim.apps.openNaics.classifyEntity',
                 'open_naics_classify_entity',
                 30000,
                 '2026-04-24T17:30:00Z',
                 'did:web:open-naics.etzhayyim.com',
                 'did:web:open-naics.etzhayyim.com',
                 'sys.bpmn.seed.open-naics',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-classifyEntity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-recordConcordance-v1',
                 'did:web:open-naics.etzhayyim.com',
                 'app.etzhayyim.apps.openNaics.recordConcordance',
                 'open_naics_record_concordance',
                 15000,
                 '2026-04-24T17:30:00Z',
                 'did:web:open-naics.etzhayyim.com',
                 'did:web:open-naics.etzhayyim.com',
                 'sys.bpmn.seed.open-naics',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-recordConcordance-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-classifyEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-naics-recordConcordance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-classify-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-naics-record-concordance-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
