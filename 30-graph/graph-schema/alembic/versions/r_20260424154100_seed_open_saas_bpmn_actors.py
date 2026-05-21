"""Captured from Kysely migration 20260424154100_seed_open_saas_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424154100_seed_open_saas_bpmn_actors"
down_revision = 'r_20260424154000_vertex_open_saas'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-register-product-v1',
                 'did:web:open-saas.etzhayyim.com',
                 'open_saas_register_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_saas_register_product"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-saas"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_saas_register_product" name="SaaS product 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Score"/>\n'
                 '\n'
                 '    <!--\n'
                 '      riskScore:\n'
                 '        high   : vendorCountry in {IRN,PRK,RUS,SYR,MMR} OR (soc2=false AND '
                 'iso27001=false)\n'
                 '        medium : exactly one of (soc2, iso27001) true\n'
                 '        low    : soc2=true AND iso27001=true AND gdprCompliant=true\n'
                 '      requireSecurityReview = high OR medium\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Score" name="risk score 計算">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if list '
                 'contains([&quot;IRN&quot;,&quot;PRK&quot;,&quot;RUS&quot;,&quot;SYR&quot;,&quot;MMR&quot;], '
                 'vendorCountry) or (soc2 = false and iso27001 = false) then &quot;high&quot;\n'
                 '                                else if soc2 = true and iso27001 = true and '
                 'gdprCompliant = true then &quot;low&quot;\n'
                 '                                else &quot;medium&quot;" target="riskScore"/>\n'
                 '          <zeebe:output source="=not(soc2 = true and iso27001 = true and '
                 'gdprCompliant = true) or list '
                 'contains([&quot;IRN&quot;,&quot;PRK&quot;,&quot;RUS&quot;,&quot;SYR&quot;,&quot;MMR&quot;], '
                 'vendorCountry)" target="requireSecurityReview"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Score" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="product 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_saas_product&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, product_name: productName,\n'
                 '              vendor_did: vendorDid, vendor_country: vendorCountry,\n'
                 '              homepage: homepage, category: category, pricing_tier: '
                 'pricingTier,\n'
                 '              data_residency: dataResidency, soc2: soc2, iso27001: iso27001,\n'
                 '              gdpr_compliant: gdprCompliant, risk_score: riskScore,\n'
                 '              require_security_review: requireSecurityReview,\n'
                 '              status: &quot;active&quot;, registered_at: registeredAt,\n'
                 '              created_at: string(now()), owner_did: callerDid,\n'
                 '              sensitivity_ord: 1, org_id: vendorDid,\n'
                 '              user_id: callerDid, actor_id: &quot;sys.bpmn.open-saas&quot;\n'
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
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requireSecurityReview = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Auto" sourceRef="Gate" '
                 'targetRef="Task_AuditAuto"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditReview" name="audit '
                 'product.securityReview">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-saas.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSaas.product.securityReview&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, productName: productName, '
                 'vendorDid: vendorDid, riskScore: riskScore}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Review</bpmn:incoming><bpmn:outgoing>Flow_ER</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ER" sourceRef="Task_AuditReview" '
                 'targetRef="End_R"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAuto" name="audit product.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-saas.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSaas.product.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, productName: productName, '
                 'category: category, riskScore: riskScore}" target="payload"/>\n'
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
                 5780,
                 '00-contracts/bpmn/ai/gftd/open-saas/registerProduct.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-saas.etzhayyim.com',
                 'did:web:open-saas.etzhayyim.com',
                 'sys.bpmn.seed.open-saas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-register-product-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-map-to-unspsc-v1',
                 'did:web:open-saas.etzhayyim.com',
                 'open_saas_map_to_unspsc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_saas_map_to_unspsc"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-saas"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_saas_map_to_unspsc" name="SaaS → UNSPSC 対応" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="mapping 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_saas_mapping&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, product_vid: productVid,\n'
                 '              unspsc_code: unspscCode, confidence: confidence,\n'
                 '              mapper_did: mapperDid, status: &quot;active&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid,\n'
                 '              sensitivity_ord: 1, org_id: callerDid,\n'
                 '              user_id: callerDid, actor_id: &quot;sys.bpmn.open-saas&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Edge</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Edge" sourceRef="Task_Save" '
                 'targetRef="Task_Edge"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Edge" name="product → unspsc edge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_saas_product_unspsc&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:unspsc&quot;,\n'
                 '              src_vid: productVid,\n'
                 '              dst_vid: &quot;did:web:unispsc.etzhayyim.com:seg&quot; + '
                 'substring(string(unspscCode),1,2) + &quot;:commodity:c&quot; + '
                 'string(unspscCode),\n'
                 '              role: &quot;mapped_as&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-saas&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Edge</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Edge" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit mapping.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-saas.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openSaas.mapping.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, productVid: productVid, '
                 'unspscCode: unspscCode, confidence: confidence}" target="payload"/>\n'
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
                 3670,
                 '00-contracts/bpmn/ai/gftd/open-saas/mapToUnspsc.bpmn',
                 '2026-04-24T15:30:00Z',
                 'did:web:open-saas.etzhayyim.com',
                 'did:web:open-saas.etzhayyim.com',
                 'sys.bpmn.seed.open-saas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-map-to-unspsc-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-registerProduct-v1',
                 'did:web:open-saas.etzhayyim.com',
                 'ai.gftd.apps.openSaas.registerProduct',
                 'open_saas_register_product',
                 30000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-saas.etzhayyim.com',
                 'did:web:open-saas.etzhayyim.com',
                 'sys.bpmn.seed.open-saas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-registerProduct-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-mapToUnspsc-v1',
                 'did:web:open-saas.etzhayyim.com',
                 'ai.gftd.apps.openSaas.mapToUnspsc',
                 'open_saas_map_to_unspsc',
                 15000,
                 '2026-04-24T15:30:00Z',
                 'did:web:open-saas.etzhayyim.com',
                 'did:web:open-saas.etzhayyim.com',
                 'sys.bpmn.seed.open-saas',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-mapToUnspsc-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-registerProduct-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-saas-mapToUnspsc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-register-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-saas-map-to-unspsc-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
