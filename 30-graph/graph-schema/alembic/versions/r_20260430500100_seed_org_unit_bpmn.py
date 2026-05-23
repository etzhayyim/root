"""Captured from Kysely migration 20260430500100_seed_org_unit_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430500100_seed_org_unit_bpmn"
down_revision = 'r_20260430500000_vertex_org_unit'
branch_labels = None
depends_on = None

UP = [{'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-register-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_register_org_unit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_register_org_unit"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_register_org_unit" name="Org Unit 登録" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '\n'
                 '    <!-- Compute path/level from parent context and INSERT vertex_org_unit + '
                 'edge -->\n'
                 '    <bpmn:serviceTask id="Task_Register" name="Org Unit 登録">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=lei"              target="lei"/>\n'
                 '          <zeebe:input source="=leiVertexId"      target="leiVertexId"/>\n'
                 '          <zeebe:input source="=orgType"          target="orgType"/>\n'
                 '          <zeebe:input source="=name"             target="name"/>\n'
                 '          <zeebe:input source="=nameEn"           target="nameEn"/>\n'
                 '          <zeebe:input source="=parentOrgVid"     target="parentOrgVid"/>\n'
                 '          <zeebe:input source="=code"             target="code"/>\n'
                 '          <zeebe:input source="=purpose"          target="purpose"/>\n'
                 '          <zeebe:input source="=url"              target="url"/>\n'
                 '          <zeebe:input source="=validFrom"        target="validFrom"/>\n'
                 '          <zeebe:input source="=props"            target="props"/>\n'
                 '          <zeebe:input source="=if dryRun = true then true else false" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok"              target="registerOk"/>\n'
                 '          <zeebe:output source="=vertexId"        target="orgUnitVid"/>\n'
                 '          <zeebe:output source="=code"            target="orgCode"/>\n'
                 '          <zeebe:output source="=path"            target="orgPath"/>\n'
                 '          <zeebe:output source="=level"           target="orgLevel"/>\n'
                 '          <zeebe:output source="=error"           target="registerError"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Register" '
                 'targetRef="GW_Ok"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Ok" default="Flow_Audit">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Err</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Err" sourceRef="GW_Ok" targetRef="End_Err">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=registerOk = '
                 'false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Ok" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit openLei.org.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.org.register&quot;"    '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: orgUnitVid, lei: lei, orgType: '
                 'orgType, path: orgPath, level: orgLevel, dryRun: dryRun}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Ok"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_Ok"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_Err"><bpmn:incoming>Flow_Err</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3938,
                 '00-contracts/bpmn/ai/gftd/open-lei/registerOrgUnit.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-register-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-register-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.registerOrgUnit',
                 'open_lei_register_org_unit',
                 'vertex_org_unit,edge_org_unit_parent',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-register-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-dissolve-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_dissolve_org_unit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_dissolve_org_unit"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_dissolve_org_unit" name="Org Unit 解散" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Dissolve"/>\n'
                 '\n'
                 '    <!-- Mark unit + optional descendant cascade as dissolved -->\n'
                 '    <bpmn:serviceTask id="Task_Dissolve" name="Org Unit 解散">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.dissolve"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=orgUnitVid"   target="orgUnitVid"/>\n'
                 '          <zeebe:input source="=validUntil"   target="validUntil"/>\n'
                 '          <zeebe:input source="=if cascade = false then false else true" '
                 'target="cascade"/>\n'
                 '          <zeebe:input source="=if dryRun = true then true else false"   '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok"          target="dissolveOk"/>\n'
                 '          <zeebe:output source="=dissolved"   target="dissolvedCount"/>\n'
                 '          <zeebe:output source="=validUntil"  target="resolvedValidUntil"/>\n'
                 '          <zeebe:output source="=errors"      target="dissolveErrors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Dissolve" '
                 'targetRef="GW_Ok"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Ok" default="Flow_Audit">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Err</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Err" sourceRef="GW_Ok" targetRef="End_Err">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=dissolveOk = '
                 'false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Ok" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit openLei.org.dissolve">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.org.dissolve&quot;"    '
                 'target="action"/>\n'
                 '          <zeebe:input source="={orgUnitVid: orgUnitVid, dissolved: '
                 'dissolvedCount, validUntil: resolvedValidUntil, dryRun: dryRun}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Ok"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_Ok"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_Err"><bpmn:incoming>Flow_Err</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3257,
                 '00-contracts/bpmn/ai/gftd/open-lei/dissolveOrgUnit.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-dissolve-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-dissolve-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.dissolveOrgUnit',
                 'open_lei_dissolve_org_unit',
                 'vertex_org_unit',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-dissolve-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-move-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_move_org_unit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_move_org_unit"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_move_org_unit" name="Org Unit 移動" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Move"/>\n'
                 '\n'
                 '    <!-- Re-parent org unit; updates materialized path for self + descendants '
                 'atomically -->\n'
                 '    <bpmn:serviceTask id="Task_Move" name="Org Unit 移動">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.move"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=orgUnitVid"           target="orgUnitVid"/>\n'
                 '          <zeebe:input source="=lei"                  target="lei"/>\n'
                 '          <zeebe:input source="=newParentOrgVid"      '
                 'target="newParentOrgVid"/>\n'
                 '          <zeebe:input source="=newParentLeiVertexId" '
                 'target="newParentLeiVertexId"/>\n'
                 '          <zeebe:input source="=if dryRun = true then true else false" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok"      target="moveOk"/>\n'
                 '          <zeebe:output source="=updated" target="updatedCount"/>\n'
                 '          <zeebe:output source="=errors"  target="moveErrors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Move" targetRef="GW_Ok"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Ok" default="Flow_Audit">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Err</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Err" sourceRef="GW_Ok" targetRef="End_Err">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=moveOk = '
                 'false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Ok" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit openLei.org.move">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.org.move&quot;"         '
                 'target="action"/>\n'
                 '          <zeebe:input source="={orgUnitVid: orgUnitVid, lei: lei, updated: '
                 'updatedCount, dryRun: dryRun}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Ok"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_Ok"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_Err"><bpmn:incoming>Flow_Err</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3211,
                 '00-contracts/bpmn/ai/gftd/open-lei/moveOrgUnit.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-move-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-move-org-unit-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.moveOrgUnit',
                 'open_lei_move_org_unit',
                 'vertex_org_unit,edge_org_unit_parent',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-move-org-unit-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-add-org-member-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_add_org_member',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_add_org_member"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_add_org_member" name="Org Member 追加" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Add"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Add" name="Member 追加">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.addMember"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=orgUnitVid" target="orgUnitVid"/>\n'
                 '          <zeebe:input source="=personDid"  target="personDid"/>\n'
                 '          <zeebe:input source="=role"       target="role"/>\n'
                 '          <zeebe:input source="=since"      target="since"/>\n'
                 '          <zeebe:input source="=until"      target="until"/>\n'
                 '          <zeebe:input source="=confidence" target="confidence"/>\n'
                 '          <zeebe:input source="=if dryRun = true then true else false" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok"     target="addOk"/>\n'
                 '          <zeebe:output source="=edgeId" target="memberEdgeId"/>\n'
                 '          <zeebe:output source="=error"  target="addError"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Add" targetRef="GW_Ok"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Ok" default="Flow_Audit">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Err</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Err" sourceRef="GW_Ok" targetRef="End_Err">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=addOk = '
                 'false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Ok" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit openLei.org.addMember">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.etzhayyim.com&quot;"  '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.org.addMember&quot;"     '
                 'target="action"/>\n'
                 '          <zeebe:input source="={orgUnitVid: orgUnitVid, personDid: personDid, '
                 'role: role, edgeId: memberEdgeId, dryRun: dryRun}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Ok"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_Ok"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_Err"><bpmn:incoming>Flow_Err</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3212,
                 '00-contracts/bpmn/ai/gftd/open-lei/addOrgMember.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-add-org-member-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-add-org-member-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.addOrgMember',
                 'open_lei_add_org_member',
                 'edge_org_unit_member',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-add-org-member-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-remove-org-member-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_remove_org_member',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_remove_org_member"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_remove_org_member" name="Org Member 削除" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Remove"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Remove" name="Member 削除">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.removeMember"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=orgUnitVid" target="orgUnitVid"/>\n'
                 '          <zeebe:input source="=personDid"  target="personDid"/>\n'
                 '          <zeebe:input source="=until"      target="until"/>\n'
                 '          <zeebe:input source="=if dryRun = true then true else false" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=ok"    target="removeOk"/>\n'
                 '          <zeebe:output source="=error" target="removeError"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Remove" '
                 'targetRef="GW_Ok"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Ok" default="Flow_Audit">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Err</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Err" sourceRef="GW_Ok" targetRef="End_Err">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=removeOk = '
                 'false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Ok" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit openLei.org.removeMember">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.etzhayyim.com&quot;"    '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.org.removeMember&quot;"    '
                 'target="action"/>\n'
                 '          <zeebe:input source="={orgUnitVid: orgUnitVid, personDid: personDid, '
                 'until: until, dryRun: dryRun}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Ok"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_Ok"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_Err"><bpmn:incoming>Flow_Err</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2972,
                 '00-contracts/bpmn/ai/gftd/open-lei/removeOrgMember.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-remove-org-member-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-remove-org-member-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.removeOrgMember',
                 'open_lei_remove_org_member',
                 'edge_org_unit_member',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-remove-org-member-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-query-org-subtree-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'open_lei_query_org_subtree',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_open_lei_query_org_subtree"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="open_lei_query_org_subtree" name="Org Subtree 検索" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Query"/>\n'
                 '\n'
                 '    <!-- Read-only materialized-path prefix scan; no audit needed -->\n'
                 '    <bpmn:serviceTask id="Task_Query" name="Subtree 検索">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.org.subtree"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=lei"          target="lei"/>\n'
                 '          <zeebe:input source="=rootOrgVid"   target="rootOrgVid"/>\n'
                 '          <zeebe:input source="=orgType"      target="orgType"/>\n'
                 '          <zeebe:input source="=statusFilter" target="statusFilter"/>\n'
                 '          <zeebe:input source="=maxDepth"     target="maxDepth"/>\n'
                 '          <zeebe:input source="=limit"        target="limit"/>\n'
                 '          <zeebe:input source="=offset"       target="offset"/>\n'
                 '          <zeebe:output source="=ok"     target="queryOk"/>\n'
                 '          <zeebe:output source="=units"  target="orgUnits"/>\n'
                 '          <zeebe:output source="=total"  target="totalCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Query" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1841,
                 '00-contracts/bpmn/ai/gftd/open-lei/queryOrgSubtree.bpmn',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-query-org-subtree-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, '
         'write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, '
         'actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000, $5,\n'
         "             'active', $6, 100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-query-org-subtree-v1',
                 'did:web:open-lei.etzhayyim.com',
                 'ai.gftd.apps.openLei.queryOrgSubtree',
                 'open_lei_query_org_subtree',
                 '',
                 '2026-04-30T12:00:00+09:00',
                 'did:web:open-lei.etzhayyim.com',
                 'did:web:open-lei.etzhayyim.com',
                 'sys.bpmn.seed.open-lei',
                 'did:web:open-lei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-query-org-subtree-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-register-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-register-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-dissolve-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-dissolve-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-move-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-move-org-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-add-org-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-add-org-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-remove-org-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-remove-org-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-lei-query-org-subtree-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-lei-query-org-subtree-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
