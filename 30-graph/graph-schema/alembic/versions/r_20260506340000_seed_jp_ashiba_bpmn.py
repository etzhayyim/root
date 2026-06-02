"""Captured from Kysely migration 20260506340000_seed_jp_ashiba_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506340000_seed_jp_ashiba_bpmn"
down_revision = 'r_20260506330000_seed_malak_remaining_bpmn'
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
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-cancel-subscription-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_cancel_subscription',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_cancel_subscription" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_cancel_subscription" name="cancelSubscription" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_cancelSubscription"/>\n'
                 '    <bpmn:serviceTask id="Task_cancelSubscription" name="cancelSubscription">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.jpAshiba.cancelSubscription" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_cancelSubscription" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1184,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/cancelSubscription.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-cancel-subscription-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-change-tier-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_change_tier',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_change_tier" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_change_tier" name="changeTier" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_changeTier"/>\n'
                 '    <bpmn:serviceTask id="Task_changeTier" name="changeTier">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.changeTier" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_changeTier" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1120,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/changeTier.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-change-tier-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-check-availability-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_check_availability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_check_availability" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_check_availability" name="checkAvailability" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_checkAvailability"/>\n'
                 '    <bpmn:serviceTask id="Task_checkAvailability" name="checkAvailability">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.jpAshiba.checkAvailability" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_checkAvailability" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1176,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/checkAvailability.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-check-availability-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-confirm-rental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_confirm_rental',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_confirm_rental" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_confirm_rental" name="confirmRental" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_confirmRental"/>\n'
                 '    <bpmn:serviceTask id="Task_confirmRental" name="confirmRental">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.confirmRental" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_confirmRental" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1144,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/confirmRental.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-confirm-rental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-create-quote-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_create_quote',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_create_quote" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_create_quote" name="createQuote" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createQuote"/>\n'
                 '    <bpmn:serviceTask id="Task_createQuote" name="createQuote">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.createQuote" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createQuote" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1128,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/createQuote.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-create-quote-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-extend-rental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_extend_rental',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_extend_rental" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_extend_rental" name="extendRental" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_extendRental"/>\n'
                 '    <bpmn:serviceTask id="Task_extendRental" name="extendRental">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.extendRental" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_extendRental" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1136,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/extendRental.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-extend-rental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-item-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_get_item',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_get_item" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_get_item" name="getItem" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getItem"/>\n'
                 '    <bpmn:serviceTask id="Task_getItem" name="getItem">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.getItem" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getItem" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1096,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/getItem.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-item-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-usage-summary-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_get_usage_summary',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_get_usage_summary" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_get_usage_summary" name="getUsageSummary" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getUsageSummary"/>\n'
                 '    <bpmn:serviceTask id="Task_getUsageSummary" name="getUsageSummary">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.getUsageSummary" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getUsageSummary" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1162,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/getUsageSummary.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-usage-summary-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-list-catalog-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_list_catalog',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_list_catalog" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_list_catalog" name="listCatalog" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listCatalog"/>\n'
                 '    <bpmn:serviceTask id="Task_listCatalog" name="listCatalog">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.listCatalog" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listCatalog" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1128,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/listCatalog.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-list-catalog-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-record-inspection-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_record_inspection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_record_inspection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_record_inspection" name="recordInspection" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_recordInspection"/>\n'
                 '    <bpmn:serviceTask id="Task_recordInspection" name="recordInspection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.recordInspection" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_recordInspection" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1168,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/recordInspection.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-record-inspection-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-report-defect-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_report_defect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_report_defect" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_report_defect" name="reportDefect" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_reportDefect"/>\n'
                 '    <bpmn:serviceTask id="Task_reportDefect" name="reportDefect">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.reportDefect" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_reportDefect" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1136,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/reportDefect.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-report-defect-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-return-rental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_return_rental',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_return_rental" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_return_rental" name="returnRental" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_returnRental"/>\n'
                 '    <bpmn:serviceTask id="Task_returnRental" name="returnRental">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.returnRental" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_returnRental" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1136,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/returnRental.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-return-rental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-schedule-delivery-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_schedule_delivery',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_schedule_delivery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_schedule_delivery" name="scheduleDelivery" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_scheduleDelivery"/>\n'
                 '    <bpmn:serviceTask id="Task_scheduleDelivery" name="scheduleDelivery">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.scheduleDelivery" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_scheduleDelivery" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1168,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/scheduleDelivery.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-schedule-delivery-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-subscribe-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'jp_ashiba_subscribe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_jp_ashiba_subscribe" '
                 'targetNamespace="https://etzhayyim.com/bpmn/jp-ashiba" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="jp_ashiba_subscribe" name="subscribe" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_subscribe"/>\n'
                 '    <bpmn:serviceTask id="Task_subscribe" name="subscribe">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.jpAshiba.subscribe" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_subscribe" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1110,
                 '00-contracts/bpmn/com/etzhayyim/jp-ashiba/subscribe.bpmn',
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-subscribe-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-cancelSubscription-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.cancelSubscription',
                 'jp_ashiba_cancel_subscription',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-cancelSubscription-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-changeTier-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.changeTier',
                 'jp_ashiba_change_tier',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-changeTier-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-checkAvailability-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.checkAvailability',
                 'jp_ashiba_check_availability',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-checkAvailability-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-confirmRental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.confirmRental',
                 'jp_ashiba_confirm_rental',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-confirmRental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-createQuote-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.createQuote',
                 'jp_ashiba_create_quote',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-createQuote-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-extendRental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.extendRental',
                 'jp_ashiba_extend_rental',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-extendRental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getItem-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.getItem',
                 'jp_ashiba_get_item',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getItem-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getUsageSummary-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.getUsageSummary',
                 'jp_ashiba_get_usage_summary',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getUsageSummary-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-listCatalog-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.listCatalog',
                 'jp_ashiba_list_catalog',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-listCatalog-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-recordInspection-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.recordInspection',
                 'jp_ashiba_record_inspection',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-recordInspection-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-reportDefect-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.reportDefect',
                 'jp_ashiba_report_defect',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-reportDefect-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-returnRental-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.returnRental',
                 'jp_ashiba_return_rental',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-returnRental-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-scheduleDelivery-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.scheduleDelivery',
                 'jp_ashiba_schedule_delivery',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-scheduleDelivery-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-subscribe-v1',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'com.etzhayyim.apps.jpAshiba.subscribe',
                 'jp_ashiba_subscribe',
                 30000,
                 '2026-05-06T23:40:00Z',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'did:web:jp-ashiba.etzhayyim.com',
                 'sys.bpmn.seed.jp-ashiba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-subscribe-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-cancelSubscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-changeTier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-checkAvailability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-confirmRental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-createQuote-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-extendRental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getItem-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-getUsageSummary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-listCatalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-recordInspection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-reportDefect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-returnRental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-scheduleDelivery-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/jp-ashiba-subscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-cancel-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-change-tier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-check-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-confirm-rental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-create-quote-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-extend-rental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-get-usage-summary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-list-catalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-record-inspection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-report-defect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-return-rental-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-schedule-delivery-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/jp-ashiba-subscribe-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
