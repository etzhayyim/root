"""Captured from Kysely migration 20260508000100_seed_training_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508000100_seed_training_bpmn_actors"
down_revision = 'r_20260508000100_seed_chat_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-sft-v1',
                 'did:web:training.etzhayyim.com',
                 'training_run_sft',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - runSft workflow (XRPC ai.gftd.apps.training.runSft).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. train.dataset.snapshot   freeze v_training_text label set into B2 + '
                 'vertex_training_dataset_snapshot\n'
                 '    2. train.sft.run            fine-tune base_model on snapshot, write step '
                 'checkpoints to B2 + vertex_training_checkpoint\n'
                 '    3. train.eval.run           run requested benches against final checkpoint '
                 '(lm-eval-harness)\n'
                 '    4. generic.audit.emit       OCEL trail\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_run_sft"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_run_sft" name="training run sft" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.runSft", "version": 1, "resultTimeoutMs": '
                 '1800000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="runSft">\n'
                 '      <bpmn:outgoing>Flow_ToSnapshot</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Snapshot" name="freeze dataset snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.dataset.snapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetName" target="datasetName"/>\n'
                 '          <zeebe:input source="=datasetLabel" target="datasetLabel"/>\n'
                 '          <zeebe:input source="=datasetRevision" target="datasetRevision"/>\n'
                 '          <zeebe:output source="=snapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:output source="=b2Prefix" target="datasetB2Prefix"/>\n'
                 '          <zeebe:output source="=rowCount" target="datasetRowCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSnapshot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToTrain</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSnapshot" sourceRef="Start" '
                 'targetRef="Task_Snapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Train" name="sft fine-tune on GPU">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.sft.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=baseModel" target="baseModel"/>\n'
                 '          <zeebe:input source="=baseModelRevision" target="baseModelRevision"/>\n'
                 '          <zeebe:input source="=datasetSnapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:input source="=hyperparams" target="hyperparams"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:input source="=seed" target="seed"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=runVertexId" target="runVertexId"/>\n'
                 '          <zeebe:output source="=finalCheckpointId" '
                 'target="finalCheckpointId"/>\n'
                 '          <zeebe:output source="=finalCheckpointVertexId" '
                 'target="finalCheckpointVertexId"/>\n'
                 '          <zeebe:output source="=stepCount" target="stepCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToTrain</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEval</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToTrain" sourceRef="Task_Snapshot" '
                 'targetRef="Task_Train"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Eval" name="eval final checkpoint">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.eval.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=finalCheckpointId" target="checkpointId"/>\n'
                 '          <zeebe:input source="=evalBenches" target="benches"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:output source="=evalSummary" target="evalSummary"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEval</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEval" sourceRef="Task_Train" '
                 'targetRef="Task_Eval"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:training.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.training.runSft&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;datasetSnapshotId&quot;: datasetSnapshotId, &quot;finalCheckpointId&quot;: '
                 'finalCheckpointId }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Eval" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5148,
                 '00-contracts/bpmn/ai/gftd/training/runSft.bpmn',
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-sft-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-lora-v1',
                 'did:web:training.etzhayyim.com',
                 'training_run_lora',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - runLora workflow (XRPC ai.gftd.apps.training.runLora).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Same shape as runSft but emits adapter-only checkpoints (PEFT / LoRA).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_run_lora"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_run_lora" name="training run lora" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.runLora", "version": 1, '
                 '"resultTimeoutMs": 1800000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="runLora">\n'
                 '      <bpmn:outgoing>Flow_ToSnapshot</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Snapshot" name="freeze dataset snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.dataset.snapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetName" target="datasetName"/>\n'
                 '          <zeebe:input source="=datasetLabel" target="datasetLabel"/>\n'
                 '          <zeebe:input source="=datasetRevision" target="datasetRevision"/>\n'
                 '          <zeebe:output source="=snapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:output source="=rowCount" target="datasetRowCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSnapshot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToTrain</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSnapshot" sourceRef="Start" '
                 'targetRef="Task_Snapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Train" name="lora fine-tune on GPU">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.lora.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=baseModel" target="baseModel"/>\n'
                 '          <zeebe:input source="=baseModelRevision" target="baseModelRevision"/>\n'
                 '          <zeebe:input source="=datasetSnapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:input source="=hyperparams" target="hyperparams"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:input source="=seed" target="seed"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=runVertexId" target="runVertexId"/>\n'
                 '          <zeebe:output source="=finalCheckpointId" '
                 'target="finalCheckpointId"/>\n'
                 '          <zeebe:output source="=finalCheckpointVertexId" '
                 'target="finalCheckpointVertexId"/>\n'
                 '          <zeebe:output source="=adapterRank" target="adapterRank"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToTrain</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEval</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToTrain" sourceRef="Task_Snapshot" '
                 'targetRef="Task_Train"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Eval" name="eval adapter">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.eval.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=finalCheckpointId" target="checkpointId"/>\n'
                 '          <zeebe:input source="=evalBenches" target="benches"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:output source="=evalSummary" target="evalSummary"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEval</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEval" sourceRef="Task_Train" '
                 'targetRef="Task_Eval"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:training.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.training.runLora&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;datasetSnapshotId&quot;: datasetSnapshotId, &quot;finalCheckpointId&quot;: '
                 'finalCheckpointId, &quot;adapterRank&quot;: adapterRank }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Eval" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4810,
                 '00-contracts/bpmn/ai/gftd/training/runLora.bpmn',
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-lora-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-distill-v1',
                 'did:web:training.etzhayyim.com',
                 'training_run_distill',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - runDistill workflow (XRPC '
                 'ai.gftd.apps.training.runDistill).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. train.dataset.snapshot   freeze dataset\n'
                 '    2. train.teacher.label      bulk-infer logits via teacher (run | actor DID | '
                 'artifact)\n'
                 '                                writes Hume-style artifact (ADR-2604300135)\n'
                 '    3. train.distill.run        student fine-tune with hard/soft/feature loss\n'
                 '    4. train.eval.run           bench final student\n'
                 '    5. generic.audit.emit\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_run_distill"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_run_distill" name="training run distill" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.runDistill", "version": 1, '
                 '"resultTimeoutMs": 3600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="runDistill">\n'
                 '      <bpmn:outgoing>Flow_ToSnapshot</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Snapshot" name="freeze dataset snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.dataset.snapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetName" target="datasetName"/>\n'
                 '          <zeebe:input source="=datasetLabel" target="datasetLabel"/>\n'
                 '          <zeebe:input source="=datasetRevision" target="datasetRevision"/>\n'
                 '          <zeebe:output source="=snapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:output source="=rowCount" target="datasetRowCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSnapshot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToTeacher</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSnapshot" sourceRef="Start" '
                 'targetRef="Task_Snapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Teacher" name="bulk-infer teacher labels">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.teacher.label"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetSnapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:input source="=teacherKind" target="teacherKind"/>\n'
                 '          <zeebe:input source="=teacherRunId" target="teacherRunId"/>\n'
                 '          <zeebe:input source="=teacherActorDid" target="teacherActorDid"/>\n'
                 '          <zeebe:input source="=teacherArtifactRunId" '
                 'target="teacherArtifactRunId"/>\n'
                 '          <zeebe:input source="=distillMethod" target="distillMethod"/>\n'
                 '          <zeebe:input source="=temperature" target="temperature"/>\n'
                 '          <zeebe:output source="=teacherLabelArtifactRunId" '
                 'target="teacherLabelArtifactRunId"/>\n'
                 '          <zeebe:output source="=teacherLabelB2Uri" '
                 'target="teacherLabelB2Uri"/>\n'
                 '          <zeebe:output source="=labelSampleCount" target="labelSampleCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToTeacher</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToTrain</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToTeacher" sourceRef="Task_Snapshot" '
                 'targetRef="Task_Teacher"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Train" name="student distill on GPU">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.distill.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=studentBaseModel" target="studentBaseModel"/>\n'
                 '          <zeebe:input source="=studentBaseModelRevision" '
                 'target="studentBaseModelRevision"/>\n'
                 '          <zeebe:input source="=datasetSnapshotId" target="datasetSnapshotId"/>\n'
                 '          <zeebe:input source="=teacherLabelArtifactRunId" '
                 'target="teacherLabelArtifactRunId"/>\n'
                 '          <zeebe:input source="=teacherKind" target="teacherKind"/>\n'
                 '          <zeebe:input source="=teacherRunId" target="teacherRunId"/>\n'
                 '          <zeebe:input source="=teacherActorDid" target="teacherActorDid"/>\n'
                 '          <zeebe:input source="=distillMethod" target="distillMethod"/>\n'
                 '          <zeebe:input source="=temperature" target="temperature"/>\n'
                 '          <zeebe:input source="=hyperparams" target="hyperparams"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:input source="=seed" target="seed"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=runVertexId" target="runVertexId"/>\n'
                 '          <zeebe:output source="=finalCheckpointId" '
                 'target="finalCheckpointId"/>\n'
                 '          <zeebe:output source="=finalCheckpointVertexId" '
                 'target="finalCheckpointVertexId"/>\n'
                 '          <zeebe:output source="=distilledFromEdgeId" '
                 'target="distilledFromEdgeId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToTrain</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEval</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToTrain" sourceRef="Task_Teacher" '
                 'targetRef="Task_Train"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Eval" name="eval student">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.eval.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=finalCheckpointId" target="checkpointId"/>\n'
                 '          <zeebe:input source="=evalBenches" target="benches"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:output source="=evalSummary" target="evalSummary"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEval</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEval" sourceRef="Task_Train" '
                 'targetRef="Task_Eval"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:training.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.training.runDistill&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;datasetSnapshotId&quot;: datasetSnapshotId, &quot;teacherKind&quot;: '
                 'teacherKind, &quot;teacherLabelArtifactRunId&quot;: teacherLabelArtifactRunId, '
                 '&quot;finalCheckpointId&quot;: finalCheckpointId }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Eval" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6957,
                 '00-contracts/bpmn/ai/gftd/training/runDistill.bpmn',
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-distill-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-eval-v1',
                 'did:web:training.etzhayyim.com',
                 'training_run_eval',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - runEval workflow (XRPC ai.gftd.apps.training.runEval).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. train.eval.run        run benches against given checkpointId, write '
                 'vertex_training_eval rows\n'
                 '    2. generic.audit.emit\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_run_eval"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_run_eval" name="training run eval" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.runEval", "version": 1, '
                 '"resultTimeoutMs": 600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="runEval">\n'
                 '      <bpmn:outgoing>Flow_ToEval</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Eval" name="run benches">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.eval.run"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=checkpointId" target="checkpointId"/>\n'
                 '          <zeebe:input source="=benches" target="benches"/>\n'
                 '          <zeebe:input source="=evalDatasetName" target="evalDatasetName"/>\n'
                 '          <zeebe:input source="=evalDatasetRevision" '
                 'target="evalDatasetRevision"/>\n'
                 '          <zeebe:input source="=sampleLimit" target="sampleLimit"/>\n'
                 '          <zeebe:input source="=gpuTarget" target="gpuTarget"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=evalCount" target="evalCount"/>\n'
                 '          <zeebe:output source="=evalIds" target="evalIds"/>\n'
                 '          <zeebe:output source="=primaryScores" target="primaryScores"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEval</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEval" sourceRef="Start" '
                 'targetRef="Task_Eval"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:training.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.training.runEval&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;checkpointId&quot;: checkpointId, '
                 '&quot;evalCount&quot;: evalCount, &quot;primaryScores&quot;: primaryScores }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Eval" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3101,
                 '00-contracts/bpmn/ai/gftd/training/runEval.bpmn',
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-eval-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-promote-v1',
                 'did:web:training.etzhayyim.com',
                 'training_promote',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  training.etzhayyim.com - promote workflow (XRPC ai.gftd.apps.training.promote).\n'
                 '  ADR-2605070700.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. train.promote.checkpoint   retire prior active edge for alias, insert new '
                 'active edge\n'
                 '    2. generic.audit.emit\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_training_promote"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/training"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="training_promote" name="training promote" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.training.promote", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="promote">\n'
                 '      <bpmn:outgoing>Flow_ToPromote</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Promote" name="promote checkpoint">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="train.promote.checkpoint"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=checkpointId" target="checkpointId"/>\n'
                 '          <zeebe:input source="=alias" target="alias"/>\n'
                 '          <zeebe:input source="=servingTarget" target="servingTarget"/>\n'
                 '          <zeebe:input source="=promotedBy" target="promotedBy"/>\n'
                 '          <zeebe:input source="=rationale" target="rationale"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=newEdgeId" target="newEdgeId"/>\n'
                 '          <zeebe:output source="=retiredEdgeId" target="retiredEdgeId"/>\n'
                 '          <zeebe:output source="=weightB2Uri" target="weightB2Uri"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPromote</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPromote" sourceRef="Start" '
                 'targetRef="Task_Promote"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:training.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.training.promote&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;alias&quot;: alias, '
                 '&quot;checkpointId&quot;: checkpointId, &quot;newEdgeId&quot;: newEdgeId, '
                 '&quot;retiredEdgeId&quot;: retiredEdgeId }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Promote" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3064,
                 '00-contracts/bpmn/ai/gftd/training/promote.bpmn',
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-promote-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runSft-v1',
                 'did:web:training.etzhayyim.com',
                 'ai.gftd.apps.training.runSft',
                 'training_run_sft',
                 1800000,
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runSft-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runLora-v1',
                 'did:web:training.etzhayyim.com',
                 'ai.gftd.apps.training.runLora',
                 'training_run_lora',
                 1800000,
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runLora-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runDistill-v1',
                 'did:web:training.etzhayyim.com',
                 'ai.gftd.apps.training.runDistill',
                 'training_run_distill',
                 3600000,
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runDistill-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runEval-v1',
                 'did:web:training.etzhayyim.com',
                 'ai.gftd.apps.training.runEval',
                 'training_run_eval',
                 600000,
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runEval-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-promote-v1',
                 'did:web:training.etzhayyim.com',
                 'ai.gftd.apps.training.promote',
                 'training_promote',
                 30000,
                 '2026-05-08T00:01:00Z',
                 'did:web:training.etzhayyim.com',
                 'did:web:training.etzhayyim.com',
                 'sys.bpmn.seed.training',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-promote-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runSft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runLora-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runDistill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runEval-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-promote-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-sft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-lora-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-distill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-eval-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-promote-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
