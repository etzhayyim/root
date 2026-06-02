"""Captured from Kysely migration 20260507440000_seed_bunken_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507440000_seed_bunken_bpmn"
down_revision = 'r_20260507430000_seed_handotai_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 703, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-cdx-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_collect_from_cdx',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_collect_from_cdx" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="collectFromCdx"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.collectFromCdx" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/collectFromCdx.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-cdx-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-cdx-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.collectFromCdx',
                 'bunken_collect_from_cdx',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-cdx-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 700, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-fetch-cdx-batch-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_fetch_cdx_batch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_fetch_cdx_batch" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="fetchCdxBatch"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.fetchCdxBatch" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/fetchCdxBatch.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-fetch-cdx-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-fetch-cdx-batch-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.fetchCdxBatch',
                 'bunken_fetch_cdx_batch',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-fetch-cdx-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 693, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-enrich-batch-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_enrich_batch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_enrich_batch" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="enrichBatch"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.enrichBatch" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/enrichBatch.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-enrich-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-enrich-batch-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.enrichBatch',
                 'bunken_enrich_batch',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-enrich-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 713, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-ndl-api-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_collect_from_ndl_api',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_collect_from_ndl_api" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="collectFromNdlApi"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.collectFromNdlApi" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/collectFromNdlApi.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-ndl-api-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-ndl-api-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.collectFromNdlApi',
                 'bunken_collect_from_ndl_api',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-ndl-api-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 696, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-register-dids-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_register_dids" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="registerDids"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.registerDids" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/registerDids.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-register-dids-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-register-dids-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.registerDids',
                 'bunken_register_dids',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-register-dids-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 691, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-link-same-as-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_link_same_as',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_link_same_as" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="linkSameAs"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.linkSameAs" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/linkSameAs.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-link-same-as-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-link-same-as-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.linkSameAs',
                 'bunken_link_same_as',
                 'vertex_bunken_collection_job,vertex_bunken_bibliographic_item,edge_bunken_same_as',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-link-same-as-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 674, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-stats-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process id="bunken_stats" '
                 'isExecutable="true"><bpmn:startEvent id="start" /><bpmn:serviceTask id="task" '
                 'name="stats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.stats" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/stats.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-stats-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.stats',
                 'bunken_stats',
                 '',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 677, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-search-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_search',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process id="bunken_search" '
                 'isExecutable="true"><bpmn:startEvent id="start" /><bpmn:serviceTask id="task" '
                 'name="search"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.search" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/search.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-search-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.search',
                 'bunken_search',
                 '',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, 687, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-get-record-v1',
                 'did:web:bunken.etzhayyim.com',
                 'bunken_get_record',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bunken"><bpmn:process '
                 'id="bunken_get_record" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getRecord"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.bunken.getRecord" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/bunken/getRecord.bpmn',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-get-record-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        60000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-get-record-v1',
                 'did:web:bunken.etzhayyim.com',
                 'com.etzhayyim.apps.bunken.getRecord',
                 'bunken_get_record',
                 '',
                 '2026-05-07T01:55:00Z',
                 'did:web:bunken.etzhayyim.com',
                 'did:web:bunken.etzhayyim.com',
                 'sys.bpmn.seed.bunken',
                 'did:web:bunken.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-get-record-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-cdx-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-cdx-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-fetch-cdx-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-fetch-cdx-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-enrich-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-enrich-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-collect-from-ndl-api-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-collect-from-ndl-api-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-link-same-as-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-link-same-as-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bunken-get-record-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bunken-get-record-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
