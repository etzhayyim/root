"""Captured from Kysely migration 20260429110000_seed_compound_crystal_protein_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429110000_seed_compound_crystal_protein_bpmn"
down_revision = 'r_20260429110000_netintel_bpmn_timer_1min'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        xml_byte_size, source_path, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1,\n'
         "        'did:web:bpmn.etzhayyim.com',\n"
         '        $2,\n'
         '        1,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         "        'active',\n"
         '        NOW()::VARCHAR,\n'
         '        0,\n'
         "        'bpmn.etzhayyim.com',\n"
         "        'system',\n"
         "        'did:web:bpmn.etzhayyim.com'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def\n'
         '        WHERE bpmn_process_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-compound-seed-v1',
                 'science_compound_seed',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_compound_seed"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler" exporterVersion="2.0">\n'
                 '  <bpmn:process id="science_compound_seed" name="Science: PubChem Compound Seed" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 30 days">\n'
                 '      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P30D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" '
                 'targetRef="Task_SeedCompounds"/>\n'
                 '    <bpmn:serviceTask id="Task_SeedCompounds" name="Seed PubChem Compounds">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="science.compound.seedPubchem" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=200" target="batch_size"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_to_seed</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedCompounds" '
                 'targetRef="End_Done"/>\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 1556,
                 '30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts',
                 'science_compound_seed']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        xml_byte_size, source_path, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1,\n'
         "        'did:web:bpmn.etzhayyim.com',\n"
         '        $2,\n'
         '        1,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         "        'active',\n"
         '        NOW()::VARCHAR,\n'
         '        0,\n'
         "        'bpmn.etzhayyim.com',\n"
         "        'system',\n"
         "        'did:web:bpmn.etzhayyim.com'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def\n'
         '        WHERE bpmn_process_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-crystal-seed-v1',
                 'science_crystal_seed',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_crystal_seed"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler" exporterVersion="2.0">\n'
                 '  <bpmn:process id="science_crystal_seed" name="Science: Crystal Structure Seed" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 30 days">\n'
                 '      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P30D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" '
                 'targetRef="Task_SeedCrystal"/>\n'
                 '    <bpmn:serviceTask id="Task_SeedCrystal" name="Seed COD Crystal Structures">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="science.crystal.seedStructures" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50" target="batch_size"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_to_seed</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedCrystal" '
                 'targetRef="End_Done"/>\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 1555,
                 '30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts',
                 'science_crystal_seed']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        xml_byte_size, source_path, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1,\n'
         "        'did:web:bpmn.etzhayyim.com',\n"
         '        $2,\n'
         '        1,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         "        'active',\n"
         '        NOW()::VARCHAR,\n'
         '        0,\n'
         "        'bpmn.etzhayyim.com',\n"
         "        'system',\n"
         "        'did:web:bpmn.etzhayyim.com'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def\n'
         '        WHERE bpmn_process_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-protein-seed-v1',
                 'science_protein_seed',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_protein_seed"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler" exporterVersion="2.0">\n'
                 '  <bpmn:process id="science_protein_seed" name="Science: UniProt Protein Seed" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 7 days">\n'
                 '      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" '
                 'targetRef="Task_SeedProtein"/>\n'
                 '    <bpmn:serviceTask id="Task_SeedProtein" name="Seed UniProt Proteins">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="science.protein.seedUniprot" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=100" target="batch_size"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_to_seed</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedProtein" '
                 'targetRef="End_Done"/>\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 1543,
                 '30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts',
                 'science_protein_seed']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        xml_byte_size, source_path, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1,\n'
         "        'did:web:bpmn.etzhayyim.com',\n"
         '        $2,\n'
         '        1,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         "        'active',\n"
         '        NOW()::VARCHAR,\n'
         '        0,\n'
         "        'bpmn.etzhayyim.com',\n"
         "        'system',\n"
         "        'did:web:bpmn.etzhayyim.com'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def\n'
         '        WHERE bpmn_process_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-link-graph-phase2-v1',
                 'science_link_graph_phase2',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_link_graph_p2"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler" exporterVersion="2.0">\n'
                 '  <bpmn:process id="science_link_graph_phase2" name="Science: KG Link Phase2 '
                 '(Compound+Protein)" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 2 hours">\n'
                 '      <bpmn:outgoing>Flow_to_link</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT2H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_link" sourceRef="Start_Timer" '
                 'targetRef="Task_LinkP2"/>\n'
                 '    <bpmn:serviceTask id="Task_LinkP2" name="Link Compound+Protein NER">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="science.paper.linkGraphPhase2" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;chemistry&quot;" target="domain"/>\n'
                 '          <zeebe:input source="=2" target="max_replan"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_to_link</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_LinkP2" '
                 'targetRef="End_Done"/>\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 1626,
                 '30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts',
                 'science_link_graph_phase2']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = $1\n    ',
  'parameters': ['science_compound_seed']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = $1\n    ',
  'parameters': ['science_crystal_seed']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = $1\n    ',
  'parameters': ['science_protein_seed']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = $1\n    ',
  'parameters': ['science_link_graph_phase2']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
