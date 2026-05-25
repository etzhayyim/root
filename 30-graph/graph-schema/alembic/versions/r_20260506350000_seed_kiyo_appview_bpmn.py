"""Captured from Kysely migration 20260506350000_seed_kiyo_appview_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506350000_seed_kiyo_appview_bpmn"
down_revision = 'r_20260506340000_seed_jp_ashiba_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-withdraw-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_withdraw_paper',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_withdraw_paper" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_withdraw_paper" name="withdrawPaper" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_withdrawPaper"/>\n'
                 '    <bpmn:serviceTask id="Task_withdrawPaper" name="withdrawPaper">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.withdrawPaper" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_withdrawPaper" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1125,
                 '00-contracts/bpmn/ai/gftd/kiyo/withdrawPaper.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-withdraw-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-withdraw-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.withdrawPaper',
                 'kiyo_withdraw_paper',
                 30000,
                 'vertex_kiyo_paper,vertex_kiyo_review,edge_kiyo_endorses',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-withdraw-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-add-review-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_add_review',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_add_review" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_add_review" name="addReview" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_addReview"/>\n'
                 '    <bpmn:serviceTask id="Task_addReview" name="addReview">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.addReview" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_addReview" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1093,
                 '00-contracts/bpmn/ai/gftd/kiyo/addReview.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-add-review-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-add-review-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.addReview',
                 'kiyo_add_review',
                 30000,
                 'vertex_kiyo_paper,vertex_kiyo_review,edge_kiyo_endorses',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-add-review-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-endorse-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_endorse_paper',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_endorse_paper" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_endorse_paper" name="endorsePaper" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_endorsePaper"/>\n'
                 '    <bpmn:serviceTask id="Task_endorsePaper" name="endorsePaper">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.endorsePaper" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_endorsePaper" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1117,
                 '00-contracts/bpmn/ai/gftd/kiyo/endorsePaper.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-endorse-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-endorse-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.endorsePaper',
                 'kiyo_endorse_paper',
                 30000,
                 'vertex_kiyo_paper,vertex_kiyo_review,edge_kiyo_endorses',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-endorse-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_get_paper',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_get_paper" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_get_paper" name="getPaper" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getPaper"/>\n'
                 '    <bpmn:serviceTask id="Task_getPaper" name="getPaper">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.getPaper" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getPaper" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1085,
                 '00-contracts/bpmn/ai/gftd/kiyo/getPaper.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.getPaper',
                 'kiyo_get_paper',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-papers-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_list_papers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_list_papers" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_list_papers" name="listPapers" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listPapers"/>\n'
                 '    <bpmn:serviceTask id="Task_listPapers" name="listPapers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.listPapers" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listPapers" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1101,
                 '00-contracts/bpmn/ai/gftd/kiyo/listPapers.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-papers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-papers-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.listPapers',
                 'kiyo_list_papers',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-papers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-search-papers-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_search_papers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_search_papers" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_search_papers" name="searchPapers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_searchPapers"/>\n'
                 '    <bpmn:serviceTask id="Task_searchPapers" name="searchPapers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.searchPapers" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_searchPapers" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1117,
                 '00-contracts/bpmn/ai/gftd/kiyo/searchPapers.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-search-papers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-search-papers-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.searchPapers',
                 'kiyo_search_papers',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-search-papers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-file-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_get_paper_file',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_get_paper_file" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_get_paper_file" name="getPaperFile" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getPaperFile"/>\n'
                 '    <bpmn:serviceTask id="Task_getPaperFile" name="getPaperFile">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.getPaperFile" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getPaperFile" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/ai/gftd/kiyo/getPaperFile.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-file-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-file-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.getPaperFile',
                 'kiyo_get_paper_file',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-file-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-by-author-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_list_by_author',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_list_by_author" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_list_by_author" name="listByAuthor" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listByAuthor"/>\n'
                 '    <bpmn:serviceTask id="Task_listByAuthor" name="listByAuthor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.listByAuthor" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listByAuthor" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/ai/gftd/kiyo/listByAuthor.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-by-author-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-by-author-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.listByAuthor',
                 'kiyo_list_by_author',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-by-author-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-citation-graph-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_get_citation_graph',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_get_citation_graph" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kiyo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_get_citation_graph" name="getCitationGraph" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getCitationGraph"/>\n'
                 '    <bpmn:serviceTask id="Task_getCitationGraph" name="getCitationGraph">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.getCitationGraph" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getCitationGraph" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1151,
                 '00-contracts/bpmn/ai/gftd/kiyo/getCitationGraph.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-citation-graph-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-citation-graph-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.getCitationGraph',
                 'kiyo_get_citation_graph',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-citation-graph-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-stats-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_get_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kiyo_get_stats" targetNamespace="https://etzhayyim.com/bpmn/kiyo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kiyo_get_stats" name="getStats" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getStats"/>\n'
                 '    <bpmn:serviceTask id="Task_getStats" name="getStats">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kiyo.getStats" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getStats" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1085,
                 '00-contracts/bpmn/ai/gftd/kiyo/getStats.bpmn',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-stats-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'app.etzhayyim.apps.kiyo.getStats',
                 'kiyo_get_stats',
                 30000,
                 '',
                 '2026-05-06T23:50:00Z',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo-appview',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-stats-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-withdraw-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-withdraw-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-add-review-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-add-review-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-endorse-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-endorse-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-papers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-papers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-search-papers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-search-papers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-paper-file-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-paper-file-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-list-by-author-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-list-by-author-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-citation-graph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-citation-graph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kiyo-get-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kiyo-get-stats-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
