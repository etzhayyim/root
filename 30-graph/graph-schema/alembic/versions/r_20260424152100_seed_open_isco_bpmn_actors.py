"""Captured from Kysely migration 20260424152100_seed_open_isco_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424152100_seed_open_isco_bpmn_actors"
down_revision = 'r_20260424152000_vertex_open_isco'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-classify-worker-v1',
                 'did:web:open-isco.gftd.ai',
                 'open_isco_classify_worker',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_isco_classify_worker"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-isco"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_isco_classify_worker" name="労働者 職業分類" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Derive"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Derive" name="openIsco classify worker">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openIsco.classifyWorker"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Derive" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_AutoAccept">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Review</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_AutoAccept</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Review" sourceRef="Gate" '
                 'targetRef="Task_AuditReview">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=requireReview '
                 '= true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_AutoAccept" sourceRef="Gate" '
                 'targetRef="Task_AuditAuto"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditReview" name="audit '
                 'classify.reviewPending">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-isco.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openIsco.classify.reviewPending&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, iscoCode: iscoCode, '
                 'workerDid: workerDid, confidence: confidence, codeLevel: codeLevel, '
                 'classifiedAt: classifiedAt}" target="payload"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-isco.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openIsco.classify.accept&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, iscoCode: iscoCode, '
                 'workerDid: workerDid, verification: verification, codeLevel: codeLevel, '
                 'classifiedAt: classifiedAt}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_AutoAccept</bpmn:incoming><bpmn:outgoing>Flow_EA</bpmn:outgoing>\n'
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
                 3441,
                 '00-contracts/bpmn/ai/gftd/open-isco/classifyWorker.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-isco.gftd.ai',
                 'did:web:open-isco.gftd.ai',
                 'sys.bpmn.seed.open-isco',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-classify-worker-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-record-concordance-v1',
                 'did:web:open-isco.gftd.ai',
                 'open_isco_record_concordance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_isco_record_concordance"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-isco"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_isco_record_concordance" name="ISCO concordance 記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="openIsco record concordance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openIsco.recordConcordance"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit concordance.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-isco.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openIsco.concordance.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, iscoCode: iscoCode, '
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
                 1938,
                 '00-contracts/bpmn/ai/gftd/open-isco/recordConcordance.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-isco.gftd.ai',
                 'did:web:open-isco.gftd.ai',
                 'sys.bpmn.seed.open-isco',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-record-concordance-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-classifyWorker-v1',
                 'did:web:open-isco.gftd.ai',
                 'ai.gftd.apps.openIsco.classifyWorker',
                 'open_isco_classify_worker',
                 30000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-isco.gftd.ai',
                 'did:web:open-isco.gftd.ai',
                 'sys.bpmn.seed.open-isco',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-classifyWorker-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-recordConcordance-v1',
                 'did:web:open-isco.gftd.ai',
                 'ai.gftd.apps.openIsco.recordConcordance',
                 'open_isco_record_concordance',
                 15000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-isco.gftd.ai',
                 'did:web:open-isco.gftd.ai',
                 'sys.bpmn.seed.open-isco',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-recordConcordance-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-classifyWorker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-isco-recordConcordance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-classify-worker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-isco-record-concordance-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
