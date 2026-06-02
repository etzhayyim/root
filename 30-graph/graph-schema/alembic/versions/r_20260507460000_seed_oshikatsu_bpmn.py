"""Captured from Kysely migration 20260507460000_seed_oshikatsu_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507460000_seed_oshikatsu_bpmn"
down_revision = 'r_20260507451000_vertex_edge_business_manager'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-create-creator-profile-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_create_creator_profile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_create_creator_profile" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="createCreatorProfile"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.createCreatorProfile" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 730,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/createCreatorProfile.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-create-creator-profile-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-create-creator-profile-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.createCreatorProfile',
                 'oshikatsu_create_creator_profile',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-create-creator-profile-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-creator-profile-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_get_creator_profile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_get_creator_profile" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="getCreatorProfile"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.getCreatorProfile" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 721,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/getCreatorProfile.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-creator-profile-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-creator-profile-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.getCreatorProfile',
                 'oshikatsu_get_creator_profile',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-creator-profile-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-creators-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_list_creators',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_list_creators" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="listCreators"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.listCreators" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 705,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/listCreators.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-creators-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-creators-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.listCreators',
                 'oshikatsu_list_creators',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-creators-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-update-tiers-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_update_tiers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_update_tiers" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="updateTiers"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.updateTiers" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/updateTiers.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-update-tiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-update-tiers-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.updateTiers',
                 'oshikatsu_update_tiers',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-update-tiers-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-subscribe-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_subscribe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_subscribe" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="subscribe"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.subscribe" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 695,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/subscribe.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-subscribe-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-subscribe-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.subscribe',
                 'oshikatsu_subscribe',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-subscribe-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-unsubscribe-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_unsubscribe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_unsubscribe" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="unsubscribe"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.unsubscribe" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 701,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/unsubscribe.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-unsubscribe-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-unsubscribe-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.unsubscribe',
                 'oshikatsu_unsubscribe',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-unsubscribe-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-subscriptions-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_list_subscriptions',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_list_subscriptions" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="listSubscriptions"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.listSubscriptions" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 720,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/listSubscriptions.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-subscriptions-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-subscriptions-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.listSubscriptions',
                 'oshikatsu_list_subscriptions',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-subscriptions-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-check-access-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_check_access',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_check_access" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="checkAccess"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.checkAccess" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/checkAccess.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-check-access-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-check-access-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.checkAccess',
                 'oshikatsu_check_access',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-check-access-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-publish-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_publish_content',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_publish_content" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="publishContent"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.publishContent" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 711,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/publishContent.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-publish-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-publish-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.publishContent',
                 'oshikatsu_publish_content',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-publish-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_get_content',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_get_content" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="getContent"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.getContent" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 699,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/getContent.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.getContent',
                 'oshikatsu_get_content',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_list_content',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_list_content" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="listContent"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.listContent" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 702,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/listContent.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-content-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.listContent',
                 'oshikatsu_list_content',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-content-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-tip-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_tip',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_tip" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="tip"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.tip" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 677,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/tip.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-tip-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-tip-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.tip',
                 'oshikatsu_tip',
                 30000,
                 'vertex_oshikatsu_creator_profile,vertex_oshikatsu_subscription_tier,vertex_oshikatsu_subscription,vertex_oshikatsu_subscription_cancel,vertex_oshikatsu_exclusive_content,vertex_oshikatsu_tip,edge_oshikatsu_creator_tier,edge_oshikatsu_subscription,edge_oshikatsu_content_by_creator,edge_oshikatsu_tip_to_creator,edge_oshikatsu_tip_for_content',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-tip-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-creator-stats-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_creator_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_creator_stats" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="creatorStats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.creatorStats" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 705,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/creatorStats.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-creator-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-creator-stats-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.creatorStats',
                 'oshikatsu_creator_stats',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-creator-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-search-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'oshikatsu_search',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://etzhayyim.com/bpmn/oshikatsu"><bpmn:process '
                 'id="oshikatsu_search" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="search"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.com.etzhayyim.apps.oshikatsu.search" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 686,
                 '00-contracts/bpmn/com/etzhayyim/oshikatsu/search.bpmn',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-search-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-search-v1',
                 'did:web:oshikatsu.etzhayyim.com',
                 'com.etzhayyim.apps.oshikatsu.search',
                 'oshikatsu_search',
                 30000,
                 '',
                 '2026-05-07T02:15:00Z',
                 'did:web:oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'sys.bpmn.seed.oshikatsu',
                 'did:web:oshikatsu.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-search-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-create-creator-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-create-creator-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-creator-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-creator-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-creators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-creators-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-update-tiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-update-tiers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-subscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-subscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-unsubscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-unsubscribe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-subscriptions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-subscriptions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-check-access-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-check-access-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-publish-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-publish-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-get-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-get-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-list-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-list-content-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-tip-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-tip-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-creator-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-creator-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/oshikatsu-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/oshikatsu-search-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
