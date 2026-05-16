"""Captured from Kysely migration 20260506280000_seed_rl_aif_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506280000_seed_rl_aif_bpmn"
down_revision = 'r_20260506270000_vertex_rl_aif'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_belief_update', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/rl/rlAifBeliefUpdate.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-belief-update-v1',
                 'did:web:bpmn.gftd.ai',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlAifBeliefUpdate — Phase 1B Active Inference belief update. '
                 'ADR-2604291800.\n'
                 '\n'
                 '  Fires every 1h. For each (actor_did, action_nsid) pair with new '
                 'vertex_rl_step\n'
                 '  rows, computes Bayesian belief update q(s) and Expected Free Energy G(a).\n'
                 '  Writes vertex_rl_aif_belief + vertex_rl_aif_efe.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.rl.aifUpdateBeliefs\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-belief-update-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_aif_belief_update"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_aif_belief_update" name="AIF Belief Update" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.rl.aifUpdateBeliefs", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToUpdate</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToUpdate" sourceRef="Start" '
                 'targetRef="Task_Update"/>\n'
                 '\n'
                 '    <!-- Belief update + EFE computation -->\n'
                 '    <bpmn:serviceTask id="Task_Update" name="update AIF beliefs and EFE">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.aif.update_beliefs" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50"  target="batch_size"/>\n'
                 '          <zeebe:input source="=20"  target="max_actors"/>\n'
                 '          <zeebe:output source="=ok"               target="ok"/>\n'
                 '          <zeebe:output source="=actors_processed" target="actorsProcessed"/>\n'
                 '          <zeebe:output source="=total_beliefs"    target="totalBeliefs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToUpdate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Update" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2445,
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-belief-update-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_belief_update',\n"
         "      'ai.gftd.apps.rl.aifUpdateBeliefs',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-belief-update-v1',
                 'did:web:bpmn.gftd.ai',
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-belief-update-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_learn_model', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/rl/rlAifLearnModel.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-learn-model-v1',
                 'did:web:bpmn.gftd.ai',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlAifLearnModel — Phase 1B Active Inference model learning. '
                 'ADR-2604291800.\n'
                 '\n'
                 '  Fires once per day. For each (actor_did, action_nsid) pair with >= min_steps\n'
                 '  accumulated trajectory steps, performs online Dirichlet update of A_counts\n'
                 '  and B_counts matrices and renormalises A and B.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.rl.aifLearnModel\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-learn-model-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_aif_learn_model"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_aif_learn_model" name="AIF Learn Model" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.rl.aifLearnModel", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: once per day -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1d">\n'
                 '      <bpmn:outgoing>Flow_ToLearn</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1d">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToLearn" sourceRef="Start" '
                 'targetRef="Task_Learn"/>\n'
                 '\n'
                 '    <!-- Dirichlet update of A_counts and B_counts -->\n'
                 '    <bpmn:serviceTask id="Task_Learn" name="learn AIF generative model">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.aif.learn_model" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=20"  target="min_steps"/>\n'
                 '          <zeebe:input source="=20"  target="max_actors"/>\n'
                 '          <zeebe:output source="=ok"             target="ok"/>\n'
                 '          <zeebe:output source="=models_updated" target="modelsUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToLearn</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Learn" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2350,
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-learn-model-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_learn_model',\n"
         "      'ai.gftd.apps.rl.aifLearnModel',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-learn-model-v1',
                 'did:web:bpmn.gftd.ai',
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-learn-model-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-learn-model-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-learn-model-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-aif-belief-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-aif-belief-update-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
