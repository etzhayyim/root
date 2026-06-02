"""Captured from Kysely migration 20260427011500_seed_tsukuru_euv_bpmn_actor."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427011500_seed_tsukuru_euv_bpmn_actor"
down_revision = 'r_20260427010000_seed_gov_zaf_official_source_coverage'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 2, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-euv-lithography-manufacturing-flow-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'tsukuru_euv_lithography_manufacturing_flow',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  id="Definitions_tsukuru_euv_lithography_manufacturing_flow"\n'
                 '  targetNamespace="https://etzhayyim.com/bpmn/tsukuru"\n'
                 '  exporter="hand-written"\n'
                 '  exporterVersion="1.0">\n'
                 '  <bpmn:process id="tsukuru_euv_lithography_manufacturing_flow" name="tsukuru '
                 'EUV lithography manufacturing flow" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="EUV flow request">\n'
                 '      <bpmn:outgoing>Flow_Design</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Design" sourceRef="Start" '
                 'targetRef="Task_DesignFlow"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_DesignFlow" name="design EUV manufacturing '
                 'flow">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.euv.designManufacturingFlow&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={ production_order_id: productionOrderId, '
                 'technology_node_nm: technologyNodeNm, wafer_diameter_mm: waferDiameterMm, '
                 'numerical_aperture: numericalAperture, source_power_w: sourcePowerW, '
                 'design_formats: designFormats, supplier_exchange_format: supplierExchangeFormat, '
                 'supplier_did: supplierDid, artifacts: artifacts, requirements: requirements }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=result" target="euvFlow"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Design</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_NormalizeSupplierPackage</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_NormalizeSupplierPackage" '
                 'sourceRef="Task_DesignFlow" targetRef="Task_NormalizeSupplierPackage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_NormalizeSupplierPackage" name="normalize '
                 'supplier CAD/RFQ package">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={ package_id: supplierPackageId, '
                 'production_order_id: productionOrderId, supplier_did: supplierDid, '
                 'exchange_format: supplierExchangeFormat, artifacts: artifacts, requirements: '
                 'requirements, channels: '
                 '[&quot;rfq&quot;,&quot;dfm&quot;,&quot;quotation&quot;,&quot;purchase-order&quot;,&quot;quality-release&quot;] '
                 '}" target="payload"/>\n'
                 '          <zeebe:output source="=result" target="supplierPackage"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_NormalizeSupplierPackage</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_NormalizeSupplierPackage" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit EUV flow audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:tsukuru.etzhayyim.com:industry:isic:c&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;euvLithographyManufacturingFlowDesigned&quot;" target="action"/>\n'
                 '          <zeebe:input source="={ bpmnProcessId: '
                 '&quot;tsukuru_euv_lithography_manufacturing_flow&quot;, flow: euvFlow, '
                 'supplierPackage: supplierPackage }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3982,
                 '00-contracts/bpmn/ai/gftd/tsukuru/euv-lithography-manufacturing-flow.bpmn',
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-euv-lithography-manufacturing-flow-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 2, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-normalize-supplier-exchange-package-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'tsukuru_normalize_supplier_exchange_package',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  id="Definitions_tsukuru_normalize_supplier_exchange_package"\n'
                 '  targetNamespace="https://etzhayyim.com/bpmn/tsukuru"\n'
                 '  exporter="hand-written"\n'
                 '  exporterVersion="1.0">\n'
                 '  <bpmn:process id="tsukuru_normalize_supplier_exchange_package" name="tsukuru '
                 'normalize supplier exchange package" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="supplier exchange request">\n'
                 '      <bpmn:outgoing>Flow_Normalize</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Normalize" sourceRef="Start" '
                 'targetRef="Task_NormalizeSupplierPackage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_NormalizeSupplierPackage" name="normalize '
                 'supplier CAD/RFQ package">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={ package_id: packageId, production_order_id: '
                 'productionOrderId, supplier_did: supplierDid, exchange_format: exchangeFormat, '
                 'artifacts: artifacts, requirements: requirements, channels: channels }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=result" target="supplierPackage"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Normalize</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_NormalizeSupplierPackage" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit supplier exchange audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:tsukuru.etzhayyim.com:industry:isic:c&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supplierExchangePackageNormalized&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ bpmnProcessId: '
                 '&quot;tsukuru_normalize_supplier_exchange_package&quot;, supplierPackage: '
                 'supplierPackage }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2691,
                 '00-contracts/bpmn/ai/gftd/tsukuru/normalize-supplier-exchange-package.bpmn',
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-normalize-supplier-exchange-package-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 2, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-prepare-euv-order-package-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'tsukuru_prepare_euv_order_package',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  id="Definitions_tsukuru_prepare_euv_order_package"\n'
                 '  targetNamespace="https://etzhayyim.com/bpmn/tsukuru"\n'
                 '  exporter="hand-written"\n'
                 '  exporterVersion="1.0">\n'
                 '  <bpmn:process id="tsukuru_prepare_euv_order_package" name="tsukuru prepare EUV '
                 'order package" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="EUV order package request">\n'
                 '      <bpmn:outgoing>Flow_Prepare</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Prepare" sourceRef="Start" '
                 'targetRef="Task_PrepareOrderPackage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PrepareOrderPackage" name="prepare EUV flow and '
                 'supplier package">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.euv.prepareOrderPackage&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={ flow_id: flowId, package_id: packageId, '
                 'production_order_id: productionOrderId, technology_node_nm: technologyNodeNm, '
                 'wafer_diameter_mm: waferDiameterMm, numerical_aperture: numericalAperture, '
                 'source_power_w: sourcePowerW, design_formats: designFormats, '
                 'supplier_exchange_format: supplierExchangeFormat, supplier_did: supplierDid, '
                 'artifacts: artifacts, requirements: requirements, channels: channels }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=result" target="orderPackage"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Prepare</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_PrepareOrderPackage" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit EUV order package audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:tsukuru.etzhayyim.com:industry:isic:c&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;euvOrderPackagePrepared&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ bpmnProcessId: '
                 '&quot;tsukuru_prepare_euv_order_package&quot;, orderPackage: orderPackage }" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2812,
                 '00-contracts/bpmn/ai/gftd/tsukuru/prepare-euv-order-package.bpmn',
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-prepare-euv-order-package-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 2, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-get-euv-implementation-coverage-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'tsukuru_get_euv_implementation_coverage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  id="Definitions_tsukuru_get_euv_implementation_coverage"\n'
                 '  targetNamespace="https://etzhayyim.com/bpmn/tsukuru"\n'
                 '  exporter="hand-written"\n'
                 '  exporterVersion="1.0">\n'
                 '  <bpmn:process id="tsukuru_get_euv_implementation_coverage" name="tsukuru get '
                 'EUV implementation coverage" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="EUV coverage request">\n'
                 '      <bpmn:outgoing>Flow_Report</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Report" sourceRef="Start" '
                 'targetRef="Task_GetCoverage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_GetCoverage" name="get EUV implementation '
                 'coverage">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.euv.getImplementationCoverage&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={}" target="payload"/>\n'
                 '          <zeebe:output source="=result" target="coverageReport"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Report</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_GetCoverage" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit EUV coverage audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:tsukuru.etzhayyim.com:industry:isic:c&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;euvImplementationCoverageReported&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ bpmnProcessId: '
                 '&quot;tsukuru_get_euv_implementation_coverage&quot;, coverageReport: '
                 'coverageReport }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2414,
                 '00-contracts/bpmn/ai/gftd/tsukuru/get-euv-implementation-coverage.bpmn',
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-get-euv-implementation-coverage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 2, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-validate-supplier-exchange-package-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'tsukuru_validate_supplier_exchange_package',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  id="Definitions_tsukuru_validate_supplier_exchange_package"\n'
                 '  targetNamespace="https://etzhayyim.com/bpmn/tsukuru"\n'
                 '  exporter="hand-written"\n'
                 '  exporterVersion="1.0">\n'
                 '  <bpmn:process id="tsukuru_validate_supplier_exchange_package" name="tsukuru '
                 'validate supplier exchange package" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="supplier exchange validation request">\n'
                 '      <bpmn:outgoing>Flow_Validate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Validate" sourceRef="Start" '
                 'targetRef="Task_ValidateSupplierPackage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ValidateSupplierPackage" name="validate supplier '
                 'CAD/RFQ package">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.xrpc.invoke"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:tsukuru.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.tsukuru.supplierExchange.validatePackage&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={ package_id: packageId, production_order_id: '
                 'productionOrderId, supplier_did: supplierDid, exchange_format: exchangeFormat, '
                 'artifacts: artifacts, requirements: requirements, channels: channels }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=result" target="validationReport"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Validate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_ValidateSupplierPackage" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit supplier validation audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:tsukuru.etzhayyim.com:industry:isic:c&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supplierExchangePackageValidated&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ bpmnProcessId: '
                 '&quot;tsukuru_validate_supplier_exchange_package&quot;, validationReport: '
                 'validationReport }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2694,
                 '00-contracts/bpmn/ai/gftd/tsukuru/validate-supplier-exchange-package.bpmn',
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-validate-supplier-exchange-package-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 2, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-designManufacturingFlow-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'com.etzhayyim.apps.tsukuru.euv.designManufacturingFlow',
                 'tsukuru_euv_lithography_manufacturing_flow',
                 30000,
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-designManufacturingFlow-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 2, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-normalizePackage-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage',
                 'tsukuru_normalize_supplier_exchange_package',
                 30000,
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-normalizePackage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 2, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-prepareOrderPackage-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'com.etzhayyim.apps.tsukuru.euv.prepareOrderPackage',
                 'tsukuru_prepare_euv_order_package',
                 30000,
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-prepareOrderPackage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 2, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-getImplementationCoverage-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'com.etzhayyim.apps.tsukuru.euv.getImplementationCoverage',
                 'tsukuru_get_euv_implementation_coverage',
                 30000,
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-getImplementationCoverage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 2, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-validatePackage-v1',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'com.etzhayyim.apps.tsukuru.supplierExchange.validatePackage',
                 'tsukuru_validate_supplier_exchange_package',
                 30000,
                 '2026-04-27T01:15:00Z',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'did:web:tsukuru.etzhayyim.com:industry:isic:c',
                 'sys.bpmn.seed.tsukuru-euv',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-validatePackage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-designManufacturingFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-normalizePackage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-prepareOrderPackage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-euv-getImplementationCoverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-supplierExchange-validatePackage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-euv-lithography-manufacturing-flow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-normalize-supplier-exchange-package-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-prepare-euv-order-package-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-get-euv-implementation-coverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-validate-supplier-exchange-package-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
