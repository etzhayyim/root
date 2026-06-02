"""Captured from Kysely migration 20260507420000_seed_kenkyusha_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507420000_seed_kenkyusha_bpmn"
down_revision = 'r_20260507410000_seed_organizer_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-collect-evidence-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_collect_evidence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_collect_evidence" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_collect_evidence" name="kenkyusha.collectEvidence" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_collectEvidence" />\n'
                 '    <bpmn:serviceTask id="Task_collectEvidence" '
                 'name="kenkyusha.collectEvidence">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.collectEvidence" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_collectEvidence" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/collectEvidence.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-collect-evidence-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-collect-evidence-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.collectEvidence',
                 'kenkyusha_collect_evidence',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-collect-evidence-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-coverage-map-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_coverage_map',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_coverage_map" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_coverage_map" name="kenkyusha.coverageMap" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_coverageMap" />\n'
                 '    <bpmn:serviceTask id="Task_coverageMap" name="kenkyusha.coverageMap">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.coverageMap" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_coverageMap" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/coverageMap.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-coverage-map-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-coverage-map-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.coverageMap',
                 'kenkyusha_coverage_map',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-coverage-map-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-detect-frontiers-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_detect_frontiers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_detect_frontiers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_detect_frontiers" name="kenkyusha.detectFrontiers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_detectFrontiers" />\n'
                 '    <bpmn:serviceTask id="Task_detectFrontiers" '
                 'name="kenkyusha.detectFrontiers">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.detectFrontiers" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_detectFrontiers" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/detectFrontiers.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-detect-frontiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-detect-frontiers-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.detectFrontiers',
                 'kenkyusha_detect_frontiers',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-detect-frontiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-evaluate-hypothesis-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_evaluate_hypothesis',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_evaluate_hypothesis" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_evaluate_hypothesis" '
                 'name="kenkyusha.evaluateHypothesis" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_evaluateHypothesis" />\n'
                 '    <bpmn:serviceTask id="Task_evaluateHypothesis" '
                 'name="kenkyusha.evaluateHypothesis">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.evaluateHypothesis" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_evaluateHypothesis" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1146,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/evaluateHypothesis.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-evaluate-hypothesis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-evaluate-hypothesis-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.evaluateHypothesis',
                 'kenkyusha_evaluate_hypothesis',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-evaluate-hypothesis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-generate-hypothesis-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_generate_hypothesis',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_generate_hypothesis" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_generate_hypothesis" '
                 'name="kenkyusha.generateHypothesis" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_generateHypothesis" />\n'
                 '    <bpmn:serviceTask id="Task_generateHypothesis" '
                 'name="kenkyusha.generateHypothesis">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.generateHypothesis" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_generateHypothesis" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1146,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/generateHypothesis.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-generate-hypothesis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-generate-hypothesis-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.generateHypothesis',
                 'kenkyusha_generate_hypothesis',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-generate-hypothesis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-get-frontier-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_get_frontier',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_get_frontier" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_get_frontier" name="kenkyusha.getFrontier" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getFrontier" />\n'
                 '    <bpmn:serviceTask id="Task_getFrontier" name="kenkyusha.getFrontier">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.getFrontier" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getFrontier" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/getFrontier.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-get-frontier-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-get-frontier-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.getFrontier',
                 'kenkyusha_get_frontier',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-get-frontier-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-disciplines-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_list_disciplines',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_list_disciplines" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_list_disciplines" name="kenkyusha.listDisciplines" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listDisciplines" />\n'
                 '    <bpmn:serviceTask id="Task_listDisciplines" '
                 'name="kenkyusha.listDisciplines">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.listDisciplines" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listDisciplines" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/listDisciplines.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-disciplines-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-disciplines-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.listDisciplines',
                 'kenkyusha_list_disciplines',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-disciplines-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-frontiers-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_list_frontiers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_list_frontiers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_list_frontiers" name="kenkyusha.listFrontiers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listFrontiers" />\n'
                 '    <bpmn:serviceTask id="Task_listFrontiers" name="kenkyusha.listFrontiers">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.listFrontiers" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listFrontiers" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/listFrontiers.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-frontiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-frontiers-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.listFrontiers',
                 'kenkyusha_list_frontiers',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-frontiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-register-dids-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_register_dids" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_register_dids" name="kenkyusha.registerDids" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_registerDids" />\n'
                 '    <bpmn:serviceTask id="Task_registerDids" name="kenkyusha.registerDids">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.registerDids" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_registerDids" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/registerDids.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-register-dids-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-register-dids-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.registerDids',
                 'kenkyusha_register_dids',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-register-dids-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-search-evidence-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_search_evidence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_search_evidence" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_search_evidence" name="kenkyusha.searchEvidence" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_searchEvidence" />\n'
                 '    <bpmn:serviceTask id="Task_searchEvidence" name="kenkyusha.searchEvidence">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.searchEvidence" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_searchEvidence" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1114,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/searchEvidence.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-search-evidence-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-search-evidence-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.searchEvidence',
                 'kenkyusha_search_evidence',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-search-evidence-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-seed-disciplines-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_seed_disciplines',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_seed_disciplines" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_seed_disciplines" name="kenkyusha.seedDisciplines" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_seedDisciplines" />\n'
                 '    <bpmn:serviceTask id="Task_seedDisciplines" '
                 'name="kenkyusha.seedDisciplines">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.seedDisciplines" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_seedDisciplines" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/seedDisciplines.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-seed-disciplines-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-seed-disciplines-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.seedDisciplines',
                 'kenkyusha_seed_disciplines',
                 30000,
                 'vertex_kenkyusha_discipline,vertex_kenkyusha_frontier,vertex_kenkyusha_hypothesis,vertex_kenkyusha_evidence,vertex_kenkyusha_did_registration,edge_kenkyusha_frontier_discipline,edge_kenkyusha_hypothesis_frontier,edge_kenkyusha_evidence_hypothesis',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-seed-disciplines-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-stats-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'kenkyusha_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kenkyusha_stats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kenkyusha">\n'
                 '  <bpmn:process id="kenkyusha_stats" name="kenkyusha.stats" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_stats" />\n'
                 '    <bpmn:serviceTask id="Task_stats" name="kenkyusha.stats">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.kenkyusha.stats" retries="2" '
                 '/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_stats" targetRef="End" '
                 '/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1040,
                 '00-contracts/bpmn/com/etzhayyim/kenkyusha/stats.bpmn',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-stats-v1',
                 'did:web:kenkyusha.etzhayyim.com',
                 'com.etzhayyim.apps.kenkyusha.stats',
                 'kenkyusha_stats',
                 30000,
                 '',
                 '2026-05-07T01:35:00Z',
                 'did:web:kenkyusha.etzhayyim.com',
                 'did:web:kenkyusha.etzhayyim.com',
                 'sys.bpmn.seed.kenkyusha',
                 'did:web:kenkyusha.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-stats-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-collect-evidence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-collect-evidence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-coverage-map-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-coverage-map-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-detect-frontiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-detect-frontiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-evaluate-hypothesis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-evaluate-hypothesis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-generate-hypothesis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-generate-hypothesis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-get-frontier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-get-frontier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-disciplines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-disciplines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-list-frontiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-list-frontiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-search-evidence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-search-evidence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-seed-disciplines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-seed-disciplines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-stats-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
