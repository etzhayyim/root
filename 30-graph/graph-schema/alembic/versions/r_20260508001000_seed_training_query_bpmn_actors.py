"""Captured from Kysely migration 20260508001000_seed_training_query_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508001000_seed_training_query_bpmn_actors"
down_revision = 'r_20260508000100_seed_training_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-runs-v1',
                 'did:web:training.gftd.ai',
                 'training_list_runs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.gftd.ai - listRuns query (XRPC ai.gftd.apps.training.listRuns).\n'
                 '  ADR-2605070700 + Addendum-of-Addendum.\n'
                 '\n'
                 '  Read-only SELECT over vertex_training_run. Audit step omitted to keep\n'
                 '  vertex_repo_commit clean for high-frequency dashboard probes\n'
                 '  (same convention as shosha.coverage).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_list_runs"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_list_runs" name="training list runs" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.listRuns", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="listRuns">\n'
                 '      <bpmn:outgoing>Flow_ToList</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select runs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.list.runs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=kind" target="kind"/>\n'
                 '          <zeebe:input source="=status" target="status"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=runs" target="runs"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToList</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToList" sourceRef="Start" '
                 'targetRef="Task_List"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_List" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2021,
                 '00-contracts/bpmn/ai/gftd/training/listRuns.bpmn',
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-runs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-checkpoints-v1',
                 'did:web:training.gftd.ai',
                 'training_list_checkpoints',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.gftd.ai - listCheckpoints query (XRPC '
                 'ai.gftd.apps.training.listCheckpoints).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Read-only SELECT over vertex_training_checkpoint. Audit omitted.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_list_checkpoints"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_list_checkpoints" name="training list checkpoints" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.listCheckpoints", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="listCheckpoints">\n'
                 '      <bpmn:outgoing>Flow_ToList</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select checkpoints">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.list.checkpoints"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=onlyFinal" target="onlyFinal"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=checkpoints" target="checkpoints"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToList</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToList" sourceRef="Start" '
                 'targetRef="Task_List"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_List" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1975,
                 '00-contracts/bpmn/ai/gftd/training/listCheckpoints.bpmn',
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-checkpoints-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-serving-v1',
                 'did:web:training.gftd.ai',
                 'training_serving',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.gftd.ai - serving query (XRPC ai.gftd.apps.training.serving).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Read-only SELECT over mv_training_active_serving. Audit omitted.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_serving"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_serving" name="training serving snapshot" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.serving", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="serving">\n'
                 '      <bpmn:outgoing>Flow_ToList</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select active serving">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.list.serving"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=alias" target="alias"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=serving" target="serving"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToList</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToList" sourceRef="Start" '
                 'targetRef="Task_List"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_List" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1796,
                 '00-contracts/bpmn/ai/gftd/training/serving.bpmn',
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-serving-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listRuns-v1',
                 'did:web:training.gftd.ai',
                 'ai.gftd.apps.training.listRuns',
                 'training_list_runs',
                 15000,
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listRuns-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listCheckpoints-v1',
                 'did:web:training.gftd.ai',
                 'ai.gftd.apps.training.listCheckpoints',
                 'training_list_checkpoints',
                 15000,
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listCheckpoints-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-serving-v1',
                 'did:web:training.gftd.ai',
                 'ai.gftd.apps.training.serving',
                 'training_serving',
                 15000,
                 '2026-05-08T00:10:00Z',
                 'did:web:training.gftd.ai',
                 'did:web:training.gftd.ai',
                 'sys.bpmn.seed.training.query',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-serving-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listRuns-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-listCheckpoints-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/training-serving-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-runs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-list-checkpoints-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-serving-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
