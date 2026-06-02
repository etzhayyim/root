"""Captured from Kysely migration 20260430216400_seed_maps_collection_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430216400_seed_maps_collection_bpmn_actors"
down_revision = 'r_20260430216300_seed_port_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-source-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_registerSource',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_registerSource" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_registerSource" name="maps_collection_registerSource" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerSource", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerSource"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.registerSource"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/registerSource.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-source-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-source-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerSource',
                 'maps_collection_registerSource',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-source-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sources-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_listSources',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_listSources" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_listSources" name="maps_collection_listSources" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listSources", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSources"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.listSources"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1028,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/listSources.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sources-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSources',
                 'maps_collection_listSources',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-create-collection-job-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_createCollectionJob',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_createCollectionJob" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_createCollectionJob" '
                 'name="maps_collection_createCollectionJob" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.createCollectionJob", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sourceId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="createCollectionJob"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.createCollectionJob"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1108,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/createCollectionJob.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-create-collection-job-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-create-collection-job-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.createCollectionJob',
                 'maps_collection_createCollectionJob',
                 'vertex_spatial,vertex_maps_job',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-create-collection-job-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-job-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_advanceJob',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_advanceJob" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_advanceJob" name="maps_collection_advanceJob" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.advanceJob", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["jobId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="advanceJob"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.advanceJob"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1051,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/advanceJob.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-job-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-job-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.advanceJob',
                 'maps_collection_advanceJob',
                 'vertex_spatial,vertex_maps_job',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-job-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-jobs-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_listJobs',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_listJobs" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_listJobs" name="maps_collection_listJobs" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.listJobs", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listJobs"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.listJobs"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1010,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/listJobs.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-jobs-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-jobs-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listJobs',
                 'maps_collection_listJobs',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-jobs-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-job-status-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_getJobStatus',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_getJobStatus" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_getJobStatus" name="maps_collection_getJobStatus" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.getJobStatus", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["jobId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getJobStatus"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.getJobStatus"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1063,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/getJobStatus.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-job-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-job-status-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getJobStatus',
                 'maps_collection_getJobStatus',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-job-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-store-dataset-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_storeDataset',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_storeDataset" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_storeDataset" name="maps_collection_storeDataset" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.storeDataset", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="storeDataset"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.storeDataset"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1034,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/storeDataset.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-store-dataset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-store-dataset-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.storeDataset',
                 'maps_collection_storeDataset',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-store-dataset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dataset-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_getDataset',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_getDataset" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_getDataset" name="maps_collection_getDataset" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.getDataset", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["datasetId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getDataset"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.getDataset"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1055,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/getDataset.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dataset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dataset-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getDataset',
                 'maps_collection_getDataset',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dataset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-datasets-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_listDatasets',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_listDatasets" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_listDatasets" name="maps_collection_listDatasets" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listDatasets", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listDatasets"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.listDatasets"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1034,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/listDatasets.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-datasets-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-datasets-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listDatasets',
                 'maps_collection_listDatasets',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-datasets-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-pipeline-stats-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_getPipelineStats',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_getPipelineStats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_getPipelineStats" name="maps_collection_getPipelineStats" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.getPipelineStats", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPipelineStats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.getPipelineStats"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1058,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/getPipelineStats.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-pipeline-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-pipeline-stats-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getPipelineStats',
                 'maps_collection_getPipelineStats',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-pipeline-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-osm-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_importOsmPois',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_importOsmPois" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_importOsmPois" name="maps_collection_importOsmPois" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.importOsmPois", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["jobId", "overpassResponse"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="importOsmPois"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.importOsmPois"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/importOsmPois.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-osm-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-osm-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.importOsmPois',
                 'maps_collection_importOsmPois',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-osm-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-wikidata-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_importWikidataPois',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_importWikidataPois" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_importWikidataPois" '
                 'name="maps_collection_importWikidataPois" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.importWikidataPois", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["jobId", "sparqlResponse"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="importWikidataPois"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.importWikidataPois"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1117,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/importWikidataPois.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-wikidata-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-wikidata-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.importWikidataPois',
                 'maps_collection_importWikidataPois',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-wikidata-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_searchPoi',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_searchPoi" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_searchPoi" name="maps_collection_searchPoi" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.searchPoi", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="searchPoi"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.searchPoi"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1016,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/searchPoi.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.searchPoi',
                 'maps_collection_searchPoi',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_getPoi',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_getPoi" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_getPoi" name="maps_collection_getPoi" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.getPoi", '
                 '"version": 1, "resultTimeoutMs": 30000, "requiredInputs": ["poiId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPoi"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.getPoi"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1027,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/getPoi.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getPoi',
                 'maps_collection_getPoi',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-poi-types-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_listPoiTypes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_listPoiTypes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_listPoiTypes" name="maps_collection_listPoiTypes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listPoiTypes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPoiTypes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.listPoiTypes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1034,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/listPoiTypes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-poi-types-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-poi-types-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listPoiTypes',
                 'maps_collection_listPoiTypes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-poi-types-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-writer-profiles-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_collection_registerWriterProfiles',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_collection_registerWriterProfiles" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_collection_registerWriterProfiles" '
                 'name="maps_collection_registerWriterProfiles" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerWriterProfiles", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerWriterProfiles"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.collection.registerWriterProfiles"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/maps/collection/registerWriterProfiles.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-writer-profiles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-writer-profiles-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerWriterProfiles',
                 'maps_collection_registerWriterProfiles',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-writer-profiles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-coverage-status-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_getCoverageStatus',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_getCoverageStatus" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_getCoverageStatus" name="maps_coverage_getCoverageStatus" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.getCoverageStatus", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getCoverageStatus"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.getCoverageStatus"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1056,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/getCoverageStatus.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-coverage-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-coverage-status-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getCoverageStatus',
                 'maps_coverage_getCoverageStatus',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-coverage-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-expand-frontier-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_expandFrontier',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_expandFrontier" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_expandFrontier" name="maps_coverage_expandFrontier" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.expandFrontier", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["targets"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="expandFrontier"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.expandFrontier"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1069,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/expandFrontier.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-expand-frontier-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-expand-frontier-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.expandFrontier',
                 'maps_coverage_expandFrontier',
                 'vertex_maps_coverage_target',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-expand-frontier-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-refresh-coverage-stats-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_refreshCoverageStats',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_refreshCoverageStats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_refreshCoverageStats" '
                 'name="maps_coverage_refreshCoverageStats" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.refreshCoverageStats", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="refreshCoverageStats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.refreshCoverageStats"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1074,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/refreshCoverageStats.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-refresh-coverage-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-refresh-coverage-stats-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.refreshCoverageStats',
                 'maps_coverage_refreshCoverageStats',
                 'vertex_maps_coverage_target',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-refresh-coverage-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-coverage-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_advanceCoverage',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_advanceCoverage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_advanceCoverage" name="maps_coverage_advanceCoverage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.advanceCoverage", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="advanceCoverage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.advanceCoverage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1044,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/advanceCoverage.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-coverage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-coverage-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.advanceCoverage',
                 'maps_coverage_advanceCoverage',
                 'vertex_spatial,vertex_maps_job,vertex_maps_coverage_target',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-coverage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-seed-all-known-variations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_seedAllKnownVariations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_seedAllKnownVariations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_seedAllKnownVariations" '
                 'name="maps_coverage_seedAllKnownVariations" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.seedAllKnownVariations", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="seedAllKnownVariations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.seedAllKnownVariations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1086,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/seedAllKnownVariations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-seed-all-known-variations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-seed-all-known-variations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.seedAllKnownVariations',
                 'maps_coverage_seedAllKnownVariations',
                 'vertex_maps_coverage_target',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-seed-all-known-variations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-batch-coverage-cycle-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_coverage_batchCoverageCycle',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_coverage_batchCoverageCycle" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_coverage_batchCoverageCycle" name="maps_coverage_batchCoverageCycle" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.batchCoverageCycle", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="batchCoverageCycle"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.coverage.batchCoverageCycle"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1063,
                 '00-contracts/bpmn/com/etzhayyim/maps/coverage/batchCoverageCycle.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-batch-coverage-cycle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-batch-coverage-cycle-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.batchCoverageCycle',
                 'maps_coverage_batchCoverageCycle',
                 'vertex_spatial,vertex_maps_job,vertex_maps_coverage_target',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-batch-coverage-cycle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-region-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_registerRegion',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_registerRegion" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_registerRegion" name="maps_geo_registerRegion" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerRegion", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["displayName", "lat", "lng"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRegion"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.registerRegion"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1067,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/registerRegion.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-region-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-region-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerRegion',
                 'maps_geo_registerRegion',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-region-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-geo-alias-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_resolveGeoAlias',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_resolveGeoAlias" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_resolveGeoAlias" name="maps_geo_resolveGeoAlias" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.resolveGeoAlias", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["scheme", "code"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="resolveGeoAlias"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.resolveGeoAlias"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1062,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/resolveGeoAlias.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-geo-alias-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-geo-alias-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.resolveGeoAlias',
                 'maps_geo_resolveGeoAlias',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-geo-alias-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-aliases-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_listGeoAliases',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_listGeoAliases" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_listGeoAliases" name="maps_geo_listGeoAliases" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listGeoAliases", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listGeoAliases"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.listGeoAliases"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/listGeoAliases.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-aliases-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-aliases-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listGeoAliases',
                 'maps_geo_listGeoAliases',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-aliases-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-schemes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_listGeoSchemes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_listGeoSchemes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_listGeoSchemes" name="maps_geo_listGeoSchemes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listGeoSchemes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listGeoSchemes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.listGeoSchemes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/listGeoSchemes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-schemes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-schemes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listGeoSchemes',
                 'maps_geo_listGeoSchemes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-schemes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vertical-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_listVerticalZones',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_listVerticalZones" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_listVerticalZones" name="maps_geo_listVerticalZones" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listVerticalZones", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listVerticalZones"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.listVerticalZones"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/listVerticalZones.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vertical-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vertical-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listVerticalZones',
                 'maps_geo_listVerticalZones',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vertical-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-natural-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_listNaturalZones',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_listNaturalZones" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_listNaturalZones" name="maps_geo_listNaturalZones" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listNaturalZones", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listNaturalZones"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.listNaturalZones"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/listNaturalZones.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-natural-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-natural-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listNaturalZones',
                 'maps_geo_listNaturalZones',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-natural-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-layer-coordinators-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_listLayerCoordinators',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_listLayerCoordinators" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_listLayerCoordinators" name="maps_geo_listLayerCoordinators" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listLayerCoordinators", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listLayerCoordinators"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.listLayerCoordinators"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1060,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/listLayerCoordinators.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-layer-coordinators-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-layer-coordinators-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listLayerCoordinators',
                 'maps_geo_listLayerCoordinators',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-layer-coordinators-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-zones3d-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geo_resolveZones3d',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geo_resolveZones3d" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geo_resolveZones3d" name="maps_geo_resolveZones3d" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.resolveZones3d", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["lat", "lng"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="resolveZones3d"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geo.resolveZones3d"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1052,
                 '00-contracts/bpmn/com/etzhayyim/maps/geo/resolveZones3d.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-zones3d-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-zones3d-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.resolveZones3d',
                 'maps_geo_resolveZones3d',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-zones3d-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-crawler-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_place_crawlerLocations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_place_crawlerLocations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_place_crawlerLocations" name="maps_place_crawlerLocations" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.crawlerLocations", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="crawlerLocations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.place.crawlerLocations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1038,
                 '00-contracts/bpmn/com/etzhayyim/maps/place/crawlerLocations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-crawler-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-crawler-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.crawlerLocations',
                 'maps_place_crawlerLocations',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-crawler-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-places-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_place_searchPlaces',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_place_searchPlaces" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_place_searchPlaces" name="maps_place_searchPlaces" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.searchPlaces", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="searchPlaces"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.place.searchPlaces"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1014,
                 '00-contracts/bpmn/com/etzhayyim/maps/place/searchPlaces.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-places-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-places-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.searchPlaces',
                 'maps_place_searchPlaces',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-places-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-place-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_place_getPlace',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_place_getPlace" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_place_getPlace" name="maps_place_getPlace" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.getPlace", '
                 '"version": 1, "resultTimeoutMs": 30000, "requiredInputs": ["placeId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPlace"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.place.getPlace"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1021,
                 '00-contracts/bpmn/com/etzhayyim/maps/place/getPlace.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-place-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-place-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getPlace',
                 'maps_place_getPlace',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-place-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-traverse-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_graph_graphTraverse',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_graph_graphTraverse" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_graph_graphTraverse" name="maps_graph_graphTraverse" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.graphTraverse", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["startId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="graphTraverse"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.graph.graphTraverse"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1051,
                 '00-contracts/bpmn/com/etzhayyim/maps/graph/graphTraverse.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-traverse-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-traverse-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.graphTraverse',
                 'maps_graph_graphTraverse',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-traverse-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-neighbors-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_graph_graphNeighbors',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_graph_graphNeighbors" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_graph_graphNeighbors" name="maps_graph_graphNeighbors" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.graphNeighbors", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["nodeId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="graphNeighbors"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.graph.graphNeighbors"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1056,
                 '00-contracts/bpmn/com/etzhayyim/maps/graph/graphNeighbors.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-neighbors-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-neighbors-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.graphNeighbors',
                 'maps_graph_graphNeighbors',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-neighbors-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-resources-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_graph_searchResources',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_graph_searchResources" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_graph_searchResources" name="maps_graph_searchResources" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.searchResources", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["query"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="searchResources"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.graph.searchResources"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1061,
                 '00-contracts/bpmn/com/etzhayyim/maps/graph/searchResources.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-resources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-resources-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.searchResources',
                 'maps_graph_searchResources',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-resources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerRoute',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerRoute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerRoute" name="maps_transport_registerRoute" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerRoute", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRoute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerRoute"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1064,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerRoute.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerRoute',
                 'maps_transport_registerRoute',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listRoutes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listRoutes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listRoutes" name="maps_transport_listRoutes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listRoutes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listRoutes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listRoutes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listRoutes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listRoutes',
                 'maps_transport_listRoutes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_getRoute',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_getRoute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_getRoute" name="maps_transport_getRoute" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.getRoute", '
                 '"version": 1, "resultTimeoutMs": 30000, "requiredInputs": ["routeId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getRoute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.getRoute"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1037,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/getRoute.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getRoute',
                 'maps_transport_getRoute',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-road-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerRoad',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerRoad" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerRoad" name="maps_transport_registerRoad" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerRoad", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRoad"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerRoad"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1058,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerRoad.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-road-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-road-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerRoad',
                 'maps_transport_registerRoad',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-road-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-roads-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listRoads',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listRoads" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listRoads" name="maps_transport_listRoads" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.listRoads", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listRoads"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listRoads"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listRoads.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-roads-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-roads-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listRoads',
                 'maps_transport_listRoads',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-roads-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-railway-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerRailway',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerRailway" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerRailway" name="maps_transport_registerRailway" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerRailway", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRailway"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerRailway"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerRailway.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-railway-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-railway-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerRailway',
                 'maps_transport_registerRailway',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-railway-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-railways-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listRailways',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listRailways" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listRailways" name="maps_transport_listRailways" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listRailways", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listRailways"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listRailways"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listRailways.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-railways-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-railways-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listRailways',
                 'maps_transport_listRailways',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-railways-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sea-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerSeaRoute',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerSeaRoute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerSeaRoute" name="maps_transport_registerSeaRoute" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerSeaRoute", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerSeaRoute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerSeaRoute"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerSeaRoute.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sea-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sea-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerSeaRoute',
                 'maps_transport_registerSeaRoute',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sea-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sea-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listSeaRoutes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listSeaRoutes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listSeaRoutes" name="maps_transport_listSeaRoutes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listSeaRoutes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSeaRoutes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listSeaRoutes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listSeaRoutes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sea-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sea-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSeaRoutes',
                 'maps_transport_listSeaRoutes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sea-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-air-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerAirRoute',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerAirRoute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerAirRoute" name="maps_transport_registerAirRoute" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerAirRoute", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerAirRoute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerAirRoute"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerAirRoute.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-air-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-air-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerAirRoute',
                 'maps_transport_registerAirRoute',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-air-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-air-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listAirRoutes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listAirRoutes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listAirRoutes" name="maps_transport_listAirRoutes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listAirRoutes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listAirRoutes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listAirRoutes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listAirRoutes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-air-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-air-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listAirRoutes',
                 'maps_transport_listAirRoutes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-air-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_registerBusRoute',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_registerBusRoute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_registerBusRoute" name="maps_transport_registerBusRoute" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerBusRoute","version":1,"resultTimeoutMs":30000,"requiredInputs":["operator"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBusRoute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.registerBusRoute"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/registerBusRoute.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-route-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerBusRoute',
                 'maps_transport_registerBusRoute',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-route-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_listBusRoutes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_listBusRoutes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_listBusRoutes" name="maps_transport_listBusRoutes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listBusRoutes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listBusRoutes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transport.listBusRoutes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport/listBusRoutes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-routes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listBusRoutes',
                 'maps_transport_listBusRoutes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-routes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-network-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_registerInfraNetwork',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_registerInfraNetwork" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_registerInfraNetwork" name="maps_infra_registerInfraNetwork" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerInfraNetwork","version":1,"resultTimeoutMs":30000,"requiredInputs":["infraType"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerInfraNetwork"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.registerInfraNetwork"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1086,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/registerInfraNetwork.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-network-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-network-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerInfraNetwork',
                 'maps_infra_registerInfraNetwork',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-network-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-networks-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_listInfraNetworks',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_listInfraNetworks" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_listInfraNetworks" name="maps_infra_listInfraNetworks" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listInfraNetworks", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listInfraNetworks"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.listInfraNetworks"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1044,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/listInfraNetworks.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-networks-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-networks-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listInfraNetworks',
                 'maps_infra_listInfraNetworks',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-networks-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-segment-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_registerInfraSegment',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_registerInfraSegment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_registerInfraSegment" name="maps_infra_registerInfraSegment" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerInfraSegment","version":1,"resultTimeoutMs":30000,"requiredInputs":["networkId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerInfraSegment"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.registerInfraSegment"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1086,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/registerInfraSegment.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-segment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-segment-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerInfraSegment',
                 'maps_infra_registerInfraSegment',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-segment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-segments-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_listInfraSegments',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_listInfraSegments" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_listInfraSegments" name="maps_infra_listInfraSegments" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listInfraSegments", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listInfraSegments"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.listInfraSegments"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1044,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/listInfraSegments.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-segments-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-segments-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listInfraSegments',
                 'maps_infra_listInfraSegments',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-segments-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-node-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_registerInfraNode',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_registerInfraNode" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_registerInfraNode" name="maps_infra_registerInfraNode" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerInfraNode","version":1,"resultTimeoutMs":30000,"requiredInputs":["networkId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerInfraNode"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.registerInfraNode"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1068,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/registerInfraNode.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-node-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-node-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerInfraNode',
                 'maps_infra_registerInfraNode',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-node-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-nodes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_listInfraNodes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_listInfraNodes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_listInfraNodes" name="maps_infra_listInfraNodes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listInfraNodes", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listInfraNodes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.listInfraNodes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1026,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/listInfraNodes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-nodes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-nodes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listInfraNodes',
                 'maps_infra_listInfraNodes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-nodes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-incident-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_registerInfraIncident',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_registerInfraIncident" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_registerInfraIncident" name="maps_infra_registerInfraIncident" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerInfraIncident","version":1,"resultTimeoutMs":30000,"requiredInputs":["incidentType"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerInfraIncident"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.registerInfraIncident"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/registerInfraIncident.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-incident-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-incident-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerInfraIncident',
                 'maps_infra_registerInfraIncident',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-incident-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-incidents-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_listInfraIncidents',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_listInfraIncidents" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_listInfraIncidents" name="maps_infra_listInfraIncidents" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listInfraIncidents", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listInfraIncidents"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.listInfraIncidents"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1050,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/listInfraIncidents.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-incidents-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-incidents-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listInfraIncidents',
                 'maps_infra_listInfraIncidents',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-incidents-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_infraQuery',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_infraQuery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_infraQuery" name="maps_infra_infraQuery" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.infraQuery", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="infraQuery"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.infraQuery"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1002,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/infraQuery.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.infraQuery',
                 'maps_infra_infraQuery',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-cross-section-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_infra_infraCrossSection',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_infra_infraCrossSection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_infra_infraCrossSection" name="maps_infra_infraCrossSection" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.infraCrossSection", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="infraCrossSection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.infra.infraCrossSection"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1044,
                 '00-contracts/bpmn/com/etzhayyim/maps/infra/infraCrossSection.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-cross-section-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-cross-section-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.infraCrossSection',
                 'maps_infra_infraCrossSection',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-cross-section-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-spot-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerSpot',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerSpot" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerSpot" name="maps_geography_registerSpot" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerSpot", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerSpot"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerSpot"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerSpot.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-spot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-spot-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerSpot',
                 'maps_geography_registerSpot',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-spot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-spots-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listSpots',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listSpots" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listSpots" name="maps_geography_listSpots" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.listSpots", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSpots"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listSpots"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listSpots.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-spots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-spots-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSpots',
                 'maps_geography_listSpots',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-spots-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-spot-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_getSpot',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_getSpot" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_getSpot" name="maps_geography_getSpot" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.getSpot", '
                 '"version": 1, "resultTimeoutMs": 30000, "requiredInputs": ["spotId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getSpot"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.getSpot"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/getSpot.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-spot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-spot-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getSpot',
                 'maps_geography_getSpot',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-spot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-search-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_spotSearch',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_spotSearch" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_spotSearch" name="maps_geography_spotSearch" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.spotSearch", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spotSearch"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.spotSearch"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/spotSearch.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-search-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spotSearch',
                 'maps_geography_spotSearch',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-recommend-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_spotRecommend',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_spotRecommend" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_spotRecommend" name="maps_geography_spotRecommend" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.spotRecommend", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spotRecommend"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.spotRecommend"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/spotRecommend.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-recommend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-recommend-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spotRecommend',
                 'maps_geography_spotRecommend',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-recommend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-river-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerRiver',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerRiver" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerRiver" name="maps_geography_registerRiver" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerRiver", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRiver"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerRiver"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerRiver.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-river-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-river-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerRiver',
                 'maps_geography_registerRiver',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-river-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-rivers-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listRivers',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listRivers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listRivers" name="maps_geography_listRivers" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listRivers", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listRivers"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listRivers"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listRivers.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-rivers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-rivers-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listRivers',
                 'maps_geography_listRivers',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-rivers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-lake-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerLake',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerLake" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerLake" name="maps_geography_registerLake" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerLake", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerLake"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerLake"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerLake.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-lake-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-lake-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerLake',
                 'maps_geography_registerLake',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-lake-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-lakes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listLakes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listLakes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listLakes" name="maps_geography_listLakes" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.maps.listLakes", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listLakes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listLakes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listLakes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-lakes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-lakes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listLakes',
                 'maps_geography_listLakes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-lakes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-coastline-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerCoastline',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerCoastline" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerCoastline" name="maps_geography_registerCoastline" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerCoastline", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerCoastline"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerCoastline"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1060,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerCoastline.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-coastline-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-coastline-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerCoastline',
                 'maps_geography_registerCoastline',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-coastline-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-coastlines-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listCoastlines',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listCoastlines" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listCoastlines" name="maps_geography_listCoastlines" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listCoastlines", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listCoastlines"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listCoastlines"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1042,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listCoastlines.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-coastlines-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-coastlines-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listCoastlines',
                 'maps_geography_listCoastlines',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-coastlines-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-mountain-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerMountain',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerMountain" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerMountain" name="maps_geography_registerMountain" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerMountain", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerMountain"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerMountain"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1054,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerMountain.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-mountain-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-mountain-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerMountain',
                 'maps_geography_registerMountain',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-mountain-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-mountains-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listMountains',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listMountains" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listMountains" name="maps_geography_listMountains" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listMountains", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listMountains"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listMountains"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1036,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listMountains.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-mountains-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-mountains-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listMountains',
                 'maps_geography_listMountains',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-mountains-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-maritime-zone-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerMaritimeZone',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerMaritimeZone" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerMaritimeZone" '
                 'name="maps_geography_registerMaritimeZone" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerMaritimeZone", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerMaritimeZone"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerMaritimeZone"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerMaritimeZone.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-maritime-zone-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-maritime-zone-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerMaritimeZone',
                 'maps_geography_registerMaritimeZone',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-maritime-zone-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-maritime-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listMaritimeZones',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listMaritimeZones" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listMaritimeZones" name="maps_geography_listMaritimeZones" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listMaritimeZones", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listMaritimeZones"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listMaritimeZones"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1060,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listMaritimeZones.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-maritime-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-maritime-zones-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listMaritimeZones',
                 'maps_geography_listMaritimeZones',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-maritime-zones-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-admin-area-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_registerAdminArea',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_registerAdminArea" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_registerAdminArea" name="maps_geography_registerAdminArea" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerAdminArea", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerAdminArea"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.registerAdminArea"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1060,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/registerAdminArea.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-admin-area-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-admin-area-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerAdminArea',
                 'maps_geography_registerAdminArea',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-admin-area-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-admin-areas-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_geography_listAdminAreas',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_geography_listAdminAreas" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_geography_listAdminAreas" name="maps_geography_listAdminAreas" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listAdminAreas", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listAdminAreas"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.geography.listAdminAreas"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1042,
                 '00-contracts/bpmn/com/etzhayyim/maps/geography/listAdminAreas.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-admin-areas-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-admin-areas-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listAdminAreas',
                 'maps_geography_listAdminAreas',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-admin-areas-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-aircraft-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerAircraft',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerAircraft" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerAircraft" '
                 'name="maps_transport_extra_registerAircraft" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerAircraft","version":1,"resultTimeoutMs":30000,"requiredInputs":["tailNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerAircraft"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerAircraft"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1102,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerAircraft.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-aircraft-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-aircraft-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerAircraft',
                 'maps_transport_extra_registerAircraft',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-aircraft-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-operation-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_upsertFlightOperation',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_upsertFlightOperation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_upsertFlightOperation" '
                 'name="maps_transport_extra_upsertFlightOperation" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.upsertFlightOperation","version":1,"resultTimeoutMs":30000,"requiredInputs":["flightNumber","aircraftDid","asOf"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="upsertFlightOperation"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.upsertFlightOperation"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/upsertFlightOperation.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-operation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-operation-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.upsertFlightOperation',
                 'maps_transport_extra_upsertFlightOperation',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-operation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-operations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listFlightOperations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listFlightOperations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listFlightOperations" '
                 'name="maps_transport_extra_listFlightOperations" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listFlightOperations","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listFlightOperations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listFlightOperations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listFlightOperations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-operations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-operations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listFlightOperations',
                 'maps_transport_extra_listFlightOperations',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-operations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-waterway-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerWaterway',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerWaterway" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerWaterway" '
                 'name="maps_transport_extra_registerWaterway" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerWaterway","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerWaterway"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerWaterway"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1096,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerWaterway.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-waterway-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-waterway-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerWaterway',
                 'maps_transport_extra_registerWaterway',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-waterway-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-waterways-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listWaterways',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listWaterways" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listWaterways" '
                 'name="maps_transport_extra_listWaterways" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listWaterways","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listWaterways"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listWaterways"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1052,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listWaterways.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-waterways-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-waterways-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listWaterways',
                 'maps_transport_extra_listWaterways',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-waterways-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-port-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerPort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerPort" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerPort" name="maps_transport_extra_registerPort" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerPort","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerPort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerPort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1072,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerPort.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-port-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-port-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerPort',
                 'maps_transport_extra_registerPort',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-port-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ports-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listPorts',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listPorts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listPorts" name="maps_transport_extra_listPorts" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listPorts","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPorts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listPorts"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1028,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listPorts.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ports-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ports-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listPorts',
                 'maps_transport_extra_listPorts',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ports-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-airport-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerAirport',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerAirport" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerAirport" '
                 'name="maps_transport_extra_registerAirport" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerAirport","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerAirport"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerAirport"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerAirport.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-airport-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-airport-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerAirport',
                 'maps_transport_extra_registerAirport',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-airport-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-airports-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listAirports',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listAirports" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listAirports" name="maps_transport_extra_listAirports" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listAirports","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listAirports"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listAirports"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listAirports.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-airports-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-airports-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listAirports',
                 'maps_transport_extra_listAirports',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-airports-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-station-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerStation',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerStation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerStation" '
                 'name="maps_transport_extra_registerStation" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerStation","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerStation"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerStation"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerStation.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-station-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-station-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerStation',
                 'maps_transport_extra_registerStation',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-station-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-stations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listStations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listStations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listStations" name="maps_transport_extra_listStations" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listStations","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listStations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listStations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listStations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-stations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-stations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listStations',
                 'maps_transport_extra_listStations',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-stations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-stop-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerBusStop',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerBusStop" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerBusStop" '
                 'name="maps_transport_extra_registerBusStop" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerBusStop","version":1,"resultTimeoutMs":30000,"requiredInputs":["name","operator"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBusStop"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerBusStop"/><zeebe:ioMapping><zeebe:input '
                 'source="=name" target="name"/><zeebe:input source="=operator" '
                 'target="operator"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1230,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerBusStop.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-stop-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-stop-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerBusStop',
                 'maps_transport_extra_registerBusStop',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-stop-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-stops-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listBusStops',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listBusStops" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listBusStops" name="maps_transport_extra_listBusStops" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listBusStops","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listBusStops"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listBusStops"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listBusStops.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-stops-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-stops-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listBusStops',
                 'maps_transport_extra_listBusStops',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-stops-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-parking-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerParking',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerParking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerParking" '
                 'name="maps_transport_extra_registerParking" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerParking","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerParking"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerParking"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerParking.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-parking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-parking-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerParking',
                 'maps_transport_extra_registerParking',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-parking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-parkings-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listParkings',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listParkings" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listParkings" name="maps_transport_extra_listParkings" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listParkings","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listParkings"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listParkings"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listParkings.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-parkings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-parkings-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listParkings',
                 'maps_transport_extra_listParkings',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-parkings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ev-charger-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_registerEvCharger',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_registerEvCharger" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_registerEvCharger" '
                 'name="maps_transport_extra_registerEvCharger" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerEvCharger","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerEvCharger"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.registerEvCharger"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1102,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/registerEvCharger.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ev-charger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ev-charger-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerEvCharger',
                 'maps_transport_extra_registerEvCharger',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ev-charger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ev-chargers-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listEvChargers',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listEvChargers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listEvChargers" '
                 'name="maps_transport_extra_listEvChargers" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listEvChargers","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listEvChargers"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listEvChargers"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1058,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listEvChargers.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ev-chargers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ev-chargers-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listEvChargers',
                 'maps_transport_extra_listEvChargers',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ev-chargers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-offer-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_upsertFlightOffer',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_upsertFlightOffer" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_upsertFlightOffer" '
                 'name="maps_transport_extra_upsertFlightOffer" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.upsertFlightOffer","version":1,"resultTimeoutMs":30000,"requiredInputs":["originIata","destinationIata","outboundDate","totalPrice","currency","bookingUrl"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="upsertFlightOffer"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.upsertFlightOffer"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1178,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/upsertFlightOffer.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-offer-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-offer-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.upsertFlightOffer',
                 'maps_transport_extra_upsertFlightOffer',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-offer-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-offers-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_transport_extra_listFlightOffers',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_transport_extra_listFlightOffers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_transport_extra_listFlightOffers" '
                 'name="maps_transport_extra_listFlightOffers" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listFlightOffers","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listFlightOffers"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.transportExtra.listFlightOffers"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1070,
                 '00-contracts/bpmn/com/etzhayyim/maps/transport-extra/listFlightOffers.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-offers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-offers-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listFlightOffers',
                 'maps_transport_extra_listFlightOffers',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-offers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_registerBuilding',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_registerBuilding" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_registerBuilding" '
                 'name="maps_twin_sensor_sim_registerBuilding" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerBuilding", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBuilding"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.registerBuilding"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/registerBuilding.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerBuilding',
                 'maps_twin_sensor_sim_registerBuilding',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-buildings-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_listBuildings',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_listBuildings" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_listBuildings" '
                 'name="maps_twin_sensor_sim_listBuildings" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listBuildings", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listBuildings"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.listBuildings"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1058,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/listBuildings.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-buildings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-buildings-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listBuildings',
                 'maps_twin_sensor_sim_listBuildings',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-buildings-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-building-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_getBuilding',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_getBuilding" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_getBuilding" name="maps_twin_sensor_sim_getBuilding" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.getBuilding", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["buildingId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getBuilding"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.getBuilding"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1080,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/getBuilding.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-building-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-building-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getBuilding',
                 'maps_twin_sensor_sim_getBuilding',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-building-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-floor-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_registerBuildingFloor',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_registerBuildingFloor" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_registerBuildingFloor" '
                 'name="maps_twin_sensor_sim_registerBuildingFloor" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerBuildingFloor", "version": 1, "resultTimeoutMs": '
                 '30000, "requiredInputs": ["buildingId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBuildingFloor"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.registerBuildingFloor"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1140,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/registerBuildingFloor.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-floor-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-floor-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerBuildingFloor',
                 'maps_twin_sensor_sim_registerBuildingFloor',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-floor-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-asset-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_registerAsset',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_registerAsset" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_registerAsset" '
                 'name="maps_twin_sensor_sim_registerAsset" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerAsset", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name", "assetType"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerAsset"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.registerAsset"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1099,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/registerAsset.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-asset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-asset-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerAsset',
                 'maps_twin_sensor_sim_registerAsset',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-asset-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-assets-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_listAssets',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_listAssets" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_listAssets" name="maps_twin_sensor_sim_listAssets" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listAssets", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listAssets"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.listAssets"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1040,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/listAssets.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-assets-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-assets-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listAssets',
                 'maps_twin_sensor_sim_listAssets',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-assets-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-device-bind-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_deviceBind',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_deviceBind" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_deviceBind" name="maps_twin_sensor_sim_deviceBind" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.deviceBind", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["deviceDid", "assetId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="deviceBind"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.deviceBind"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/deviceBind.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-device-bind-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-device-bind-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.deviceBind',
                 'maps_twin_sensor_sim_deviceBind',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-device-bind-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-devices-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_listDevices',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_listDevices" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_listDevices" name="maps_twin_sensor_sim_listDevices" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listDevices", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listDevices"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.listDevices"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/listDevices.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-devices-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-devices-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listDevices',
                 'maps_twin_sensor_sim_listDevices',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-devices-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_twinStateUpdate',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_twinStateUpdate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_twinStateUpdate" '
                 'name="maps_twin_sensor_sim_twinStateUpdate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.twinStateUpdate", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityType", "entityId"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="twinStateUpdate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.twinStateUpdate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1116,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/twinStateUpdate.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.twinStateUpdate',
                 'maps_twin_sensor_sim_twinStateUpdate',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_twinStateGet',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_twinStateGet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_twinStateGet" name="maps_twin_sensor_sim_twinStateGet" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.twinStateGet", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="twinStateGet"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.twinStateGet"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/twinStateGet.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.twinStateGet',
                 'maps_twin_sensor_sim_twinStateGet',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-occupancy-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_occupancyUpdate',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_occupancyUpdate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_occupancyUpdate" '
                 'name="maps_twin_sensor_sim_occupancyUpdate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.occupancyUpdate", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["buildingId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="occupancyUpdate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.occupancyUpdate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/occupancyUpdate.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-occupancy-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-occupancy-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.occupancyUpdate',
                 'maps_twin_sensor_sim_occupancyUpdate',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-occupancy-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sensor-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_registerSensor',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_registerSensor" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_registerSensor" '
                 'name="maps_twin_sensor_sim_registerSensor" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.registerSensor", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sensorType"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerSensor"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.registerSensor"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/registerSensor.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sensor-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sensor-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerSensor',
                 'maps_twin_sensor_sim_registerSensor',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sensor-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensors-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_listSensors',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_listSensors" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_listSensors" name="maps_twin_sensor_sim_listSensors" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listSensors", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSensors"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.listSensors"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1046,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/listSensors.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensors-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensors-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSensors',
                 'maps_twin_sensor_sim_listSensors',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensors-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-ingest-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_sensorIngest',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_sensorIngest" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_sensorIngest" name="maps_twin_sensor_sim_sensorIngest" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.sensorIngest", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sensorId", "readings"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="sensorIngest"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.sensorIngest"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1096,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/sensorIngest.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-ingest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-ingest-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.sensorIngest',
                 'maps_twin_sensor_sim_sensorIngest',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-ingest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_sensorQuery',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_sensorQuery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_sensorQuery" name="maps_twin_sensor_sim_sensorQuery" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.sensorQuery", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sensorId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="sensorQuery"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.sensorQuery"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/sensorQuery.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.sensorQuery',
                 'maps_twin_sensor_sim_sensorQuery',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-latest-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_sensorLatest',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_sensorLatest" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_sensorLatest" name="maps_twin_sensor_sim_sensorLatest" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.sensorLatest", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sensorId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="sensorLatest"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.sensorLatest"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/sensorLatest.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-latest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-latest-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.sensorLatest',
                 'maps_twin_sensor_sim_sensorLatest',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-latest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-alert-set-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_sensorAlertSet',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_sensorAlertSet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_sensorAlertSet" '
                 'name="maps_twin_sensor_sim_sensorAlertSet" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.sensorAlertSet", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["sensorId", "metric", "threshold"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="sensorAlertSet"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.sensorAlertSet"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/sensorAlertSet.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-alert-set-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-alert-set-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.sensorAlertSet',
                 'maps_twin_sensor_sim_sensorAlertSet',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-alert-set-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensor-alerts-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_listSensorAlerts',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_listSensorAlerts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_listSensorAlerts" '
                 'name="maps_twin_sensor_sim_listSensorAlerts" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.listSensorAlerts", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSensorAlerts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.listSensorAlerts"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/listSensorAlerts.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensor-alerts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensor-alerts-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSensorAlerts',
                 'maps_twin_sensor_sim_listSensorAlerts',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensor-alerts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-create-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_simulationCreate',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_simulationCreate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_simulationCreate" '
                 'name="maps_twin_sensor_sim_simulationCreate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.simulationCreate", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["name"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="simulationCreate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.simulationCreate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/simulationCreate.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-create-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-create-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.simulationCreate',
                 'maps_twin_sensor_sim_simulationCreate',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-create-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-run-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_simulationRun',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_simulationRun" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_simulationRun" '
                 'name="maps_twin_sensor_sim_simulationRun" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.simulationRun", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["simulationId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="simulationRun"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.simulationRun"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/simulationRun.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-run-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-run-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.simulationRun',
                 'maps_twin_sensor_sim_simulationRun',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-run-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-result-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_simulationResult',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_simulationResult" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_simulationResult" '
                 'name="maps_twin_sensor_sim_simulationResult" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.simulationResult", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["simulationId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="simulationResult"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.simulationResult"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/simulationResult.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-result-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-result-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.simulationResult',
                 'maps_twin_sensor_sim_simulationResult',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-result-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-forecast-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_forecastGet',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_forecastGet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_forecastGet" name="maps_twin_sensor_sim_forecastGet" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.forecastGet", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="forecastGet"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.forecastGet"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/forecastGet.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-forecast-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-forecast-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.forecastGet',
                 'maps_twin_sensor_sim_forecastGet',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-forecast-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-health-assess-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_healthAssess',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_healthAssess" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_healthAssess" name="maps_twin_sensor_sim_healthAssess" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.healthAssess", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="healthAssess"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.healthAssess"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/healthAssess.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-health-assess-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-health-assess-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.healthAssess',
                 'maps_twin_sensor_sim_healthAssess',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-health-assess-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-maintenance-plan-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_maintenancePlan',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_maintenancePlan" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_maintenancePlan" '
                 'name="maps_twin_sensor_sim_maintenancePlan" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.maintenancePlan", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="maintenancePlan"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.maintenancePlan"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1102,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/maintenancePlan.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-maintenance-plan-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-maintenance-plan-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.maintenancePlan',
                 'maps_twin_sensor_sim_maintenancePlan',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-maintenance-plan-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_worldBeliefUpdate',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_worldBeliefUpdate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_worldBeliefUpdate" '
                 'name="maps_twin_sensor_sim_worldBeliefUpdate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.worldBeliefUpdate", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId", "hypothesis"] '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="worldBeliefUpdate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.worldBeliefUpdate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1128,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/worldBeliefUpdate.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-update-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.worldBeliefUpdate',
                 'maps_twin_sensor_sim_worldBeliefUpdate',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-update-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_worldBeliefGet',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_worldBeliefGet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_worldBeliefGet" '
                 'name="maps_twin_sensor_sim_worldBeliefGet" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.worldBeliefGet", "version": 1, "resultTimeoutMs": 30000, '
                 '"requiredInputs": ["entityId"] }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="worldBeliefGet"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.worldBeliefGet"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1096,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/worldBeliefGet.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-get-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.worldBeliefGet',
                 'maps_twin_sensor_sim_worldBeliefGet',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-get-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-latent-world-model-run-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_twin_sensor_sim_latentWorldModelRun',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_twin_sensor_sim_latentWorldModelRun" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_twin_sensor_sim_latentWorldModelRun" '
                 'name="maps_twin_sensor_sim_latentWorldModelRun" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.maps.latentWorldModelRun", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="latentWorldModelRun"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.twinSensorSim.latentWorldModelRun"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/maps/twin-sensor-sim/latentWorldModelRun.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-latent-world-model-run-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-latent-world-model-run-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.latentWorldModelRun',
                 'maps_twin_sensor_sim_latentWorldModelRun',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-latent-world-model-run-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialEventRecord',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialEventRecord" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialEventRecord" '
                 'name="maps_spatiotemporal_spatialEventRecord" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialEventRecord","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId","eventType"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialEventRecord"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialEventRecord"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialEventRecord.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialEventRecord',
                 'maps_spatiotemporal_spatialEventRecord',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialEventQuery',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialEventQuery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialEventQuery" '
                 'name="maps_spatiotemporal_spatialEventQuery" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialEventQuery","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialEventQuery"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialEventQuery"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1073,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialEventQuery.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialEventQuery',
                 'maps_spatiotemporal_spatialEventQuery',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialVersionRecord',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialVersionRecord" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialVersionRecord" '
                 'name="maps_spatiotemporal_spatialVersionRecord" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialVersionRecord","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId","changeType"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialVersionRecord"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialVersionRecord"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1134,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialVersionRecord.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialVersionRecord',
                 'maps_spatiotemporal_spatialVersionRecord',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialVersionQuery',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialVersionQuery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialVersionQuery" '
                 'name="maps_spatiotemporal_spatialVersionQuery" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialVersionQuery","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialVersionQuery"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialVersionQuery"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1115,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialVersionQuery.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialVersionQuery',
                 'maps_spatiotemporal_spatialVersionQuery',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-write-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialRelationWrite',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialRelationWrite" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialRelationWrite" '
                 'name="maps_spatiotemporal_spatialRelationWrite" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialRelationWrite","version":1,"resultTimeoutMs":30000,"requiredInputs":["fromId","toId","relation"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialRelationWrite"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialRelationWrite"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialRelationWrite.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-write-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-write-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialRelationWrite',
                 'maps_spatiotemporal_spatialRelationWrite',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-write-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialRelationQuery',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialRelationQuery" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialRelationQuery" '
                 'name="maps_spatiotemporal_spatialRelationQuery" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialRelationQuery","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialRelationQuery"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialRelationQuery"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialRelationQuery.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-query-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialRelationQuery',
                 'maps_spatiotemporal_spatialRelationQuery',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-query-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-timeline-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_timeline',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_timeline" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_timeline" name="maps_spatiotemporal_timeline" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.timeline","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="timeline"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.timeline"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/timeline.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-timeline-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-timeline-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.timeline',
                 'maps_spatiotemporal_timeline',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-timeline-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-diff-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_spatialDiff',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_spatialDiff" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_spatialDiff" name="maps_spatiotemporal_spatialDiff" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.spatialDiff","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="spatialDiff"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.spatialDiff"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1067,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/spatialDiff.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-diff-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-diff-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.spatialDiff',
                 'maps_spatiotemporal_spatialDiff',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-diff-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-display-layer-define-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_displayLayerDefine',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_displayLayerDefine" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_displayLayerDefine" '
                 'name="maps_spatiotemporal_displayLayerDefine" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.displayLayerDefine","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="displayLayerDefine"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.displayLayerDefine"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1105,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/displayLayerDefine.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-display-layer-define-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-display-layer-define-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.displayLayerDefine',
                 'maps_spatiotemporal_displayLayerDefine',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-display-layer-define-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-display-layers-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_listDisplayLayers',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_listDisplayLayers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_listDisplayLayers" '
                 'name="maps_spatiotemporal_listDisplayLayers" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listDisplayLayers","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listDisplayLayers"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.listDisplayLayers"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1073,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/listDisplayLayers.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-display-layers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-display-layers-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listDisplayLayers',
                 'maps_spatiotemporal_listDisplayLayers',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-display-layers-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dashboard-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_getDashboard',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_getDashboard" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_getDashboard" name="maps_spatiotemporal_getDashboard" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.getDashboard","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getDashboard"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.getDashboard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1043,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/getDashboard.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dashboard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dashboard-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.getDashboard',
                 'maps_spatiotemporal_getDashboard',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dashboard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-actor-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_spatiotemporal_actorLocations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_spatiotemporal_actorLocations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_spatiotemporal_actorLocations" '
                 'name="maps_spatiotemporal_actorLocations" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.actorLocations","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="actorLocations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.spatiotemporal.actorLocations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1055,
                 '00-contracts/bpmn/com/etzhayyim/maps/spatiotemporal/actorLocations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-actor-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-actor-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.actorLocations',
                 'maps_spatiotemporal_actorLocations',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-actor-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-post-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listPostLocations',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listPostLocations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listPostLocations" '
                 'name="maps_registry_media_listPostLocations" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listPostLocations","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPostLocations"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listPostLocations"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1072,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listPostLocations.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-post-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-post-locations-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listPostLocations',
                 'maps_registry_media_listPostLocations',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-post-locations-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-import-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_mapralyImportPoi',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_mapralyImportPoi" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_mapralyImportPoi" '
                 'name="maps_registry_media_mapralyImportPoi" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.mapralyImportPoi","version":1,"resultTimeoutMs":30000,"requiredInputs":["pois"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="mapralyImportPoi"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.mapralyImportPoi"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/mapralyImportPoi.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-import-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-import-poi-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.mapralyImportPoi',
                 'maps_registry_media_mapralyImportPoi',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-import-poi-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-list-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_mapralyListPois',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_mapralyListPois" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_mapralyListPois" '
                 'name="maps_registry_media_mapralyListPois" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.mapralyListPois","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="mapralyListPois"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.mapralyListPois"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1060,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/mapralyListPois.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-list-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-list-pois-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.mapralyListPois',
                 'maps_registry_media_mapralyListPois',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-list-pois-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-vision-import-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_visionImportEntities',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_visionImportEntities" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_visionImportEntities" '
                 'name="maps_registry_media_visionImportEntities" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.visionImportEntities","version":1,"resultTimeoutMs":30000,"requiredInputs":["entities"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="visionImportEntities"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.visionImportEntities"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1120,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/visionImportEntities.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-vision-import-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-vision-import-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.visionImportEntities',
                 'maps_registry_media_visionImportEntities',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-vision-import-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vision-results-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listVisionResults',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listVisionResults" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listVisionResults" '
                 'name="maps_registry_media_listVisionResults" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listVisionResults","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listVisionResults"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listVisionResults"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1072,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listVisionResults.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vision-results-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vision-results-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listVisionResults',
                 'maps_registry_media_listVisionResults',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vision-results-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-satellite-import-scene-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_satelliteImportScene',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_satelliteImportScene" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_satelliteImportScene" '
                 'name="maps_registry_media_satelliteImportScene" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.satelliteImportScene","version":1,"resultTimeoutMs":30000,"requiredInputs":["scenes"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="satelliteImportScene"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.satelliteImportScene"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1118,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/satelliteImportScene.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-satellite-import-scene-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-satellite-import-scene-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.satelliteImportScene',
                 'maps_registry_media_satelliteImportScene',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-satellite-import-scene-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-scenes-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listSatelliteScenes',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listSatelliteScenes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listSatelliteScenes" '
                 'name="maps_registry_media_listSatelliteScenes" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listSatelliteScenes","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSatelliteScenes"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listSatelliteScenes"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listSatelliteScenes.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-scenes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-scenes-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSatelliteScenes',
                 'maps_registry_media_listSatelliteScenes',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-scenes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-sources-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listSatelliteSources',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listSatelliteSources" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listSatelliteSources" '
                 'name="maps_registry_media_listSatelliteSources" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listSatelliteSources","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listSatelliteSources"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listSatelliteSources"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1090,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listSatelliteSources.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-sources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-sources-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listSatelliteSources',
                 'maps_registry_media_listSatelliteSources',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-sources-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-domains-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listGeoDomains',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listGeoDomains" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listGeoDomains" '
                 'name="maps_registry_media_listGeoDomains" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listGeoDomains","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listGeoDomains"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listGeoDomains"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1054,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listGeoDomains.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-domains-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-domains-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listGeoDomains',
                 'maps_registry_media_listGeoDomains',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-domains-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-web-crawl-geo-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listWebCrawlGeoEntities',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listWebCrawlGeoEntities" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listWebCrawlGeoEntities" '
                 'name="maps_registry_media_listWebCrawlGeoEntities" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listWebCrawlGeoEntities","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listWebCrawlGeoEntities"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listWebCrawlGeoEntities"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1108,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listWebCrawlGeoEntities.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-web-crawl-geo-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-web-crawl-geo-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listWebCrawlGeoEntities',
                 'maps_registry_media_listWebCrawlGeoEntities',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-web-crawl-geo-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-legal-entity-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerLegalEntity',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerLegalEntity" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerLegalEntity" '
                 'name="maps_registry_media_registerLegalEntity" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerLegalEntity","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerLegalEntity"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerLegalEntity"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1110,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerLegalEntity.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-legal-entity-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-legal-entity-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerLegalEntity',
                 'maps_registry_media_registerLegalEntity',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-legal-entity-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-legal-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listLegalEntities',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listLegalEntities" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listLegalEntities" '
                 'name="maps_registry_media_listLegalEntities" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listLegalEntities","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listLegalEntities"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listLegalEntities"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1072,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listLegalEntities.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-legal-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-legal-entities-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listLegalEntities',
                 'maps_registry_media_listLegalEntities',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-legal-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operator-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerOperator',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerOperator" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerOperator" '
                 'name="maps_registry_media_registerOperator" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerOperator","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerOperator"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerOperator"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerOperator.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operator-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operator-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerOperator',
                 'maps_registry_media_registerOperator',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operator-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operators-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listOperators',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listOperators" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listOperators" name="maps_registry_media_listOperators" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listOperators","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listOperators"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listOperators"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1048,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listOperators.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operators-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operators-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listOperators',
                 'maps_registry_media_listOperators',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operators-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-owner-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerPropertyOwner',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerPropertyOwner" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerPropertyOwner" '
                 'name="maps_registry_media_registerPropertyOwner" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerPropertyOwner","version":1,"resultTimeoutMs":30000,"requiredInputs":["name"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerPropertyOwner"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerPropertyOwner"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1122,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerPropertyOwner.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-owner-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-owner-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerPropertyOwner',
                 'maps_registry_media_registerPropertyOwner',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-owner-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-owners-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listPropertyOwners',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listPropertyOwners" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listPropertyOwners" '
                 'name="maps_registry_media_listPropertyOwners" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listPropertyOwners","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPropertyOwners"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listPropertyOwners"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listPropertyOwners.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-owners-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-owners-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listPropertyOwners',
                 'maps_registry_media_listPropertyOwners',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-owners-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-land-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerLandRegistry',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerLandRegistry" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerLandRegistry" '
                 'name="maps_registry_media_registerLandRegistry" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerLandRegistry","version":1,"resultTimeoutMs":30000,"requiredInputs":["registryNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerLandRegistry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerLandRegistry"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1126,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerLandRegistry.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-land-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-land-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerLandRegistry',
                 'maps_registry_media_registerLandRegistry',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-land-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-land-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listLandRegistries',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listLandRegistries" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listLandRegistries" '
                 'name="maps_registry_media_listLandRegistries" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listLandRegistries","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listLandRegistries"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listLandRegistries"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listLandRegistries.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-land-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-land-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listLandRegistries',
                 'maps_registry_media_listLandRegistries',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-land-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerPropertyRegistry',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerPropertyRegistry" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerPropertyRegistry" '
                 'name="maps_registry_media_registerPropertyRegistry" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerPropertyRegistry","version":1,"resultTimeoutMs":30000,"requiredInputs":["registryNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerPropertyRegistry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerPropertyRegistry"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1150,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerPropertyRegistry.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerPropertyRegistry',
                 'maps_registry_media_registerPropertyRegistry',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listPropertyRegistries',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listPropertyRegistries" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listPropertyRegistries" '
                 'name="maps_registry_media_listPropertyRegistries" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listPropertyRegistries","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPropertyRegistries"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listPropertyRegistries"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1102,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listPropertyRegistries.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listPropertyRegistries',
                 'maps_registry_media_listPropertyRegistries',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-business-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerBusinessRegistry',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerBusinessRegistry" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerBusinessRegistry" '
                 'name="maps_registry_media_registerBusinessRegistry" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerBusinessRegistry","version":1,"resultTimeoutMs":30000,"requiredInputs":["registryNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBusinessRegistry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerBusinessRegistry"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1150,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerBusinessRegistry.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-business-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-business-registry-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerBusinessRegistry',
                 'maps_registry_media_registerBusinessRegistry',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-business-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-business-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listBusinessRegistries',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listBusinessRegistries" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listBusinessRegistries" '
                 'name="maps_registry_media_listBusinessRegistries" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listBusinessRegistries","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listBusinessRegistries"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listBusinessRegistries"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1102,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listBusinessRegistries.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-business-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-business-registries-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listBusinessRegistries',
                 'maps_registry_media_listBusinessRegistries',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-business-registries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-construction-permit-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerConstructionPermit',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerConstructionPermit" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerConstructionPermit" '
                 'name="maps_registry_media_registerConstructionPermit" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerConstructionPermit","version":1,"resultTimeoutMs":30000,"requiredInputs":["registryNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerConstructionPermit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerConstructionPermit"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1162,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerConstructionPermit.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-construction-permit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-construction-permit-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerConstructionPermit',
                 'maps_registry_media_registerConstructionPermit',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-construction-permit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-construction-permits-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listConstructionPermits',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listConstructionPermits" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listConstructionPermits" '
                 'name="maps_registry_media_listConstructionPermits" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listConstructionPermits","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listConstructionPermits"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listConstructionPermits"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1108,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listConstructionPermits.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-construction-permits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-construction-permits-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listConstructionPermits',
                 'maps_registry_media_listConstructionPermits',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-construction-permits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operating-license-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerOperatingLicense',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerOperatingLicense" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerOperatingLicense" '
                 'name="maps_registry_media_registerOperatingLicense" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerOperatingLicense","version":1,"resultTimeoutMs":30000,"requiredInputs":["registryNumber"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerOperatingLicense"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerOperatingLicense"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1150,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerOperatingLicense.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operating-license-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operating-license-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerOperatingLicense',
                 'maps_registry_media_registerOperatingLicense',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operating-license-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operating-licenses-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listOperatingLicenses',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listOperatingLicenses" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listOperatingLicenses" '
                 'name="maps_registry_media_listOperatingLicenses" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listOperatingLicenses","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listOperatingLicenses"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listOperatingLicenses"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1096,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listOperatingLicenses.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operating-licenses-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operating-licenses-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listOperatingLicenses',
                 'maps_registry_media_listOperatingLicenses',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operating-licenses-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-zoning-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerZoningRecord',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerZoningRecord" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerZoningRecord" '
                 'name="maps_registry_media_registerZoningRecord" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerZoningRecord","version":1,"resultTimeoutMs":30000,"requiredInputs":["landUse"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerZoningRecord"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerZoningRecord"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerZoningRecord.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-zoning-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-zoning-record-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerZoningRecord',
                 'maps_registry_media_registerZoningRecord',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-zoning-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-zoning-records-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_listZoningRecords',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_listZoningRecords" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_listZoningRecords" '
                 'name="maps_registry_media_listZoningRecords" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.listZoningRecords","version":1,"resultTimeoutMs":30000}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listZoningRecords"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.listZoningRecords"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1072,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/listZoningRecords.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-zoning-records-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-zoning-records-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.listZoningRecords',
                 'maps_registry_media_listZoningRecords',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-zoning-records-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ownership-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_registerOwnership',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_registerOwnership" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_registerOwnership" '
                 'name="maps_registry_media_registerOwnership" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.registerOwnership","version":1,"resultTimeoutMs":30000,"requiredInputs":["ownerEntityId","propertyId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerOwnership"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.registerOwnership"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1120,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/registerOwnership.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ownership-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ownership-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.registerOwnership',
                 'maps_registry_media_registerOwnership',
                 'vertex_spatial',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ownership-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-ownership-chain-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_ownershipChain',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_ownershipChain" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_ownershipChain" '
                 'name="maps_registry_media_ownershipChain" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.ownershipChain","version":1,"resultTimeoutMs":30000,"requiredInputs":["propertyId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="ownershipChain"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.ownershipChain"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1086,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/ownershipChain.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-ownership-chain-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-ownership-chain-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.ownershipChain',
                 'maps_registry_media_ownershipChain',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-ownership-chain-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, '
         'source_path,\n'
         '         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, '
         'org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6,\n'
         "             'active', $7, 100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-entity-history-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_registry_media_entityHistory',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_maps_registry_media_entityHistory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/maps"><bpmn:process '
                 'id="maps_registry_media_entityHistory" name="maps_registry_media_entityHistory" '
                 'isExecutable="true"><bpmn:documentation>{"nsid":"com.etzhayyim.apps.maps.entityHistory","version":1,"resultTimeoutMs":30000,"requiredInputs":["entityId"]}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="entityHistory"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="maps.registryMedia.entityHistory"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1078,
                 '00-contracts/bpmn/com/etzhayyim/maps/registry-media/entityHistory.bpmn',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-entity-history-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1, 30000,\n'
         "             $5, 'active', $6, 100, $7, $8,\n"
         "             $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-entity-history-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.entityHistory',
                 'maps_registry_media_entityHistory',
                 '',
                 '2026-04-30T22:04:00+09:00',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-collection',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-entity-history-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-create-collection-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-create-collection-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-jobs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-jobs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-job-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-job-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-store-dataset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-store-dataset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dataset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dataset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-datasets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-datasets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-pipeline-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-pipeline-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-osm-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-osm-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-import-wikidata-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-import-wikidata-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-poi-types-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-poi-types-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-writer-profiles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-writer-profiles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-coverage-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-coverage-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-expand-frontier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-expand-frontier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-refresh-coverage-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-refresh-coverage-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-advance-coverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-advance-coverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-seed-all-known-variations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-seed-all-known-variations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-batch-coverage-cycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-batch-coverage-cycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-region-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-region-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-geo-alias-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-geo-alias-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-aliases-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-aliases-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-schemes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-schemes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vertical-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vertical-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-natural-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-natural-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-layer-coordinators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-layer-coordinators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-resolve-zones3d-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-resolve-zones3d-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-crawler-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-crawler-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-places-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-places-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-place-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-place-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-traverse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-traverse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-graph-neighbors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-graph-neighbors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-search-resources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-search-resources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-road-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-road-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-roads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-roads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-railway-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-railway-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-railways-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-railways-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sea-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sea-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sea-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sea-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-air-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-air-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-air-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-air-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-route-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-routes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-network-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-network-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-networks-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-networks-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-segment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-segment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-segments-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-segments-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-node-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-node-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-nodes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-nodes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-infra-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-infra-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-infra-incidents-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-infra-incidents-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-infra-cross-section-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-infra-cross-section-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-spot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-spot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-spots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-spots-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-spot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-spot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spot-recommend-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spot-recommend-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-river-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-river-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-rivers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-rivers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-lake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-lake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-lakes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-lakes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-coastline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-coastline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-coastlines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-coastlines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-mountain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-mountain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-mountains-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-mountains-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-maritime-zone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-maritime-zone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-maritime-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-maritime-zones-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-admin-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-admin-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-admin-areas-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-admin-areas-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-aircraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-aircraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-operation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-operation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-operations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-operations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-waterway-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-waterway-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-waterways-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-waterways-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-airport-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-airport-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-airports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-airports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-station-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-station-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-stations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-stations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-bus-stop-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-bus-stop-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-bus-stops-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-bus-stops-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-parking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-parking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-parkings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-parkings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ev-charger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ev-charger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-ev-chargers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-ev-chargers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-upsert-flight-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-upsert-flight-offer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-flight-offers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-flight-offers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-buildings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-buildings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-building-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-building-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-building-floor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-building-floor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-asset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-asset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-assets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-assets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-device-bind-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-device-bind-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-devices-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-devices-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-twin-state-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-twin-state-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-occupancy-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-occupancy-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-sensor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-sensor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-ingest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-ingest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-latest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-latest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-sensor-alert-set-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-sensor-alert-set-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-sensor-alerts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-sensor-alerts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-create-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-create-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-simulation-result-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-simulation-result-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-forecast-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-forecast-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-health-assess-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-health-assess-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-maintenance-plan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-maintenance-plan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-update-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-world-belief-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-world-belief-get-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-latent-world-model-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-latent-world-model-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-event-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-event-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-version-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-version-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-write-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-write-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-relation-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-relation-query-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-timeline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-timeline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-spatial-diff-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-spatial-diff-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-display-layer-define-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-display-layer-define-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-display-layers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-display-layers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-actor-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-actor-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-post-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-post-locations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-import-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-import-poi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-mapraly-list-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-mapraly-list-pois-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-vision-import-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-vision-import-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-vision-results-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-vision-results-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-satellite-import-scene-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-satellite-import-scene-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-scenes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-scenes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-satellite-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-satellite-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-geo-domains-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-geo-domains-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-web-crawl-geo-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-web-crawl-geo-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-legal-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-legal-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-legal-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-legal-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operator-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operator-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-owners-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-owners-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-land-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-land-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-land-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-land-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-property-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-property-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-property-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-property-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-business-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-business-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-business-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-business-registries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-construction-permit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-construction-permit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-construction-permits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-construction-permits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-operating-license-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-operating-license-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-operating-licenses-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-operating-licenses-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-zoning-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-zoning-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-list-zoning-records-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-list-zoning-records-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-register-ownership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-register-ownership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-ownership-chain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-ownership-chain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-collection-entity-history-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-collection-entity-history-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
