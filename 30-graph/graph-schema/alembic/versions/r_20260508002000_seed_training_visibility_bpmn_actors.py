"""Captured from Kysely migration 20260508002000_seed_training_visibility_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508002000_seed_training_visibility_bpmn_actors"
down_revision = 'r_20260508001000_seed_training_query_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-list-snapshots-v1',
                 'did:web:training.etzhayyim.com',
                 'training_list_snapshots',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - listSnapshots query (XRPC '
                 'app.etzhayyim.apps.training.listSnapshots).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Read-only SELECT over vertex_training_dataset_snapshot. Audit omitted.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_list_snapshots"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_list_snapshots" name="training list snapshots" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.training.listSnapshots", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="listSnapshots">\n'
                 '      <bpmn:outgoing>Flow_ToList</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select snapshots">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.list.snapshots"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetName" target="datasetName"/>\n'
                 '          <zeebe:input source="=status" target="status"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=snapshots" target="snapshots"/>\n'
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
                 1965,
                 '00-contracts/bpmn/ai/gftd/training/listSnapshots.bpmn',
                 '2026-05-08T00:20:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training.visibility',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-list-snapshots-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-coverage-v1',
                 'did:web:training.etzhayyim.com',
                 'training_coverage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - coverage query (XRPC app.etzhayyim.apps.training.coverage).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Single-shot summary aggregate. Audit omitted (high-frequency probe).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_coverage"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_coverage" name="training coverage snapshot" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.training.coverage", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="coverage">\n'
                 '      <bpmn:outgoing>Flow_ToSnap</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Coverage" name="aggregate counts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.coverage.snapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=asOf" target="asOf"/>\n'
                 '          <zeebe:output source="=snapshotsCount" target="snapshotsCount"/>\n'
                 '          <zeebe:output source="=datasetSnapshotRows" '
                 'target="datasetSnapshotRows"/>\n'
                 '          <zeebe:output source="=runsTotal" target="runsTotal"/>\n'
                 '          <zeebe:output source="=runsQueued" target="runsQueued"/>\n'
                 '          <zeebe:output source="=runsRunning" target="runsRunning"/>\n'
                 '          <zeebe:output source="=runsDone" target="runsDone"/>\n'
                 '          <zeebe:output source="=runsFailed" target="runsFailed"/>\n'
                 '          <zeebe:output source="=checkpointsTotal" target="checkpointsTotal"/>\n'
                 '          <zeebe:output source="=checkpointsFinal" target="checkpointsFinal"/>\n'
                 '          <zeebe:output source="=checkpointBytesTotal" '
                 'target="checkpointBytesTotal"/>\n'
                 '          <zeebe:output source="=evalsTotal" target="evalsTotal"/>\n'
                 '          <zeebe:output source="=servingActiveCount" '
                 'target="servingActiveCount"/>\n'
                 '          <zeebe:output source="=lastRunStartedAt" target="lastRunStartedAt"/>\n'
                 '          <zeebe:output source="=lastCheckpointAt" target="lastCheckpointAt"/>\n'
                 '          <zeebe:output source="=lastPromotedAt" target="lastPromotedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSnap</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSnap" sourceRef="Start" '
                 'targetRef="Task_Coverage"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Coverage" '
                 'targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2819,
                 '00-contracts/bpmn/ai/gftd/training/coverage.bpmn',
                 '2026-05-08T00:20:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training.visibility',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-coverage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-listSnapshots-v1',
                 'did:web:training.etzhayyim.com',
                 'app.etzhayyim.apps.training.listSnapshots',
                 'training_list_snapshots',
                 15000,
                 '2026-05-08T00:20:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training.visibility',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-listSnapshots-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-coverage-v1',
                 'did:web:training.etzhayyim.com',
                 'app.etzhayyim.apps.training.coverage',
                 'training_coverage',
                 15000,
                 '2026-05-08T00:20:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training.visibility',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-coverage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-listSnapshots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/training-coverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-list-snapshots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/training-coverage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
