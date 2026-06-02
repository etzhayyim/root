"""Captured from Kysely migration 20260507120000_seed_trust_weight_update_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507120000_seed_trust_weight_update_bpmn"
down_revision = 'r_20260507110100_vertex_agent_active_inference'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-trust-weight-update-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_trust_weight_update',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.trustWeightUpdate — ADR-0098.\n'
                 '\n'
                 '  Fires every 1h. Reads mv_attractor_stability_by_agent to compute pairwise\n'
                 '  belief distance D(q_i, q_j). Applies Bounded Confidence filter (bc_epsilon)\n'
                 '  and writes W_ij weights to edge_trust_weight.\n'
                 '\n'
                 '  SBGE mapping:\n'
                 '    W_ij = exp(-k * D(q_i, q_j))  if D < bc_epsilon  (information flows)\n'
                 '           0                        if D >= bc_epsilon  (channel blocked)\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.trustWeightUpdate\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-trust-weight-update-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_trust_weight_update"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_trust_weight_update" name="Well-Becoming Trust '
                 'Weight Update" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.trustWeightUpdate", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
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
                 '    <!-- Compute W_ij + apply Bounded Confidence filter -->\n'
                 '    <bpmn:serviceTask id="Task_Update" name="update W_ij trust weights">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.trust.updateWeights"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=0.3"  target="bc_epsilon"/>\n'
                 '          <zeebe:input source="=5.0"  target="weight_k"/>\n'
                 '          <zeebe:input source="=3"    target="min_scored_events"/>\n'
                 '          <zeebe:output source="=agents_found"    target="agentsFound"/>\n'
                 '          <zeebe:output source="=pairs_evaluated" target="pairsEvaluated"/>\n'
                 '          <zeebe:output source="=pairs_blocked"   target="pairsBlocked"/>\n'
                 '          <zeebe:output source="=pairs_updated"   target="pairsUpdated"/>\n'
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
                 2808,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/trustWeightUpdate.bpmn',
                 '2026-05-07T11:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-trust-weight-update-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-trust-weight-update-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
