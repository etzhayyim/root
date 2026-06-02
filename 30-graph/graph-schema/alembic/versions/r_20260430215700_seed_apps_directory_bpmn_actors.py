"""Captured from Kysely migration 20260430215700_seed_apps_directory_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430215700_seed_apps_directory_bpmn_actors"
down_revision = 'r_20260430215600_vertex_apps_directory_record'
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
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-register-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_register_app_listing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_register_app_listing" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_register_app_listing" name="appsDirectory registerAppListing" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.apps.registerAppListing", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="register app listing"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.registerAppListing"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1080,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/registerAppListing.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-register-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-register-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.registerAppListing',
                 'apps_directory_register_app_listing',
                 'vertex_apps_directory_listing,vertex_apps_directory_feature,vertex_apps_directory_install_intent,edge_apps_directory_listing_feature,edge_apps_directory_listing_install_intent',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-register-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-update-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_update_app_listing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_update_app_listing" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_update_app_listing" name="appsDirectory updateAppListing" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.apps.updateAppListing", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="update app listing"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.updateAppListing"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1068,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/updateAppListing.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-update-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-update-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.updateAppListing',
                 'apps_directory_update_app_listing',
                 'vertex_apps_directory_listing,vertex_apps_directory_feature,vertex_apps_directory_install_intent,edge_apps_directory_listing_feature,edge_apps_directory_listing_install_intent',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-update-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-list-apps-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_list_apps',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_list_apps" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_list_apps" name="appsDirectory listApps" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.apps.listApps", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list apps"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.listApps"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1017,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/listApps.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-list-apps-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-list-apps-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.listApps',
                 'apps_directory_list_apps',
                 '',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-list-apps-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-get-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_get_app_listing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_get_app_listing" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_get_app_listing" name="appsDirectory getAppListing" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.apps.getAppListing", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get app listing"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.getAppListing"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1050,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/getAppListing.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-get-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-get-app-listing-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.getAppListing',
                 'apps_directory_get_app_listing',
                 '',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-get-app-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-feature-app-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_feature_app',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_feature_app" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_feature_app" name="appsDirectory featureApp" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.apps.featureApp", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="feature app"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.featureApp"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1029,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/featureApp.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-feature-app-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-feature-app-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.featureApp',
                 'apps_directory_feature_app',
                 'vertex_apps_directory_listing,vertex_apps_directory_feature,vertex_apps_directory_install_intent,edge_apps_directory_listing_feature,edge_apps_directory_listing_install_intent',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-feature-app-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-record-install-intent-v1',
                 'did:web:apps.etzhayyim.com',
                 'apps_directory_record_install_intent',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_apps_directory_record_install_intent" '
                 'targetNamespace="https://etzhayyim.com/bpmn/appsDirectory"><bpmn:process '
                 'id="apps_directory_record_install_intent" name="appsDirectory '
                 'recordInstallIntent" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.apps.recordInstallIntent", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record install intent"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="appsDirectory.recordInstallIntent"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1086,
                 '00-contracts/bpmn/com/etzhayyim/appsDirectory/recordInstallIntent.bpmn',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-record-install-intent-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-record-install-intent-v1',
                 'did:web:apps.etzhayyim.com',
                 'com.etzhayyim.apps.apps.recordInstallIntent',
                 'apps_directory_record_install_intent',
                 'vertex_apps_directory_listing,vertex_apps_directory_feature,vertex_apps_directory_install_intent,edge_apps_directory_listing_feature,edge_apps_directory_listing_install_intent',
                 '2026-04-30T21:57:00+09:00',
                 'did:web:apps.etzhayyim.com',
                 'did:web:apps.etzhayyim.com',
                 'sys.bpmn.seed.apps-directory',
                 'did:web:apps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-record-install-intent-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-register-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-register-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-update-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-update-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-list-apps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-list-apps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-get-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-get-app-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-feature-app-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-feature-app-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-directory-record-install-intent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-directory-record-install-intent-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
