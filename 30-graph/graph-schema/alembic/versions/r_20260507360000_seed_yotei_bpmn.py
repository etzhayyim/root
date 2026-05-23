"""Captured from Kysely migration 20260507360000_seed_yotei_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507360000_seed_yotei_bpmn"
down_revision = 'r_20260507250000_seed_belief_noise_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-analyze-schedule-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_analyze_schedule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_analyze_schedule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_analyze_schedule" name="analyzeSchedule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_analyzeSchedule"/>\n'
                 '    <bpmn:serviceTask id="Task_analyzeSchedule" name="analyzeSchedule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.analyzeSchedule" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_analyzeSchedule" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/analyzeSchedule.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-analyze-schedule-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1145,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-analyze-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-analyze-schedule-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.analyzeSchedule',
                 'yotei_analyze_schedule',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-analyze-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-auto-reschedule-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_auto_reschedule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_auto_reschedule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_auto_reschedule" name="autoReschedule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_autoReschedule"/>\n'
                 '    <bpmn:serviceTask id="Task_autoReschedule" name="autoReschedule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.autoReschedule" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_autoReschedule" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/autoReschedule.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-auto-reschedule-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1137,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-auto-reschedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-auto-reschedule-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.autoReschedule',
                 'yotei_auto_reschedule',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-auto-reschedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_cancel_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_cancel_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_cancel_booking" name="cancelBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_cancelBooking"/>\n'
                 '    <bpmn:serviceTask id="Task_cancelBooking" name="cancelBooking">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.cancelBooking" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_cancelBooking" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/cancelBooking.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-booking-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1129,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.cancelBooking',
                 'yotei_cancel_booking',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_cancel_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_cancel_event" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_cancel_event" name="cancelEvent" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_cancelEvent"/>\n'
                 '    <bpmn:serviceTask id="Task_cancelEvent" name="cancelEvent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.cancelEvent" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_cancelEvent" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/cancelEvent.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-event-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1113,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.cancelEvent',
                 'yotei_cancel_event',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-confirm-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_confirm_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_confirm_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_confirm_booking" name="confirmBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_confirmBooking"/>\n'
                 '    <bpmn:serviceTask id="Task_confirmBooking" name="confirmBooking">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.confirmBooking" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_confirmBooking" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/confirmBooking.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-confirm-booking-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1137,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-confirm-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-confirm-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.confirmBooking',
                 'yotei_confirm_booking',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-confirm-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_create_calendar',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_create_calendar" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_create_calendar" name="createCalendar" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createCalendar"/>\n'
                 '    <bpmn:serviceTask id="Task_createCalendar" name="createCalendar">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.createCalendar" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createCalendar" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/createCalendar.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-calendar-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1137,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.createCalendar',
                 'yotei_create_calendar',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_create_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_create_event" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_create_event" name="createEvent" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createEvent"/>\n'
                 '    <bpmn:serviceTask id="Task_createEvent" name="createEvent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.createEvent" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createEvent" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/createEvent.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-event-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1113,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.createEvent',
                 'yotei_create_event',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-delete-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_delete_calendar',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_delete_calendar" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_delete_calendar" name="deleteCalendar" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_deleteCalendar"/>\n'
                 '    <bpmn:serviceTask id="Task_deleteCalendar" name="deleteCalendar">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.deleteCalendar" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_deleteCalendar" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/deleteCalendar.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-delete-calendar-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1137,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-delete-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-delete-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.deleteCalendar',
                 'yotei_delete_calendar',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-delete-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-describe-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_describe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_describe" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_describe" name="describe" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_describe"/>\n'
                 '    <bpmn:serviceTask id="Task_describe" name="describe">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.describe" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_describe" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/describe.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-describe-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1087, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-describe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-describe-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.describe',
                 'yotei_describe',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-describe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_get_availability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_get_availability" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_get_availability" name="getAvailability" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getAvailability"/>\n'
                 '    <bpmn:serviceTask id="Task_getAvailability" name="getAvailability">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.getAvailability" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getAvailability" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/getAvailability.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-availability-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1145,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.getAvailability',
                 'yotei_get_availability',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_get_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_get_booking" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_get_booking" name="getBooking" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getBooking"/>\n'
                 '    <bpmn:serviceTask id="Task_getBooking" name="getBooking">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.getBooking" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getBooking" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/getBooking.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-booking-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1105,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.getBooking',
                 'yotei_get_booking',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_get_calendar',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_get_calendar" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_get_calendar" name="getCalendar" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getCalendar"/>\n'
                 '    <bpmn:serviceTask id="Task_getCalendar" name="getCalendar">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.getCalendar" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getCalendar" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/getCalendar.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-calendar-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1113,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-calendar-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.getCalendar',
                 'yotei_get_calendar',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-calendar-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_get_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_get_event" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_get_event" name="getEvent" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getEvent"/>\n'
                 '    <bpmn:serviceTask id="Task_getEvent" name="getEvent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.getEvent" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getEvent" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/getEvent.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-event-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1089,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.getEvent',
                 'yotei_get_event',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-open-slots-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_get_open_slots',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_get_open_slots" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_get_open_slots" name="getOpenSlots" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getOpenSlots"/>\n'
                 '    <bpmn:serviceTask id="Task_getOpenSlots" name="getOpenSlots">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.getOpenSlots" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getOpenSlots" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/getOpenSlots.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-open-slots-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1123,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-open-slots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-open-slots-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.getOpenSlots',
                 'yotei_get_open_slots',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-open-slots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-health-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_health',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_yotei_health" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_health" name="health" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_health"/>\n'
                 '    <bpmn:serviceTask id="Task_health" name="health">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.health" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_health" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/health.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-health-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1071, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-health-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.health',
                 'yotei_health',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-bookings-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_list_bookings',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_list_bookings" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_list_bookings" name="listBookings" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listBookings"/>\n'
                 '    <bpmn:serviceTask id="Task_listBookings" name="listBookings">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.listBookings" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listBookings" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/listBookings.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-bookings-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1121,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-bookings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-bookings-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.listBookings',
                 'yotei_list_bookings',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-bookings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-calendars-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_list_calendars',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_list_calendars" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_list_calendars" name="listCalendars" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listCalendars"/>\n'
                 '    <bpmn:serviceTask id="Task_listCalendars" name="listCalendars">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.listCalendars" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listCalendars" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/listCalendars.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-calendars-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1129,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-calendars-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-calendars-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.listCalendars',
                 'yotei_list_calendars',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-calendars-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-events-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_list_events',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_list_events" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_list_events" name="listEvents" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listEvents"/>\n'
                 '    <bpmn:serviceTask id="Task_listEvents" name="listEvents">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.listEvents" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listEvents" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/listEvents.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-events-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1105,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-events-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-events-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.listEvents',
                 'yotei_list_events',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-events-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-propose-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_propose_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_propose_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_propose_booking" name="proposeBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_proposeBooking"/>\n'
                 '    <bpmn:serviceTask id="Task_proposeBooking" name="proposeBooking">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.proposeBooking" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_proposeBooking" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/proposeBooking.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-propose-booking-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1137,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-propose-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-propose-booking-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.proposeBooking',
                 'yotei_propose_booking',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-propose-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-remove-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_remove_availability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_remove_availability" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_remove_availability" name="removeAvailability" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_removeAvailability"/>\n'
                 '    <bpmn:serviceTask id="Task_removeAvailability" name="removeAvailability">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.removeAvailability" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_removeAvailability" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/removeAvailability.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-remove-availability-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1169,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-remove-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-remove-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.removeAvailability',
                 'yotei_remove_availability',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-remove-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-set-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_set_availability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_set_availability" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_set_availability" name="setAvailability" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_setAvailability"/>\n'
                 '    <bpmn:serviceTask id="Task_setAvailability" name="setAvailability">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.setAvailability" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_setAvailability" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/setAvailability.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-set-availability-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1145,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-set-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-set-availability-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.setAvailability',
                 'yotei_set_availability',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-set-availability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-suggest-slots-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_suggest_slots',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_suggest_slots" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yotei" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_suggest_slots" name="suggestSlots" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_suggestSlots"/>\n'
                 '    <bpmn:serviceTask id="Task_suggestSlots" name="suggestSlots">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.suggestSlots" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_suggestSlots" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/suggestSlots.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-suggest-slots-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1121,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-suggest-slots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-suggest-slots-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.suggestSlots',
                 'yotei_suggest_slots',
                 '',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-suggest-slots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-update-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'yotei_update_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yotei_update_event" targetNamespace="https://etzhayyim.com/bpmn/yotei" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="yotei_update_event" name="updateEvent" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_updateEvent"/>\n'
                 '    <bpmn:serviceTask id="Task_updateEvent" name="updateEvent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.yotei.updateEvent" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_updateEvent" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/yotei/updateEvent.bpmn',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-update-event-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1113,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-update-event-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-update-event-v1',
                 'did:web:yotei.etzhayyim.com',
                 'ai.gftd.apps.yotei.updateEvent',
                 'yotei_update_event',
                 'vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking',
                 '2026-05-07T00:20:00Z',
                 'did:web:yotei.etzhayyim.com',
                 'did:web:yotei.etzhayyim.com',
                 'sys.bpmn.seed.yotei',
                 'did:web:yotei.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-update-event-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-analyze-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-analyze-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-auto-reschedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-auto-reschedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-cancel-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-cancel-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-confirm-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-confirm-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-create-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-create-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-delete-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-delete-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-describe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-describe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-calendar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-get-open-slots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-get-open-slots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-bookings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-bookings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-calendars-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-calendars-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-list-events-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-list-events-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-propose-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-propose-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-remove-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-remove-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-set-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-set-availability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-suggest-slots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-suggest-slots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yotei-update-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yotei-update-event-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
