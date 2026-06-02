"""Captured from Kysely migration 20260507390000_seed_market_appview_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507390000_seed_market_appview_bpmn"
down_revision = 'r_20260507380000_seed_os_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-list-offer-v1',
                 'did:web:market.etzhayyim.com',
                 'market_list_offer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_list_offer" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_list_offer" name="market.listOffer" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listOffer" />\n'
                 '    <bpmn:serviceTask id="Task_listOffer" name="market.listOffer">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.listOffer" retries="2" '
                 '/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listOffer" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/com/etzhayyim/market/listOffer.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-list-offer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-list-offer-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.listOffer',
                 'market_list_offer',
                 30000,
                 '',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-list-offer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-observe-demand-v1',
                 'did:web:market.etzhayyim.com',
                 'market_observe_demand',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_observe_demand" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_observe_demand" name="market.observeDemand" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_observeDemand" />\n'
                 '    <bpmn:serviceTask id="Task_observeDemand" name="market.observeDemand">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.observeDemand" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_observeDemand" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1130,
                 '00-contracts/bpmn/com/etzhayyim/market/observeDemand.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-observe-demand-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-observe-demand-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.observeDemand',
                 'market_observe_demand',
                 30000,
                 'vertex_market_demand_signal',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-observe-demand-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-publish-offer-v1',
                 'did:web:market.etzhayyim.com',
                 'market_publish_offer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_publish_offer" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_publish_offer" name="market.publishOffer" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_publishOffer" />\n'
                 '    <bpmn:serviceTask id="Task_publishOffer" name="market.publishOffer">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.publishOffer" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_publishOffer" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/market/publishOffer.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-publish-offer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-publish-offer-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.publishOffer',
                 'market_publish_offer',
                 30000,
                 'vertex_market_listing',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-publish-offer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-quote-price-v1',
                 'did:web:market.etzhayyim.com',
                 'market_quote_price',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_quote_price" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_quote_price" name="market.quotePrice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_quotePrice" />\n'
                 '    <bpmn:serviceTask id="Task_quotePrice" name="market.quotePrice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.quotePrice" retries="2" '
                 '/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_quotePrice" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/com/etzhayyim/market/quotePrice.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-quote-price-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-quote-price-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.quotePrice',
                 'market_quote_price',
                 30000,
                 '',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-quote-price-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-settle-invoice-v1',
                 'did:web:market.etzhayyim.com',
                 'market_settle_invoice',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_settle_invoice" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_settle_invoice" name="market.settleInvoice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_settleInvoice" />\n'
                 '    <bpmn:serviceTask id="Task_settleInvoice" name="market.settleInvoice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.settleInvoice" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_settleInvoice" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1130,
                 '00-contracts/bpmn/com/etzhayyim/market/settleInvoice.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-settle-invoice-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-settle-invoice-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.settleInvoice',
                 'market_settle_invoice',
                 30000,
                 'vertex_market_settlement',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-settle-invoice-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-well-known-market-v1',
                 'did:web:market.etzhayyim.com',
                 'market_well_known_market',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_market_well_known_market" '
                 'targetNamespace="https://etzhayyim.com/bpmn/market">\n'
                 '  <bpmn:process id="market_well_known_market" name="market.wellKnownMarket" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_wellKnownMarket" />\n'
                 '    <bpmn:serviceTask id="Task_wellKnownMarket" name="market.wellKnownMarket">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.market.wellKnownMarket" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_wellKnownMarket" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1148,
                 '00-contracts/bpmn/com/etzhayyim/market/wellKnownMarket.bpmn',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-well-known-market-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-well-known-market-v1',
                 'did:web:market.etzhayyim.com',
                 'com.etzhayyim.market.wellKnownMarket',
                 'market_well_known_market',
                 30000,
                 '',
                 '2026-05-07T01:05:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-well-known-market-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-list-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-list-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-observe-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-observe-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-publish-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-publish-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-quote-price-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-quote-price-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-settle-invoice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-settle-invoice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/market-well-known-market-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-well-known-market-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
