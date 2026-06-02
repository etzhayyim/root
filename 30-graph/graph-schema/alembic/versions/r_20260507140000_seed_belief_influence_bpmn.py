"""Captured from Kysely migration 20260507140000_seed_belief_influence_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507140000_seed_belief_influence_bpmn"
down_revision = 'r_20260507131500_seed_agent_policy_adaptation_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active', $7,\n"
         '      1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-belief-influence-propagate-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_belief_influence_propagate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.beliefInfluencePropagate — ADR-0098 D-obs.\n'
                 '\n'
                 '  Fires every 1h. Reads mv_attractor_stability_by_agent (q_i) and\n'
                 '  edge_trust_weight (W_ij) to compute per-agent influence_delta:\n'
                 '    influence_delta_i = λ * Σ_j W_ij * (q_j - q_i)\n'
                 '\n'
                 '  Observation-only (D-obs): writes to vertex_belief_influence for\n'
                 '  convergence monitoring. Does NOT feed back into wellbecoming scores.\n'
                 '  mv_belief_convergence tracks convergence_status '
                 "('converged'/'converging'/'active').\n"
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.beliefInfluencePropagate\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-belief-influence-propagate-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_belief_influence_propagate"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_belief_influence_propagate" name="Well-Becoming '
                 'Belief Influence Propagate (D-obs)" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.beliefInfluencePropagate", "version": '
                 '1, "resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h (offset from trust weight update to avoid concurrent RW '
                 'writes) -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToPropagate</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPropagate" sourceRef="Start" '
                 'targetRef="Task_Propagate"/>\n'
                 '\n'
                 '    <!-- Compute influence_delta_i = λ * Σ_j W_ij * (q_j - q_i) per agent -->\n'
                 '    <bpmn:serviceTask id="Task_Propagate" name="propagate Φ influence (D-obs)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.influence.propagate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=0.1"  target="lambda_lr"/>\n'
                 '          <zeebe:input source="=3"    target="min_scored_events"/>\n'
                 '          <zeebe:output source="=agents_processed"    '
                 'target="agentsProcessed"/>\n'
                 '          <zeebe:output source="=rows_written"        target="rowsWritten"/>\n'
                 '          <zeebe:output source="=max_abs_influence"   '
                 'target="maxAbsInfluence"/>\n'
                 '          <zeebe:output source="=mean_abs_influence"  '
                 'target="meanAbsInfluence"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPropagate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Propagate" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2986,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/beliefInfluencePropagate.bpmn',
                 '2026-05-07T12:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-belief-influence-propagate-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-belief-influence-propagate-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
