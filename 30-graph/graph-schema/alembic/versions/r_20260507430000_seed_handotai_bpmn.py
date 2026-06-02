"""Captured from Kysely migration 20260507430000_seed_handotai_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507430000_seed_handotai_bpmn"
down_revision = 'r_20260507420000_seed_kenkyusha_bpmn'
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
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-create-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_alert_create',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai">\n'
                 '  <bpmn:process id="handotai_alert_create" isExecutable="true">\n'
                 '    <bpmn:startEvent id="start" />\n'
                 '    <bpmn:serviceTask id="task" name="alertCreate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.alertCreate" /></bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:endEvent id="end" />\n'
                 '    <bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/>\n'
                 '    <bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" />\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 743,
                 '00-contracts/bpmn/com/etzhayyim/handotai/alertCreate.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-create-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-create-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.alertCreate',
                 'handotai_alert_create',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-create-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-delete-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_alert_delete',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai">\n'
                 '  <bpmn:process id="handotai_alert_delete" isExecutable="true">\n'
                 '    <bpmn:startEvent id="start" /><bpmn:serviceTask id="task" '
                 'name="alertDelete"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.alertDelete" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" />\n'
                 '    <bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" />\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 716,
                 '00-contracts/bpmn/com/etzhayyim/handotai/alertDelete.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-delete-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-delete-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.alertDelete',
                 'handotai_alert_delete',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-delete-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-list-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_alert_list',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_alert_list" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="alertList"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.alertList" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 693,
                 '00-contracts/bpmn/com/etzhayyim/handotai/alertList.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-list-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.alertList',
                 'handotai_alert_list',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-backfill-writer-posts-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_backfill_writer_posts',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_backfill_writer_posts" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="backfillWriterPosts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.backfillWriterPosts" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 724,
                 '00-contracts/bpmn/com/etzhayyim/handotai/backfillWriterPosts.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-backfill-writer-posts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-backfill-writer-posts-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.backfillWriterPosts',
                 'handotai_backfill_writer_posts',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-backfill-writer-posts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-crawl-trigger-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_crawl_trigger',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_crawl_trigger" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="crawlTrigger"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.crawlTrigger" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/handotai/crawlTrigger.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-crawl-trigger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-crawl-trigger-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.crawlTrigger',
                 'handotai_crawl_trigger',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-crawl-trigger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-article-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_get_article',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_get_article" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getArticle"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.getArticle" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 696,
                 '00-contracts/bpmn/com/etzhayyim/handotai/getArticle.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-article-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-article-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.getArticle',
                 'handotai_get_article',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-article-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-daily-digest-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_get_daily_digest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_get_daily_digest" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getDailyDigest"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.getDailyDigest" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 709,
                 '00-contracts/bpmn/com/etzhayyim/handotai/getDailyDigest.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-daily-digest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-daily-digest-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.getDailyDigest',
                 'handotai_get_daily_digest',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-daily-digest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-subscription-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_get_subscription',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_get_subscription" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getSubscription"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.getSubscription" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 711,
                 '00-contracts/bpmn/com/etzhayyim/handotai/getSubscription.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-subscription-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-subscription-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.getSubscription',
                 'handotai_get_subscription',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-subscription-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-weekly-report-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_get_weekly_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_get_weekly_report" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getWeeklyReport"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.getWeeklyReport" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 712,
                 '00-contracts/bpmn/com/etzhayyim/handotai/getWeeklyReport.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-weekly-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-weekly-report-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.getWeeklyReport',
                 'handotai_get_weekly_report',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-weekly-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-handle-daily-evolution-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_handle_daily_evolution',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_handle_daily_evolution" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="handleDailyEvolution"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.handleDailyEvolution" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 727,
                 '00-contracts/bpmn/com/etzhayyim/handotai/handleDailyEvolution.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-handle-daily-evolution-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-handle-daily-evolution-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.handleDailyEvolution',
                 'handotai_handle_daily_evolution',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-handle-daily-evolution-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_list_articles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_list_articles" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="listArticles"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.listArticles" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/handotai/listArticles.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.listArticles',
                 'handotai_list_articles',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-semi-entities-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_list_semi_entities',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_list_semi_entities" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="listSemiEntities"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.listSemiEntities" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 715,
                 '00-contracts/bpmn/com/etzhayyim/handotai/listSemiEntities.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-semi-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-semi-entities-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.listSemiEntities',
                 'handotai_list_semi_entities',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-semi-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-semi-entities-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_register_semi_entities',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_register_semi_entities" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="registerSemiEntities"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.registerSemiEntities" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 727,
                 '00-contracts/bpmn/com/etzhayyim/handotai/registerSemiEntities.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-semi-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-semi-entities-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.registerSemiEntities',
                 'handotai_register_semi_entities',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-semi-entities-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-writer-profiles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_register_writer_profiles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_register_writer_profiles" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="registerWriterProfiles"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.registerWriterProfiles" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 733,
                 '00-contracts/bpmn/com/etzhayyim/handotai/registerWriterProfiles.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-writer-profiles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-writer-profiles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.registerWriterProfiles',
                 'handotai_register_writer_profiles',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-writer-profiles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-report-generate-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_report_generate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_report_generate" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="reportGenerate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.reportGenerate" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 708,
                 '00-contracts/bpmn/com/etzhayyim/handotai/reportGenerate.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-report-generate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-report-generate-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.reportGenerate',
                 'handotai_report_generate',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-report-generate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-search-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_search_articles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_search_articles" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="searchArticles"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.searchArticles" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 708,
                 '00-contracts/bpmn/com/etzhayyim/handotai/searchArticles.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-search-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-search-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.searchArticles',
                 'handotai_search_articles',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-search-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-seed-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_seed_articles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_seed_articles" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="seedArticles"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.seedArticles" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/handotai/seedArticles.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-seed-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-seed-articles-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.seedArticles',
                 'handotai_seed_articles',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-seed-articles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-add-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_source_add',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_source_add" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="sourceAdd"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.sourceAdd" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 693,
                 '00-contracts/bpmn/com/etzhayyim/handotai/sourceAdd.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-add-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-add-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.sourceAdd',
                 'handotai_source_add',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-add-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-list-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_source_list',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_source_list" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="sourceList"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.sourceList" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 696,
                 '00-contracts/bpmn/com/etzhayyim/handotai/sourceList.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-list-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.sourceList',
                 'handotai_source_list',
                 30000,
                 '',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-subscribe-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_subscribe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_subscribe" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="subscribe"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.subscribe" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 692,
                 '00-contracts/bpmn/com/etzhayyim/handotai/subscribe.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-subscribe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-subscribe-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.subscribe',
                 'handotai_subscribe',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-subscribe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-translate-article-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_translate_article',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_translate_article" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="translateArticle"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.translateArticle" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 714,
                 '00-contracts/bpmn/com/etzhayyim/handotai/translateArticle.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-translate-article-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-translate-article-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.translateArticle',
                 'handotai_translate_article',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-translate-article-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-update-translation-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_update_translation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process '
                 'id="handotai_update_translation" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="updateTranslation"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.updateTranslation" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 717,
                 '00-contracts/bpmn/com/etzhayyim/handotai/updateTranslation.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-update-translation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-update-translation-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.updateTranslation',
                 'handotai_update_translation',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-update-translation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-wave-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_wave',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/handotai"><bpmn:process id="handotai_wave" '
                 'isExecutable="true"><bpmn:startEvent id="start" /><bpmn:serviceTask id="task" '
                 'name="wave"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.handotai.wave" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 677,
                 '00-contracts/bpmn/com/etzhayyim/handotai/wave.bpmn',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-wave-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-wave-v1',
                 'did:web:handotai.etzhayyim.com',
                 'com.etzhayyim.apps.handotai.wave',
                 'handotai_wave',
                 30000,
                 'vertex_handotai_alert,vertex_handotai_article,vertex_handotai_collection_job,vertex_handotai_digest,vertex_handotai_report,vertex_handotai_semi_entity,vertex_handotai_source,vertex_handotai_subscription,edge_handotai_article_entity,edge_handotai_source_article,edge_handotai_subscription_entity,vertex_repo_record',
                 '2026-05-07T01:45:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'did:web:handotai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-wave-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-create-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-create-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-delete-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-delete-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-alert-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-alert-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-backfill-writer-posts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-backfill-writer-posts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-crawl-trigger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-crawl-trigger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-article-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-article-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-daily-digest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-daily-digest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-get-weekly-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-get-weekly-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-handle-daily-evolution-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-handle-daily-evolution-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-list-semi-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-list-semi-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-semi-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-semi-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-register-writer-profiles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-register-writer-profiles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-report-generate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-report-generate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-search-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-search-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-seed-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-seed-articles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-add-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-add-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-source-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-source-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-subscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-subscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-translate-article-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-translate-article-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-update-translation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-update-translation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/handotai-wave-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/handotai-wave-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
