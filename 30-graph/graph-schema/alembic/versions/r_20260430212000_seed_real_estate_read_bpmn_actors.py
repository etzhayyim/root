"""Captured from Kysely migration 20260430212000_seed_real_estate_read_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430212000_seed_real_estate_read_bpmn_actors"
down_revision = 'r_20260430211100_seed_kami_ketsu_gorilla_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         "        $7, 1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-search-listings-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'real_estate_search_listings',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_search_listings" '
                 'targetNamespace="https://gftd.ai/bpmn/real-estate"><bpmn:process '
                 'id="real_estate_search_listings" name="realEstate searchListings" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.realEstate.searchListings", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="search listings"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="realEstate.searchListings"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1045,
                 '00-contracts/bpmn/ai/gftd/real-estate/searchListings.bpmn',
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-search-listings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), '', 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-search-listings-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'ai.gftd.apps.realEstate.searchListings',
                 'real_estate_search_listings',
                 30000,
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-search-listings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         "        $7, 1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-property-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'real_estate_get_property',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_get_property" '
                 'targetNamespace="https://gftd.ai/bpmn/real-estate"><bpmn:process '
                 'id="real_estate_get_property" name="realEstate getProperty" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.realEstate.getProperty", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get property"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="realEstate.getProperty"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1027,
                 '00-contracts/bpmn/ai/gftd/real-estate/getProperty.bpmn',
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-property-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), '', 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-property-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'ai.gftd.apps.realEstate.getProperty',
                 'real_estate_get_property',
                 30000,
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-property-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         "        $7, 1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-market-stats-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'real_estate_get_market_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_get_market_stats" '
                 'targetNamespace="https://gftd.ai/bpmn/real-estate"><bpmn:process '
                 'id="real_estate_get_market_stats" name="realEstate getMarketStats" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.realEstate.getMarketStats", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get market stats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="realEstate.getMarketStats"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1048,
                 '00-contracts/bpmn/ai/gftd/real-estate/getMarketStats.bpmn',
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-market-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), '', 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-market-stats-v1',
                 'did:web:real-estate.gftd.ai:ops',
                 'ai.gftd.apps.realEstate.getMarketStats',
                 'real_estate_get_market_stats',
                 30000,
                 '2026-04-30T21:20:00+09:00',
                 'did:web:real-estate.gftd.ai:ops',
                 'did:web:real-estate.gftd.ai:ops',
                 'sys.bpmn.seed.real-estate-read',
                 'did:web:real-estate.gftd.ai:ops',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-market-stats-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-search-listings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-search-listings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-property-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-property-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/real-estate-get-market-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/real-estate-get-market-stats-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
