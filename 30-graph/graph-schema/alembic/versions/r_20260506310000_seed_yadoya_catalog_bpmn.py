"""Captured from Kysely migration 20260506310000_seed_yadoya_catalog_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506310000_seed_yadoya_catalog_bpmn"
down_revision = 'r_20260506300000_seed_resource_flow_project_review_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-search-hotels-v1',
                 'did:web:yadoya.gftd.ai',
                 'yadoya_search_hotels',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yadoya_search_hotels" '
                 'targetNamespace="https://gftd.ai/bpmn/yadoya" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yadoya_search_hotels" name="searchHotels" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Search"/>\n'
                 '    <bpmn:serviceTask id="Task_Search" name="search published hotels">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.yadoya.searchHotels"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=hotels" target="hotels"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Search" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1224,
                 '00-contracts/bpmn/ai/gftd/yadoya/searchHotels.bpmn',
                 '2026-05-06T22:00:00Z',
                 'did:web:yadoya.gftd.ai',
                 'did:web:yadoya.gftd.ai',
                 'sys.bpmn.seed.yadoya-catalog',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-search-hotels-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-list-hotels-v1',
                 'did:web:yadoya.gftd.ai',
                 'yadoya_list_hotels',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yadoya_list_hotels" '
                 'targetNamespace="https://gftd.ai/bpmn/yadoya" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yadoya_list_hotels" name="listHotels" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_List"/>\n'
                 '    <bpmn:serviceTask id="Task_List" name="list published hotels">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.yadoya.listHotels"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=hotels" target="hotels"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '          <zeebe:output source="=offset" target="offset"/>\n'
                 '          <zeebe:output source="=limit" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1324,
                 '00-contracts/bpmn/ai/gftd/yadoya/listHotels.bpmn',
                 '2026-05-06T22:00:00Z',
                 'did:web:yadoya.gftd.ai',
                 'did:web:yadoya.gftd.ai',
                 'sys.bpmn.seed.yadoya-catalog',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-list-hotels-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-searchHotels-v1',
                 'did:web:yadoya.gftd.ai',
                 'ai.gftd.apps.yadoya.searchHotels',
                 'yadoya_search_hotels',
                 30000,
                 '2026-05-06T22:00:00Z',
                 'did:web:yadoya.gftd.ai',
                 'did:web:yadoya.gftd.ai',
                 'sys.bpmn.seed.yadoya-catalog',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-searchHotels-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-listHotels-v1',
                 'did:web:yadoya.gftd.ai',
                 'ai.gftd.apps.yadoya.listHotels',
                 'yadoya_list_hotels',
                 30000,
                 '2026-05-06T22:00:00Z',
                 'did:web:yadoya.gftd.ai',
                 'did:web:yadoya.gftd.ai',
                 'sys.bpmn.seed.yadoya-catalog',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-listHotels-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-searchHotels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/yadoya-listHotels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-search-hotels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-list-hotels-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
