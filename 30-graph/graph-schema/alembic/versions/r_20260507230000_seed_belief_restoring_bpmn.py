"""Captured from Kysely migration 20260507230000_seed_belief_restoring_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507230000_seed_belief_restoring_bpmn"
down_revision = 'r_20260507230000_mv_rl_aif_convergence'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         '      $1, $2,\n'
         "      'wellbecoming_belief_restoring_capture', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/wellbecoming/beliefRestoringCapture.bpmn',\n"
         "      'active', $5, 1,\n"
         "      $6, $7, 'sys.bpmn.seed.wellbecoming'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-restoring-capture-v1',
                 'did:web:bpmn.gftd.ai',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.beliefRestoringCapture — ADR-0098 E (γ restoring force).\n'
                 '\n'
                 '  Fires every 1h. Reads mv_attractor_stability_by_agent (q_i) and\n'
                 '  vertex_belief_baseline (q_i^0) to compute per-agent restoring force:\n'
                 '    restoring_delta_i = -γ * (q_i - q_i^0)\n'
                 '\n'
                 '  Baseline q_i^0 is captured on first observation (write-once).\n'
                 '  Writes to vertex_belief_restoring for homeostasis monitoring.\n'
                 '  mv_belief_restoring_summary tracks deviation_status\n'
                 "  ('at_baseline'/'near_baseline'/'drifting') for D-feed gate.\n"
                 '\n'
                 '  NSID: ai.gftd.apps.wellbecoming.beliefRestoringCapture\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-restoring-capture-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_belief_restoring_capture"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_belief_restoring_capture" name="Well-Becoming '
                 'Belief Restoring Capture (γ homeostasis)" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.wellbecoming.beliefRestoringCapture", "version": '
                 '1, "resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToCapture</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCapture" sourceRef="Start" '
                 'targetRef="Task_Capture"/>\n'
                 '\n'
                 '    <!-- Compute restoring_delta_i = -γ * (q_i - q_i^0) per agent -->\n'
                 '    <bpmn:serviceTask id="Task_Capture" name="capture γ restoring force">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.restoring.capture"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=0.05" target="gamma_lr"/>\n'
                 '          <zeebe:input source="=3"    target="min_scored_events"/>\n'
                 '          <zeebe:output source="=agents_processed"    '
                 'target="agentsProcessed"/>\n'
                 '          <zeebe:output source="=rows_written"        target="rowsWritten"/>\n'
                 '          <zeebe:output source="=max_abs_deviation"   '
                 'target="maxAbsDeviation"/>\n'
                 '          <zeebe:output source="=mean_abs_deviation"  '
                 'target="meanAbsDeviation"/>\n'
                 '          <zeebe:output source="=n_new_baselines"     target="nNewBaselines"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCapture</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Capture" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3002,
                 '2026-05-07T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-restoring-capture-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         '      $1, $2,\n'
         "      'wellbecoming_belief_restoring_capture',\n"
         "      'ai.gftd.apps.wellbecoming.beliefRestoringCapture',\n"
         '      $3, 1,\n'
         "      $4, $5, 'sys.bpmn.seed.wellbecoming'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-restoring-capture-v1',
                 'did:web:bpmn.gftd.ai',
                 '2026-05-07T23:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-restoring-capture-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-restoring-capture-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-restoring-capture-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
