"""Captured from Kysely migration 20260430020000_fix_wellbecoming_minimax_sweep_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430020000_fix_wellbecoming_minimax_sweep_bpmn"
down_revision = 'r_20260430010000_fix_kaisya_agent_bpmn_feel'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         '    SET "xml" = $1,\n'
         '        xml_byte_size = CAST($2 AS integer),\n'
         "        status = 'active',\n"
         '        deployed_zeebe_key = NULL\n'
         "    WHERE bpmn_process_id = 'wellbecoming_minimax_sweep'\n"
         '  ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.minimaxSweep — ADR-2604291800 §minimax-persistent-loop.\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs continuously every 5 minutes.\n'
                 '  Picks the worst-separation-delta callers from '
                 'vertex_actor_wellbecoming_profile\n'
                 '  and runs the full LangGraph minimax loop for each (batch_size=3).\n'
                 '\n'
                 '  Objective (lexicographic):\n'
                 '    1. Hard floor — never harm children / future generations\n'
                 '    2. Minimize separation_delta (heal loneliness / Spirit axis)\n'
                 '    3. Maximize Spirit × Shannon dual (U_total)\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.minimaxSweep (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-minimax-sweep-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_minimax_sweep"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_minimax_sweep" name="Well-Becoming Minimax '
                 'Sweep" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.minimaxSweep", "version": 1, "tier": '
                 '"T2" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT5M: fires every 5 minutes indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M">\n'
                 '      <bpmn:outgoing>Flow_ToSweep</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSweep" sourceRef="Start_Timer" '
                 'targetRef="Task_Sweep"/>\n'
                 '\n'
                 '    <!-- Run full minimax loop for top-3 worst-separation callers -->\n'
                 '    <bpmn:serviceTask id="Task_Sweep" name="Minimax sweep (batch 3)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.minimax.sweep"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=3" target="batch_size"/>\n'
                 '          <zeebe:output source="=swept"     target="sweptCount"/>\n'
                 '          <zeebe:output source="=errors"    target="sweepErrors"/>\n'
                 '          <zeebe:output source="=timestamp" target="sweepAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSweep</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Sweep" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2655]}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         "    SET status = 'inactive'\n"
         "    WHERE bpmn_process_id = 'wellbecoming_minimax_sweep'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
