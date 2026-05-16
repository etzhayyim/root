"""Captured from Kysely migration 20260506210000_seed_rl_generate_preferences_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506210000_seed_rl_generate_preferences_bpmn"
down_revision = 'r_20260506200000_vertex_rl_preference_pair'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_generate_preferences', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/rl/rlGeneratePreferences.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-generate-preferences-v1',
                 'did:web:bpmn.gftd.ai',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlGeneratePreferences — Phase 1 DPO preference pair generation. '
                 'ADR-2604291800.\n'
                 '\n'
                 '  Fires daily (R/P1D). Queries total step count, then conditionally generates\n'
                 '  cross-actor (chosen, rejected) pairs for DPO fine-tuning.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.rl.generatePreferences\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-generate-preferences-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_generate_preferences"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_generate_preferences" name="RL Generate Preferences" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.rl.generatePreferences", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1 day -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1 day">\n'
                 '      <bpmn:outgoing>Flow_ToGenerate</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1d">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGenerate" sourceRef="Start" '
                 'targetRef="Task_Generate"/>\n'
                 '\n'
                 '    <!-- Generate: cross-actor DPO pair generation from vertex_rl_step -->\n'
                 '    <bpmn:serviceTask id="Task_Generate" name="generate DPO preference pairs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.generate.preferences" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50"   target="min_steps"/>\n'
                 '          <zeebe:input source="=0.05" target="delta_threshold"/>\n'
                 '          <zeebe:input source="=500"  target="batch_limit"/>\n'
                 '          <zeebe:output source="=generated"   target="generated"/>\n'
                 '          <zeebe:output source="=skipped"     target="skipped"/>\n'
                 '          <zeebe:output source="=total_steps" target="totalSteps"/>\n'
                 '          <zeebe:output source="=gate_passed" target="gatePassed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToGenerate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Generate" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2568,
                 '2026-05-06T21:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-generate-preferences-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_generate_preferences',\n"
         "      'ai.gftd.apps.rl.generatePreferences',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-generate-preferences-v1',
                 'did:web:bpmn.gftd.ai',
                 '2026-05-06T21:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-generate-preferences-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-generate-preferences-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-generate-preferences-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
