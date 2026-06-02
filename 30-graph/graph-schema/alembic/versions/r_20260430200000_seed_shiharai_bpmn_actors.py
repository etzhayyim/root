"""Captured from Kysely migration 20260430200000_seed_shiharai_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430200000_seed_shiharai_bpmn_actors"
down_revision = 'r_20260430183500_repair_natural_person_cohort_hashes'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-extract-bill-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_extract_bill',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_extract_bill" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_extract_bill" name="shiharai extractBill" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.extractBill", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="extract bill"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.extractBill"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/extractBill.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-extract-bill-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-extractBill-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.extractBill',
                 'shiharai_extract_bill',
                 30000,
                 'vertex_shiharai_bill',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-extractBill-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-pending-bills-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_list_pending_bills',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_list_pending_bills" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_list_pending_bills" name="shiharai listPendingBills" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.listPendingBills", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list pending bills"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.listPendingBills"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1045,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/listPendingBills.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-pending-bills-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listPendingBills-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.listPendingBills',
                 'shiharai_list_pending_bills',
                 30000,
                 '',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listPendingBills-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-prepare-payment-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_prepare_payment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_prepare_payment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_prepare_payment" name="shiharai preparePayment" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.preparePayment", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="prepare payment"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.preparePayment"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1031,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/preparePayment.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-prepare-payment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-preparePayment-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.preparePayment',
                 'shiharai_prepare_payment',
                 120000,
                 'vertex_shiharai_job',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-preparePayment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-confirm-payment-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_confirm_payment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_confirm_payment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_confirm_payment" name="shiharai confirmPayment" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.confirmPayment", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="confirm payment"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.confirmPayment"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1031,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/confirmPayment.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-confirm-payment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-confirmPayment-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.confirmPayment',
                 'shiharai_confirm_payment',
                 120000,
                 'vertex_shiharai_payment',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-confirmPayment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-register-recurring-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_register_recurring',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_register_recurring" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_register_recurring" name="shiharai registerRecurring" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.registerRecurring", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="register recurring"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.registerRecurring"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/registerRecurring.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-register-recurring-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-registerRecurring-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.registerRecurring',
                 'shiharai_register_recurring',
                 120000,
                 'vertex_shiharai_recurring',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-registerRecurring-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-recurring-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_list_recurring',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_list_recurring" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_list_recurring" name="shiharai listRecurring" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.listRecurring", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list recurring"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.listRecurring"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1024,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/listRecurring.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-recurring-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listRecurring-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.listRecurring',
                 'shiharai_list_recurring',
                 30000,
                 '',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listRecurring-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-get-job-status-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'shiharai_get_job_status',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_shiharai_get_job_status" '
                 'targetNamespace="https://etzhayyim.com/bpmn/shiharai"><bpmn:process '
                 'id="shiharai_get_job_status" name="shiharai getJobStatus" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.shiharai.getJobStatus", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get job status"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="shiharai.getJobStatus"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1021,
                 '00-contracts/bpmn/com/etzhayyim/shiharai/getJobStatus.bpmn',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-get-job-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-getJobStatus-v1',
                 'did:web:shiharai.etzhayyim.com',
                 'com.etzhayyim.apps.shiharai.getJobStatus',
                 'shiharai_get_job_status',
                 30000,
                 '',
                 '2026-04-30T20:00:00+09:00',
                 'did:web:shiharai.etzhayyim.com',
                 'did:web:shiharai.etzhayyim.com',
                 'sys.bpmn.seed.shiharai',
                 'did:web:shiharai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-getJobStatus-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-extractBill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-extract-bill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listPendingBills-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-pending-bills-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-preparePayment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-prepare-payment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-confirmPayment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-confirm-payment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-registerRecurring-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-register-recurring-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-listRecurring-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-list-recurring-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shiharai-getJobStatus-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shiharai-get-job-status-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
