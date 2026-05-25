"""Captured from Kysely migration 20260507740000_seed_graph_sos_intel_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507740000_seed_graph_sos_intel_bpmn"
down_revision = 'r_20260507710000_drop_other_graph_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.graph-sos-intel'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-inventory-tick-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'graphSosIntel_inventoryTick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:camunda="http://camunda.org/schema/1.0/bpmn"\n'
                 '                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '                  id="graph-sos-intel-inventory-tick"\n'
                 '                  targetNamespace="https://etzhayyim.com/bpmn/graph-sos-intel">\n'
                 '  <bpmn:process id="graphSosIntelInventoryTick" name="Graph SoS Intel — '
                 'Inventory Tick (R/PT15M)" isExecutable="true">\n'
                 '    <bpmn:startEvent id="StartEvent_Timer" name="R/PT15M timer">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="f1" sourceRef="StartEvent_Timer" '
                 'targetRef="Task_InventoryCatalog"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_InventoryCatalog" '
                 'name="app.etzhayyim.apps.graphSosIntel.inventoryCatalog"\n'
                 '                      '
                 'camunda:topic="app.etzhayyim.apps.graphSosIntel.inventoryCatalog"/>\n'
                 '    <bpmn:sequenceFlow id="f2" sourceRef="Task_InventoryCatalog" '
                 'targetRef="Task_WriteSnapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteSnapshot" '
                 'name="app.etzhayyim.apps.graphSosIntel.writeSnapshot"\n'
                 '                      '
                 'camunda:topic="app.etzhayyim.apps.graphSosIntel.writeSnapshot"/>\n'
                 '    <bpmn:sequenceFlow id="f3" sourceRef="Task_WriteSnapshot" '
                 'targetRef="Task_DetectFindings"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_DetectFindings" '
                 'name="app.etzhayyim.apps.graphSosIntel.detectFindings"\n'
                 '                      '
                 'camunda:topic="app.etzhayyim.apps.graphSosIntel.detectFindings"/>\n'
                 '    <bpmn:sequenceFlow id="f4" sourceRef="Task_DetectFindings" '
                 'targetRef="EndEvent_Done"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="EndEvent_Done" name="Snapshot written"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1768,
                 '00-contracts/bpmn/ai/gftd/graph-sos-intel/inventory-tick.bpmn',
                 '2026-05-07T09:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-inventory-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.graph-sos-intel'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-inventory-tick-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'graphSosIntel_inventoryTick',
                 'app.etzhayyim.apps.graphSosIntel.inventoryTick',
                 '2026-05-07T09:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-inventory-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.graph-sos-intel'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-briefing-tick-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'graphSosIntel_briefingTick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:camunda="http://camunda.org/schema/1.0/bpmn"\n'
                 '                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '                  id="graph-sos-intel-briefing-tick"\n'
                 '                  targetNamespace="https://etzhayyim.com/bpmn/graph-sos-intel">\n'
                 '  <bpmn:process id="graphSosIntelBriefingTick" name="Graph SoS Intel — Topology '
                 'Briefing (R/PT6H)" isExecutable="true">\n'
                 '    <bpmn:startEvent id="StartEvent_Timer" name="R/PT6H timer">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="f1" sourceRef="StartEvent_Timer" '
                 'targetRef="Task_QuerySnapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_QuerySnapshot" '
                 'name="app.etzhayyim.apps.graphSosIntel.queryLatestSnapshot"\n'
                 '                      '
                 'camunda:topic="app.etzhayyim.apps.graphSosIntel.queryLatestSnapshot"/>\n'
                 '    <bpmn:sequenceFlow id="f2" sourceRef="Task_QuerySnapshot" '
                 'targetRef="Task_GenerateBriefing"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_GenerateBriefing" '
                 'name="app.etzhayyim.apps.graphSosIntel.generateBriefing"\n'
                 '                      '
                 'camunda:topic="app.etzhayyim.apps.graphSosIntel.generateBriefing"/>\n'
                 '    <bpmn:sequenceFlow id="f3" sourceRef="Task_GenerateBriefing" '
                 'targetRef="Task_WriteFinding"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteFinding" '
                 'name="app.etzhayyim.apps.graphSosIntel.writeFinding"\n'
                 '                      camunda:topic="app.etzhayyim.apps.graphSosIntel.writeFinding"/>\n'
                 '    <bpmn:sequenceFlow id="f4" sourceRef="Task_WriteFinding" '
                 'targetRef="EndEvent_Done"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="EndEvent_Done" name="Briefing finding written"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1776,
                 '00-contracts/bpmn/ai/gftd/graph-sos-intel/briefing-tick.bpmn',
                 '2026-05-07T09:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-briefing-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.graph-sos-intel'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-briefing-tick-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'graphSosIntel_briefingTick',
                 'app.etzhayyim.apps.graphSosIntel.briefingTick',
                 '2026-05-07T09:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-briefing-tick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-inventory-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-inventory-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/graph-sos-intel-briefing-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/graph-sos-intel-briefing-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
