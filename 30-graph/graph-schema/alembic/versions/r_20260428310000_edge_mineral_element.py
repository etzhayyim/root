"""Captured from Kysely migration 20260428310000_edge_mineral_element."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428310000_edge_mineral_element"
down_revision = 'r_20260428300000_vertex_lei_entity'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_mineral_element (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      mineral_did     VARCHAR NOT NULL,\n'
         '      element_sym     VARCHAR NOT NULL,\n'
         '      element_did     VARCHAR,\n'
         '      mass_pct        FLOAT,\n'
         "      role            VARCHAR DEFAULT 'major',\n"
         '      created_at      VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_mineral_element_mineral\n'
         '      ON edge_mineral_element (mineral_did)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_mineral_element_sym\n'
         '      ON edge_mineral_element (element_sym)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mineral_element_composition AS\n'
         '    SELECT\n'
         '      em.mineral_did,\n'
         '      COUNT(*)                        AS element_count,\n'
         '      MIN(em.created_at)              AS first_edge_at\n'
         '    FROM edge_mineral_element em\n'
         '    GROUP BY em.mineral_did\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '      xml_byte_size, source_path, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         "      'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/science-mineral-seed-v1',\n"
         "      'did:web:bpmn.etzhayyim.com',\n"
         "      'science_mineral_seed',\n"
         '      1,\n'
         '      $1,\n'
         '      $2,\n'
         "      '30-graph/graph-schema/migrations/20260428310000_edge_mineral_element.ts',\n"
         "      'active',\n"
         '      NOW()::VARCHAR,\n'
         '      0,\n'
         "      'bpmn.etzhayyim.com',\n"
         "      'system',\n"
         "      'did:web:bpmn.etzhayyim.com'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def\n'
         "      WHERE bpmn_process_id = 'science_mineral_seed'\n"
         '    )\n'
         '  ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_mineral_seed"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler" exporterVersion="2.0">\n'
                 '  <bpmn:process id="science_mineral_seed" name="Science: IMA Mineral Seed" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 90 days">\n'
                 '      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P90D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" '
                 'targetRef="Task_SeedMinerals"/>\n'
                 '    <bpmn:serviceTask id="Task_SeedMinerals" name="Seed IMA Minerals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="science.mineral.seedIma" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_to_seed</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedMinerals" '
                 'targetRef="End_Done"/>\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 1424]}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_mineral_element_composition', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_mineral_element', 'parameters': []},
 {'sql': '\n'
         "    DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = 'science_mineral_seed'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
