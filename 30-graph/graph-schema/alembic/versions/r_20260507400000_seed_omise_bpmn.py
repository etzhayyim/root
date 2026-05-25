"""Captured from Kysely migration 20260507400000_seed_omise_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507400000_seed_omise_bpmn"
down_revision = 'r_20260507390000_seed_market_appview_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-accept-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_accept_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_accept_order" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_accept_order" name="omise.acceptOrder" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_acceptOrder" />\n'
                 '    <bpmn:serviceTask id="Task_acceptOrder" name="omise.acceptOrder">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.acceptOrder" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_acceptOrder" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/acceptOrder.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-accept-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-accept-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.acceptOrder',
                 'omise_accept_order',
                 30000,
                 'vertex_OmiseOrder',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-accept-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-add-to-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_add_to_cart',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_add_to_cart" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_add_to_cart" name="omise.addToCart" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_addToCart" />\n'
                 '    <bpmn:serviceTask id="Task_addToCart" name="omise.addToCart">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.addToCart" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_addToCart" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1099,
                 '00-contracts/bpmn/ai/gftd/omise/addToCart.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-add-to-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-add-to-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.addToCart',
                 'omise_add_to_cart',
                 30000,
                 'vertex_OmiseCart',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-add-to-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-apply-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_apply_coupon',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_apply_coupon" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_apply_coupon" name="omise.applyCoupon" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_applyCoupon" />\n'
                 '    <bpmn:serviceTask id="Task_applyCoupon" name="omise.applyCoupon">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.applyCoupon" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_applyCoupon" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/applyCoupon.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-apply-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-apply-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.applyCoupon',
                 'omise_apply_coupon',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-apply-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-approve-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_approve_seller',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_approve_seller" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_approve_seller" name="omise.approveSeller" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_approveSeller" />\n'
                 '    <bpmn:serviceTask id="Task_approveSeller" name="omise.approveSeller">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.approveSeller" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_approveSeller" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/approveSeller.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-approve-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-approve-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.approveSeller',
                 'omise_approve_seller',
                 30000,
                 'vertex_OmiseSeller',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-approve-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-archive-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_archive_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_archive_product" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_archive_product" name="omise.archiveProduct" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_archiveProduct" />\n'
                 '    <bpmn:serviceTask id="Task_archiveProduct" name="omise.archiveProduct">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.archiveProduct" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_archiveProduct" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/omise/archiveProduct.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-archive-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-archive-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.archiveProduct',
                 'omise_archive_product',
                 30000,
                 'vertex_OmiseProduct',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-archive-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-card-home-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_card_home',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_card_home" targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_card_home" name="omise.cardHome" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_cardHome" />\n'
                 '    <bpmn:serviceTask id="Task_cardHome" name="omise.cardHome">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.cardHome" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_cardHome" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/omise/cardHome.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-card-home-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-card-home-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.cardHome',
                 'omise_card_home',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-card-home-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-clear-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_clear_cart',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_clear_cart" targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_clear_cart" name="omise.clearCart" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_clearCart" />\n'
                 '    <bpmn:serviceTask id="Task_clearCart" name="omise.clearCart">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.clearCart" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_clearCart" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1097,
                 '00-contracts/bpmn/ai/gftd/omise/clearCart.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-clear-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-clear-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.clearCart',
                 'omise_clear_cart',
                 30000,
                 'vertex_OmiseCart',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-clear-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_create_coupon',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_create_coupon" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_create_coupon" name="omise.createCoupon" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createCoupon" />\n'
                 '    <bpmn:serviceTask id="Task_createCoupon" name="omise.createCoupon">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.createCoupon" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createCoupon" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/ai/gftd/omise/createCoupon.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.createCoupon',
                 'omise_create_coupon',
                 30000,
                 'vertex_OmiseCoupon',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_create_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_create_order" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_create_order" name="omise.createOrder" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createOrder" />\n'
                 '    <bpmn:serviceTask id="Task_createOrder" name="omise.createOrder">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.createOrder" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createOrder" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/createOrder.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.createOrder',
                 'omise_create_order',
                 30000,
                 'vertex_OmiseOrder,vertex_OmiseCart',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_create_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_create_product" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_create_product" name="omise.createProduct" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createProduct" />\n'
                 '    <bpmn:serviceTask id="Task_createProduct" name="omise.createProduct">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.createProduct" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createProduct" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/createProduct.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.createProduct',
                 'omise_create_product',
                 30000,
                 'vertex_OmiseProduct',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-shipment-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_create_shipment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_create_shipment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_create_shipment" name="omise.createShipment" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createShipment" />\n'
                 '    <bpmn:serviceTask id="Task_createShipment" name="omise.createShipment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.createShipment" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createShipment" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/omise/createShipment.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-shipment-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.createShipment',
                 'omise_create_shipment',
                 30000,
                 'vertex_OmiseShipment',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-deactivate-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_deactivate_coupon',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_deactivate_coupon" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_deactivate_coupon" name="omise.deactivateCoupon" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_deactivateCoupon" />\n'
                 '    <bpmn:serviceTask id="Task_deactivateCoupon" name="omise.deactivateCoupon">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.deactivateCoupon" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_deactivateCoupon" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1153,
                 '00-contracts/bpmn/ai/gftd/omise/deactivateCoupon.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-deactivate-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-deactivate-coupon-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.deactivateCoupon',
                 'omise_deactivate_coupon',
                 30000,
                 'vertex_OmiseCoupon',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-deactivate-coupon-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_cart',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_cart" targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_cart" name="omise.getCart" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getCart" />\n'
                 '    <bpmn:serviceTask id="Task_getCart" name="omise.getCart">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getCart" retries="2" '
                 '/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getCart" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1081,
                 '00-contracts/bpmn/ai/gftd/omise/getCart.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getCart',
                 'omise_get_cart',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_order" targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_order" name="omise.getOrder" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getOrder" />\n'
                 '    <bpmn:serviceTask id="Task_getOrder" name="omise.getOrder">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getOrder" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getOrder" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/omise/getOrder.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getOrder',
                 'omise_get_order',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_product" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_product" name="omise.getProduct" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getProduct" />\n'
                 '    <bpmn:serviceTask id="Task_getProduct" name="omise.getProduct">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getProduct" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getProduct" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1105,
                 '00-contracts/bpmn/ai/gftd/omise/getProduct.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getProduct',
                 'omise_get_product',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-balance-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_seller_balance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_seller_balance" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_seller_balance" name="omise.getSellerBalance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getSellerBalance" />\n'
                 '    <bpmn:serviceTask id="Task_getSellerBalance" name="omise.getSellerBalance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getSellerBalance" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getSellerBalance" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/ai/gftd/omise/getSellerBalance.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-balance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-balance-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getSellerBalance',
                 'omise_get_seller_balance',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-balance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-profile-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_seller_profile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_seller_profile" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_seller_profile" name="omise.getSellerProfile" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getSellerProfile" />\n'
                 '    <bpmn:serviceTask id="Task_getSellerProfile" name="omise.getSellerProfile">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getSellerProfile" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getSellerProfile" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/ai/gftd/omise/getSellerProfile.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-profile-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-profile-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getSellerProfile',
                 'omise_get_seller_profile',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-profile-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-revenue-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_seller_revenue',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_seller_revenue" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_seller_revenue" name="omise.getSellerRevenue" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getSellerRevenue" />\n'
                 '    <bpmn:serviceTask id="Task_getSellerRevenue" name="omise.getSellerRevenue">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getSellerRevenue" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getSellerRevenue" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/ai/gftd/omise/getSellerRevenue.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-revenue-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-revenue-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getSellerRevenue',
                 'omise_get_seller_revenue',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-revenue-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-shipment-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_get_shipment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_get_shipment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_get_shipment" name="omise.getShipment" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getShipment" />\n'
                 '    <bpmn:serviceTask id="Task_getShipment" name="omise.getShipment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.getShipment" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getShipment" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/getShipment.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-shipment-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.getShipment',
                 'omise_get_shipment',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-coupons-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_coupons',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_coupons" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_coupons" name="omise.listCoupons" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listCoupons" />\n'
                 '    <bpmn:serviceTask id="Task_listCoupons" name="omise.listCoupons">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listCoupons" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listCoupons" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/listCoupons.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-coupons-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-coupons-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listCoupons',
                 'omise_list_coupons',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-coupons-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-orders-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_orders',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_orders" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_orders" name="omise.listOrders" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listOrders" />\n'
                 '    <bpmn:serviceTask id="Task_listOrders" name="omise.listOrders">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listOrders" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listOrders" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1105,
                 '00-contracts/bpmn/ai/gftd/omise/listOrders.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-orders-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-orders-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listOrders',
                 'omise_list_orders',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-orders-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-pending-sellers-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_pending_sellers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_pending_sellers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_pending_sellers" name="omise.listPendingSellers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listPendingSellers" />\n'
                 '    <bpmn:serviceTask id="Task_listPendingSellers" '
                 'name="omise.listPendingSellers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listPendingSellers" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listPendingSellers" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1171,
                 '00-contracts/bpmn/ai/gftd/omise/listPendingSellers.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-pending-sellers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-pending-sellers-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listPendingSellers',
                 'omise_list_pending_sellers',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-pending-sellers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-reviews-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_reviews',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_reviews" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_reviews" name="omise.listReviews" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listReviews" />\n'
                 '    <bpmn:serviceTask id="Task_listReviews" name="omise.listReviews">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listReviews" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listReviews" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/listReviews.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-reviews-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-reviews-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listReviews',
                 'omise_list_reviews',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-reviews-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-orders-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_seller_orders',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_seller_orders" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_seller_orders" name="omise.listSellerOrders" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listSellerOrders" />\n'
                 '    <bpmn:serviceTask id="Task_listSellerOrders" name="omise.listSellerOrders">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listSellerOrders" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listSellerOrders" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/ai/gftd/omise/listSellerOrders.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-orders-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-orders-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listSellerOrders',
                 'omise_list_seller_orders',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-orders-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-products-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_seller_products',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_seller_products" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_seller_products" name="omise.listSellerProducts" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listSellerProducts" />\n'
                 '    <bpmn:serviceTask id="Task_listSellerProducts" '
                 'name="omise.listSellerProducts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listSellerProducts" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listSellerProducts" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1171,
                 '00-contracts/bpmn/ai/gftd/omise/listSellerProducts.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-products-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-products-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listSellerProducts',
                 'omise_list_seller_products',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-products-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-sellers-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_sellers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_sellers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_sellers" name="omise.listSellers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listSellers" />\n'
                 '    <bpmn:serviceTask id="Task_listSellers" name="omise.listSellers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listSellers" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listSellers" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/listSellers.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-sellers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-sellers-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listSellers',
                 'omise_list_sellers',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-sellers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-settlements-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_settlements',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_settlements" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_settlements" name="omise.listSettlements" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listSettlements" />\n'
                 '    <bpmn:serviceTask id="Task_listSettlements" name="omise.listSettlements">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listSettlements" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listSettlements" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1145,
                 '00-contracts/bpmn/ai/gftd/omise/listSettlements.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-settlements-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-settlements-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listSettlements',
                 'omise_list_settlements',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-settlements-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-shipments-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_list_shipments',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_list_shipments" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_list_shipments" name="omise.listShipments" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listShipments" />\n'
                 '    <bpmn:serviceTask id="Task_listShipments" name="omise.listShipments">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.listShipments" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listShipments" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/listShipments.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-shipments-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-shipments-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.listShipments',
                 'omise_list_shipments',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-shipments-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-mark-ready-to-ship-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_mark_ready_to_ship',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_mark_ready_to_ship" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_mark_ready_to_ship" name="omise.markReadyToShip" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_markReadyToShip" />\n'
                 '    <bpmn:serviceTask id="Task_markReadyToShip" name="omise.markReadyToShip">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.markReadyToShip" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_markReadyToShip" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1149,
                 '00-contracts/bpmn/ai/gftd/omise/markReadyToShip.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-mark-ready-to-ship-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-mark-ready-to-ship-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.markReadyToShip',
                 'omise_mark_ready_to_ship',
                 30000,
                 'vertex_OmiseOrder',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-mark-ready-to-ship-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-platform-analytics-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_platform_analytics',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_platform_analytics" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_platform_analytics" name="omise.platformAnalytics" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_platformAnalytics" />\n'
                 '    <bpmn:serviceTask id="Task_platformAnalytics" '
                 'name="omise.platformAnalytics">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.platformAnalytics" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_platformAnalytics" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1161,
                 '00-contracts/bpmn/ai/gftd/omise/platformAnalytics.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-platform-analytics-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-platform-analytics-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.platformAnalytics',
                 'omise_platform_analytics',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-platform-analytics-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-register-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_register_seller',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_register_seller" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_register_seller" name="omise.registerSeller" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_registerSeller" />\n'
                 '    <bpmn:serviceTask id="Task_registerSeller" name="omise.registerSeller">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.registerSeller" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_registerSeller" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/omise/registerSeller.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-register-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-register-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.registerSeller',
                 'omise_register_seller',
                 30000,
                 'vertex_OmiseSeller',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-register-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-reject-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_reject_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_reject_order" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_reject_order" name="omise.rejectOrder" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_rejectOrder" />\n'
                 '    <bpmn:serviceTask id="Task_rejectOrder" name="omise.rejectOrder">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.rejectOrder" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_rejectOrder" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/ai/gftd/omise/rejectOrder.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-reject-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-reject-order-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.rejectOrder',
                 'omise_reject_order',
                 30000,
                 'vertex_OmiseOrder',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-reject-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-remove-from-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_remove_from_cart',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_remove_from_cart" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_remove_from_cart" name="omise.removeFromCart" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_removeFromCart" />\n'
                 '    <bpmn:serviceTask id="Task_removeFromCart" name="omise.removeFromCart">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.removeFromCart" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_removeFromCart" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1139,
                 '00-contracts/bpmn/ai/gftd/omise/removeFromCart.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-remove-from-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-remove-from-cart-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.removeFromCart',
                 'omise_remove_from_cart',
                 30000,
                 'vertex_OmiseCart',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-remove-from-cart-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-payout-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_request_payout',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_request_payout" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_request_payout" name="omise.requestPayout" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_requestPayout" />\n'
                 '    <bpmn:serviceTask id="Task_requestPayout" name="omise.requestPayout">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.requestPayout" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_requestPayout" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/requestPayout.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-payout-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-payout-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.requestPayout',
                 'omise_request_payout',
                 30000,
                 'vertex_OmisePayout',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-payout-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-pickup-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_request_pickup',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_request_pickup" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_request_pickup" name="omise.requestPickup" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_requestPickup" />\n'
                 '    <bpmn:serviceTask id="Task_requestPickup" name="omise.requestPickup">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.requestPickup" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_requestPickup" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/requestPickup.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-pickup-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-pickup-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.requestPickup',
                 'omise_request_pickup',
                 30000,
                 'vertex_OmisePickupRequest',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-pickup-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-resolve-dispute-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_resolve_dispute',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_resolve_dispute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_resolve_dispute" name="omise.resolveDispute" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_resolveDispute" />\n'
                 '    <bpmn:serviceTask id="Task_resolveDispute" name="omise.resolveDispute">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.resolveDispute" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_resolveDispute" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/omise/resolveDispute.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-resolve-dispute-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-resolve-dispute-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.resolveDispute',
                 'omise_resolve_dispute',
                 30000,
                 'vertex_OmiseDispute',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-resolve-dispute-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-search-products-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_search_products',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_search_products" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_search_products" name="omise.searchProducts" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_searchProducts" />\n'
                 '    <bpmn:serviceTask id="Task_searchProducts" name="omise.searchProducts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.searchProducts" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_searchProducts" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/omise/searchProducts.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-search-products-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-search-products-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.searchProducts',
                 'omise_search_products',
                 30000,
                 '',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-search-products-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-submit-review-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_submit_review',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_submit_review" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_submit_review" name="omise.submitReview" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_submitReview" />\n'
                 '    <bpmn:serviceTask id="Task_submitReview" name="omise.submitReview">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.submitReview" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_submitReview" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/ai/gftd/omise/submitReview.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-submit-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-submit-review-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.submitReview',
                 'omise_submit_review',
                 30000,
                 'vertex_OmiseReview',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-submit-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-suspend-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_suspend_seller',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_suspend_seller" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_suspend_seller" name="omise.suspendSeller" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_suspendSeller" />\n'
                 '    <bpmn:serviceTask id="Task_suspendSeller" name="omise.suspendSeller">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.suspendSeller" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_suspendSeller" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/suspendSeller.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-suspend-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-suspend-seller-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.suspendSeller',
                 'omise_suspend_seller',
                 30000,
                 'vertex_OmiseSeller',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-suspend-seller-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-inventory-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_update_inventory',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_update_inventory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_update_inventory" name="omise.updateInventory" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_updateInventory" />\n'
                 '    <bpmn:serviceTask id="Task_updateInventory" name="omise.updateInventory">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.updateInventory" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_updateInventory" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1145,
                 '00-contracts/bpmn/ai/gftd/omise/updateInventory.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-inventory-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-inventory-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.updateInventory',
                 'omise_update_inventory',
                 30000,
                 'vertex_OmiseProduct',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-inventory-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_update_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_update_product" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_update_product" name="omise.updateProduct" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_updateProduct" />\n'
                 '    <bpmn:serviceTask id="Task_updateProduct" name="omise.updateProduct">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.updateProduct" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_updateProduct" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/omise/updateProduct.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-product-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.updateProduct',
                 'omise_update_product',
                 30000,
                 'vertex_OmiseProduct',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-product-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-seller-profile-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_update_seller_profile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_update_seller_profile" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_update_seller_profile" '
                 'name="omise.updateSellerProfile" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_updateSellerProfile" />\n'
                 '    <bpmn:serviceTask id="Task_updateSellerProfile" '
                 'name="omise.updateSellerProfile">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.omise.updateSellerProfile" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_updateSellerProfile" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1179,
                 '00-contracts/bpmn/ai/gftd/omise/updateSellerProfile.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-seller-profile-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-seller-profile-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.updateSellerProfile',
                 'omise_update_seller_profile',
                 30000,
                 'vertex_OmiseSeller',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-seller-profile-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-shipment-status-v1',
                 'did:web:omise.etzhayyim.com',
                 'omise_update_shipment_status',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_omise_update_shipment_status" '
                 'targetNamespace="https://etzhayyim.com/bpmn/omise">\n'
                 '  <bpmn:process id="omise_update_shipment_status" '
                 'name="omise.updateShipmentStatus" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_updateShipmentStatus" />\n'
                 '    <bpmn:serviceTask id="Task_updateShipmentStatus" '
                 'name="omise.updateShipmentStatus">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.app.etzhayyim.apps.omise.updateShipmentStatus" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_updateShipmentStatus" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1187,
                 '00-contracts/bpmn/ai/gftd/omise/updateShipmentStatus.bpmn',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-shipment-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-shipment-status-v1',
                 'did:web:omise.etzhayyim.com',
                 'app.etzhayyim.apps.omise.updateShipmentStatus',
                 'omise_update_shipment_status',
                 30000,
                 'vertex_OmiseShipment',
                 '2026-05-07T01:15:00Z',
                 'did:web:omise.etzhayyim.com',
                 'did:web:omise.etzhayyim.com',
                 'sys.bpmn.seed.omise',
                 'did:web:omise.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-shipment-status-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-accept-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-accept-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-add-to-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-add-to-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-apply-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-apply-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-approve-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-approve-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-archive-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-archive-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-card-home-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-card-home-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-clear-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-clear-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-create-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-create-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-deactivate-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-deactivate-coupon-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-balance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-balance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-seller-revenue-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-seller-revenue-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-get-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-get-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-coupons-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-coupons-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-orders-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-orders-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-pending-sellers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-pending-sellers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-reviews-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-reviews-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-orders-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-orders-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-seller-products-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-seller-products-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-sellers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-sellers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-settlements-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-settlements-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-list-shipments-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-list-shipments-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-mark-ready-to-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-mark-ready-to-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-platform-analytics-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-platform-analytics-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-register-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-register-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-reject-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-reject-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-remove-from-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-remove-from-cart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-payout-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-payout-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-request-pickup-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-request-pickup-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-resolve-dispute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-resolve-dispute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-search-products-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-search-products-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-submit-review-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-submit-review-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-suspend-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-suspend-seller-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-product-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-seller-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-seller-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/omise-update-shipment-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/omise-update-shipment-status-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
