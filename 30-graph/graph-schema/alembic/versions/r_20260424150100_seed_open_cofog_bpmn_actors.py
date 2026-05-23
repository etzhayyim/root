"""Captured from Kysely migration 20260424150100_seed_open_cofog_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424150100_seed_open_cofog_bpmn_actors"
down_revision = 'r_20260424150000_vertex_open_cofog'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-expenditure-v1',
                 'did:web:open-cofog.etzhayyim.com',
                 'open_cofog_record_expenditure',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cofog_record_expenditure"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cofog"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cofog_record_expenditure" name="政府支出 記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      scale:\n'
                 '        large  : amount >= 1e9\n'
                 '        medium : amount >= 1e7\n'
                 '        small  : otherwise\n'
                 '      public notice = large\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="scale 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if amount &gt;= 1000000000 then '
                 '&quot;large&quot; else if amount &gt;= 10000000 then &quot;medium&quot; else '
                 '&quot;small&quot;" target="scale"/>\n'
                 '          <zeebe:output source="=amount &gt;= 1000000000" '
                 'target="requirePublicNotice"/>\n'
                 '          <zeebe:output '
                 'source="=&quot;at://did:web:open-cofog.etzhayyim.com/ai.gftd.apps.openCofog.class/&quot; '
                 '+ string(cofogClassCode)" target="classDst"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="expenditure 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cofog_expenditure&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, gov_org_id: govOrgId,\n'
                 '              fiscal_year: fiscalYear, cofog_class_code: cofogClassCode,\n'
                 '              amount: amount, currency: currency, narrative: narrative,\n'
                 '              evidence_url: evidenceUrl, confidence: confidence,\n'
                 '              status: &quot;confirmed&quot;, reported_at: reportedAt,\n'
                 '              created_at: string(now()), owner_did: callerDid,\n'
                 '              sensitivity_ord: 1, org_id: govOrgId,\n'
                 '              user_id: callerDid, actor_id: &quot;sys.bpmn.open-cofog&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Edge</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Edge" sourceRef="Task_Save" '
                 'targetRef="Task_Edge"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Edge" name="expenditure → class edge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_cofog_expenditure_class&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:class&quot;,\n'
                 '              src_vid: vertexId, dst_vid: classDst, role: '
                 '&quot;tagged_as&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: govOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cofog&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Edge</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Edge" targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Silent">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Notice</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Silent</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Notice" sourceRef="Gate" '
                 'targetRef="Task_AuditLarge">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Silent" sourceRef="Gate" '
                 'targetRef="Task_AuditSmall"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditLarge" name="audit expenditure.large">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cofog.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCofog.expenditure.large&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, scale: scale, '
                 'cofogClassCode: cofogClassCode, amount: amount, currency: currency, govOrgId: '
                 'govOrgId}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditLarge" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSmall" name="audit expenditure.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cofog.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCofog.expenditure.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, scale: scale, '
                 'cofogClassCode: cofogClassCode, amount: amount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Silent</bpmn:incoming><bpmn:outgoing>Flow_ES</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ES" sourceRef="Task_AuditSmall" '
                 'targetRef="End_S"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_S"><bpmn:incoming>Flow_ES</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6294,
                 '00-contracts/bpmn/ai/gftd/open-cofog/recordExpenditure.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-cofog.etzhayyim.com',
                 'did:web:open-cofog.etzhayyim.com',
                 'sys.bpmn.seed.open-cofog',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-expenditure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-concordance-v1',
                 'did:web:open-cofog.etzhayyim.com',
                 'open_cofog_record_concordance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cofog_record_concordance"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cofog"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cofog_record_concordance" name="概念対応 記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="concordance 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cofog_concordance&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, cofog_class_code: cofogClassCode,\n'
                 '              other_taxonomy: otherTaxonomy, other_code: otherCode,\n'
                 '              relation: relation, confidence: confidence, source: source,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cofog&quot;\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit concordance.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cofog.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCofog.concordance.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, cofogClassCode: '
                 'cofogClassCode, otherTaxonomy: otherTaxonomy, otherCode: otherCode, relation: '
                 'relation}" target="payload"/>\n'
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
                 2648,
                 '00-contracts/bpmn/ai/gftd/open-cofog/recordConcordance.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-cofog.etzhayyim.com',
                 'did:web:open-cofog.etzhayyim.com',
                 'sys.bpmn.seed.open-cofog',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-concordance-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordExpenditure-v1',
                 'did:web:open-cofog.etzhayyim.com',
                 'ai.gftd.apps.openCofog.recordExpenditure',
                 'open_cofog_record_expenditure',
                 30000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-cofog.etzhayyim.com',
                 'did:web:open-cofog.etzhayyim.com',
                 'sys.bpmn.seed.open-cofog',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordExpenditure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordConcordance-v1',
                 'did:web:open-cofog.etzhayyim.com',
                 'ai.gftd.apps.openCofog.recordConcordance',
                 'open_cofog_record_concordance',
                 15000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-cofog.etzhayyim.com',
                 'did:web:open-cofog.etzhayyim.com',
                 'sys.bpmn.seed.open-cofog',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordConcordance-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordExpenditure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-cofog-recordConcordance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-expenditure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-cofog-record-concordance-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
