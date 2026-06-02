"""Captured from Kysely migration 20260507240000_seed_rl_aif_attribute_outcomes_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507240000_seed_rl_aif_attribute_outcomes_bpmn"
down_revision = 'r_20260507230100_seed_domain_catalog_and_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_attribute_outcomes', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/com/etzhayyim/rl/rlAifAttributeOutcomes.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/rl-aif-attribute-outcomes-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlAifAttributeOutcomes — Phase 3 causal attribution. ADR-2605061200.\n'
                 '\n'
                 '  Fires every 1h. For each dispatched BPMN action (dispatch_ok=True,\n'
                 '  outcome_step_id IS NULL) finds the nearest vertex_rl_step within a 2h\n'
                 '  window and links both tables bidirectionally:\n'
                 '    vertex_rl_aif_dispatch_log.outcome_step_id  -> vertex_rl_step.vertex_id\n'
                 '    vertex_rl_step.triggered_by_dispatch        -> '
                 'vertex_rl_aif_dispatch_log.vertex_id\n'
                 '\n'
                 '  This closes the RL feedback loop so that _learn_model_for_pair can use\n'
                 '  real causal action->state transitions for B-matrix learning.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.rl.aifAttributeOutcomes\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/rl-aif-attribute-outcomes-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_aif_attribute_outcomes"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_aif_attribute_outcomes" name="AIF Outcome Attribution" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.rl.aifAttributeOutcomes", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToAttribute</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAttribute" sourceRef="Start" '
                 'targetRef="Task_Attribute"/>\n'
                 '\n'
                 '    <!-- Causal attribution: link dispatch -> outcome step -->\n'
                 '    <bpmn:serviceTask id="Task_Attribute" name="attribute outcomes to '
                 'dispatches">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.aif.attribute_outcomes" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50"  target="batch_size"/>\n'
                 '          <zeebe:input source="=2.0" target="window_hours"/>\n'
                 '          <zeebe:output source="=ok"      target="ok"/>\n'
                 '          <zeebe:output source="=linked"  target="linked"/>\n'
                 '          <zeebe:output source="=skipped" target="skipped"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAttribute</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Attribute" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2755,
                 '2026-05-07T23:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/rl-aif-attribute-outcomes-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_aif_attribute_outcomes',\n"
         "      'com.etzhayyim.apps.rl.aifAttributeOutcomes',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-attribute-outcomes-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-07T23:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-attribute-outcomes-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/rl-aif-attribute-outcomes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/rl-aif-attribute-outcomes-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
