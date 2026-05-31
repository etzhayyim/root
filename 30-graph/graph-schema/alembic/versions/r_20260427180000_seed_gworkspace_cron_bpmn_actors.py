"""Captured from Kysely migration 20260427180000_seed_gworkspace_cron_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427180000_seed_gworkspace_cron_bpmn_actors"
down_revision = 'r_20260427170000_seed_flight_offer_cleanup_runs_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_gmail_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="gmail_cron_tick" '
                 'name="gmail cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.gmail.cronTick", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 15 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT15M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/gmail/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/calendar-cron-tick-v1',
                 'did:web:calendar.etzhayyim.com',
                 'calendar_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_calendar_cron_tick" '
                 'targetNamespace="https://etzhayyim.com/bpmn/calendar" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="calendar_cron_tick" name="calendar '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.calendar.cronTick", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 15 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT15M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="calendar.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1301,
                 '00-contracts/bpmn/ai/gftd/calendar/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:calendar.etzhayyim.com',
                 'did:web:calendar.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/calendar-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1',
                 'did:web:contacts.etzhayyim.com',
                 'contacts_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_contacts_cron_tick" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_cron_tick" name="contacts '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.contacts.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1301,
                 '00-contracts/bpmn/ai/gftd/contacts/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1',
                 'did:web:meet.etzhayyim.com',
                 'meet_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_meet_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="meet_cron_tick" '
                 'name="meet cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.meet.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/meet/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1',
                 'did:web:sheets.etzhayyim.com',
                 'sheets_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_sheets_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/sheets" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="sheets_cron_tick" name="sheets cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.sheets.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/sheets/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1',
                 'did:web:slides.etzhayyim.com',
                 'slides_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_slides_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/slides" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="slides_cron_tick" name="slides cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.slides.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/slides/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1',
                 'did:web:tasks.etzhayyim.com',
                 'tasks_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_tasks_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/tasks" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="tasks_cron_tick" '
                 'name="tasks cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.tasks.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/tasks/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1',
                 'did:web:docs.etzhayyim.com',
                 'docs_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_docs_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="docs_cron_tick" '
                 'name="docs cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.docs.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/docs/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1',
                 'did:web:drive.etzhayyim.com',
                 'drive_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_drive_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/drive" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="drive_cron_tick" '
                 'name="drive cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.drive.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/drive/cronTick.bpmn',
                 '2026-04-27T18:00:00Z',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1',
                 'did:web:gmail.etzhayyim.com',
                 'app.etzhayyim.apps.gmail.cronTick',
                 'gmail_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/calendar-cronTick-v1',
                 'did:web:calendar.etzhayyim.com',
                 'app.etzhayyim.apps.calendar.cronTick',
                 'calendar_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:calendar.etzhayyim.com',
                 'did:web:calendar.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/calendar-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1',
                 'did:web:contacts.etzhayyim.com',
                 'app.etzhayyim.apps.contacts.cronTick',
                 'contacts_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/meet-cronTick-v1',
                 'did:web:meet.etzhayyim.com',
                 'app.etzhayyim.apps.meet.cronTick',
                 'meet_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/meet-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1',
                 'did:web:sheets.etzhayyim.com',
                 'app.etzhayyim.apps.sheets.cronTick',
                 'sheets_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/slides-cronTick-v1',
                 'did:web:slides.etzhayyim.com',
                 'app.etzhayyim.apps.slides.cronTick',
                 'slides_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/slides-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1',
                 'did:web:tasks.etzhayyim.com',
                 'app.etzhayyim.apps.tasks.cronTick',
                 'tasks_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/docs-cronTick-v1',
                 'did:web:docs.etzhayyim.com',
                 'app.etzhayyim.apps.docs.cronTick',
                 'docs_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/docs-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.gworkspace_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/drive-cronTick-v1',
                 'did:web:drive.etzhayyim.com',
                 'app.etzhayyim.apps.drive.cronTick',
                 'drive_cron_tick',
                 60000,
                 '2026-04-27T18:00:00Z',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/drive-cronTick-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/calendar-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/meet-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/slides-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/docs-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/drive-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/calendar-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
