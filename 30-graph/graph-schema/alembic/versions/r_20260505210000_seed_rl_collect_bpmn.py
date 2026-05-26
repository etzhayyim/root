"""Captured from Kysely migration 20260505210000_seed_rl_collect_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505210000_seed_rl_collect_bpmn"
down_revision = 'r_20260505200000_vertex_rl_signal_phase0'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_collect_trajectories', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/rl/rlCollectTrajectories.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-collect-trajectories-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlCollectTrajectories — Phase 0 RL signal accretion. ADR-2604291800.\n'
                 '\n'
                 '  Fires every 1h. Cursor-scans vertex_wellbecoming_event → vertex_rl_step.\n'
                 '  No training. Reward signal collection only.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.rl.collectTrajectories\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-collect-trajectories-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_collect_trajectories"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_collect_trajectories" name="RL Collect Trajectories" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.rl.collectTrajectories", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToCollect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCollect" sourceRef="Start" '
                 'targetRef="Task_Collect"/>\n'
                 '\n'
                 '    <!-- Collect: cursor-scan wellbecoming_event → rl_step -->\n'
                 '    <bpmn:serviceTask id="Task_Collect" name="collect RL trajectories">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.collect.trajectories" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=200" target="batch_size"/>\n'
                 '          <zeebe:output source="=collected"  target="collected"/>\n'
                 '          <zeebe:output source="=skipped"    target="skipped"/>\n'
                 '          <zeebe:output source="=cursor_ts"  target="cursorTs"/>\n'
                 '          <zeebe:output source="=has_more"   target="hasMore"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCollect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Collect" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2380,
                 '2026-05-05T21:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-collect-trajectories-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_collect_trajectories',\n"
         "      'app.etzhayyim.apps.rl.collectTrajectories',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-collect-trajectories-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-05T21:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-collect-trajectories-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/rl-collect-trajectories-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/rl-collect-trajectories-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
