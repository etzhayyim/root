"""Captured from Kysely migration 20260507410000_seed_organizer_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507410000_seed_organizer_bpmn"
down_revision = 'r_20260507400000_seed_omise_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-tag-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_add_tag',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_add_tag" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_add_tag" name="organizer.addTag" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_addTag" />\n'
                 '    <bpmn:serviceTask id="Task_addTag" name="organizer.addTag">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.addTag" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_addTag" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1097,
                 '00-contracts/bpmn/ai/gftd/organizer/addTag.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-tag-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-tag-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.addTag',
                 'organizer_add_tag',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-tag-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-to-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_add_to_collection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_add_to_collection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_add_to_collection" '
                 'name="organizer.addToCollection" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_addToCollection" />\n'
                 '    <bpmn:serviceTask id="Task_addToCollection" '
                 'name="organizer.addToCollection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.addToCollection" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_addToCollection" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1171,
                 '00-contracts/bpmn/ai/gftd/organizer/addToCollection.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-to-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-to-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.addToCollection',
                 'organizer_add_to_collection',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-to-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-analyze-subscriptions-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_analyze_subscriptions',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_analyze_subscriptions" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_analyze_subscriptions" '
                 'name="organizer.analyzeSubscriptions" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_analyzeSubscriptions" />\n'
                 '    <bpmn:serviceTask id="Task_analyzeSubscriptions" '
                 'name="organizer.analyzeSubscriptions">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.analyzeSubscriptions" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_analyzeSubscriptions" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1209,
                 '00-contracts/bpmn/ai/gftd/organizer/analyzeSubscriptions.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-analyze-subscriptions-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-analyze-subscriptions-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.analyzeSubscriptions',
                 'organizer_analyze_subscriptions',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-analyze-subscriptions-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_create_collection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_create_collection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_create_collection" '
                 'name="organizer.createCollection" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createCollection" />\n'
                 '    <bpmn:serviceTask id="Task_createCollection" '
                 'name="organizer.createCollection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.createCollection" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createCollection" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1177,
                 '00-contracts/bpmn/ai/gftd/organizer/createCollection.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.createCollection',
                 'organizer_create_collection',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-rule-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_create_rule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_create_rule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_create_rule" name="organizer.createRule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createRule" />\n'
                 '    <bpmn:serviceTask id="Task_createRule" name="organizer.createRule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.createRule" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createRule" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/organizer/createRule.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-rule-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-rule-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.createRule',
                 'organizer_create_rule',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-rule-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-item-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_delete_item',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_delete_item" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_delete_item" name="organizer.deleteItem" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_deleteItem" />\n'
                 '    <bpmn:serviceTask id="Task_deleteItem" name="organizer.deleteItem">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.deleteItem" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_deleteItem" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/organizer/deleteItem.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-item-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-item-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.deleteItem',
                 'organizer_delete_item',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-item-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-rule-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_delete_rule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_delete_rule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_delete_rule" name="organizer.deleteRule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_deleteRule" />\n'
                 '    <bpmn:serviceTask id="Task_deleteRule" name="organizer.deleteRule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.deleteRule" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_deleteRule" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1129,
                 '00-contracts/bpmn/ai/gftd/organizer/deleteRule.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-rule-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-rule-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.deleteRule',
                 'organizer_delete_rule',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-rule-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-detect-subscription-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_detect_subscription',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_detect_subscription" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_detect_subscription" '
                 'name="organizer.detectSubscription" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_detectSubscription" />\n'
                 '    <bpmn:serviceTask id="Task_detectSubscription" '
                 'name="organizer.detectSubscription">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.detectSubscription" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_detectSubscription" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1193,
                 '00-contracts/bpmn/ai/gftd/organizer/detectSubscription.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-detect-subscription-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-detect-subscription-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.detectSubscription',
                 'organizer_detect_subscription',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-detect-subscription-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-recommendations-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_get_recommendations',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_get_recommendations" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_get_recommendations" '
                 'name="organizer.getRecommendations" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getRecommendations" />\n'
                 '    <bpmn:serviceTask id="Task_getRecommendations" '
                 'name="organizer.getRecommendations">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.getRecommendations" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getRecommendations" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1193,
                 '00-contracts/bpmn/ai/gftd/organizer/getRecommendations.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-recommendations-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-recommendations-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.getRecommendations',
                 'organizer_get_recommendations',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-recommendations-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-vault-stats-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_get_vault_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_get_vault_stats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_get_vault_stats" name="organizer.getVaultStats" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getVaultStats" />\n'
                 '    <bpmn:serviceTask id="Task_getVaultStats" name="organizer.getVaultStats">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.getVaultStats" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getVaultStats" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1155,
                 '00-contracts/bpmn/ai/gftd/organizer/getVaultStats.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-vault-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-vault-stats-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.getVaultStats',
                 'organizer_get_vault_stats',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-vault-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-collections-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_list_collections',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_list_collections" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_list_collections" name="organizer.listCollections" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listCollections" />\n'
                 '    <bpmn:serviceTask id="Task_listCollections" '
                 'name="organizer.listCollections">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.listCollections" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listCollections" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1169,
                 '00-contracts/bpmn/ai/gftd/organizer/listCollections.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-collections-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-collections-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.listCollections',
                 'organizer_list_collections',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-collections-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-items-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_list_items',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_list_items" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_list_items" name="organizer.listItems" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listItems" />\n'
                 '    <bpmn:serviceTask id="Task_listItems" name="organizer.listItems">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.listItems" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listItems" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/ai/gftd/organizer/listItems.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-items-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-items-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.listItems',
                 'organizer_list_items',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-items-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-reclassify-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_reclassify',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_reclassify" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_reclassify" name="organizer.reclassify" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_reclassify" />\n'
                 '    <bpmn:serviceTask id="Task_reclassify" name="organizer.reclassify">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.reclassify" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_reclassify" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1127,
                 '00-contracts/bpmn/ai/gftd/organizer/reclassify.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-reclassify-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-reclassify-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.reclassify',
                 'organizer_reclassify',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-reclassify-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-register-item-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_register_item',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_register_item" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_register_item" name="organizer.registerItem" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_registerItem" />\n'
                 '    <bpmn:serviceTask id="Task_registerItem" name="organizer.registerItem">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.registerItem" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_registerItem" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1145,
                 '00-contracts/bpmn/ai/gftd/organizer/registerItem.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-register-item-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-register-item-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.registerItem',
                 'organizer_register_item',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-register-item-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-from-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_remove_from_collection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_remove_from_collection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_remove_from_collection" '
                 'name="organizer.removeFromCollection" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_removeFromCollection" />\n'
                 '    <bpmn:serviceTask id="Task_removeFromCollection" '
                 'name="organizer.removeFromCollection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.removeFromCollection" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_removeFromCollection" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1211,
                 '00-contracts/bpmn/ai/gftd/organizer/removeFromCollection.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-from-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-from-collection-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.removeFromCollection',
                 'organizer_remove_from_collection',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-from-collection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-tag-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_remove_tag',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_remove_tag" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_remove_tag" name="organizer.removeTag" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_removeTag" />\n'
                 '    <bpmn:serviceTask id="Task_removeTag" name="organizer.removeTag">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.removeTag" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_removeTag" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/ai/gftd/organizer/removeTag.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-tag-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-tag-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.removeTag',
                 'organizer_remove_tag',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-tag-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-request-cancellation-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_request_cancellation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_request_cancellation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_request_cancellation" '
                 'name="organizer.requestCancellation" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_requestCancellation" />\n'
                 '    <bpmn:serviceTask id="Task_requestCancellation" '
                 'name="organizer.requestCancellation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.organizer.requestCancellation" retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_requestCancellation" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1201,
                 '00-contracts/bpmn/ai/gftd/organizer/requestCancellation.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-request-cancellation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-request-cancellation-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.requestCancellation',
                 'organizer_request_cancellation',
                 30000,
                 'vertex_organizer_item,vertex_organizer_classification,vertex_organizer_tag,vertex_organizer_collection,vertex_organizer_rule,vertex_organizer_subscription_item,vertex_organizer_subscription_analysis,vertex_organizer_item_deletion,vertex_organizer_tag_deletion,vertex_organizer_collection_item_deletion,vertex_organizer_rule_deletion,vertex_organizer_subscription_review_job,vertex_organizer_subscription_item_update,edge_organizer_item_classification,edge_organizer_item_tag,edge_organizer_collection_item,edge_organizer_rule_collection,edge_organizer_subscription_analysis,edge_organizer_subscription_review_job',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-request-cancellation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-search-items-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_search_items',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_search_items" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_search_items" name="organizer.searchItems" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_searchItems" />\n'
                 '    <bpmn:serviceTask id="Task_searchItems" name="organizer.searchItems">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.searchItems" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_searchItems" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1137,
                 '00-contracts/bpmn/ai/gftd/organizer/searchItems.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-search-items-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-search-items-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.searchItems',
                 'organizer_search_items',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-search-items-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-suggest-rules-v1',
                 'did:web:organizer.etzhayyim.com',
                 'organizer_suggest_rules',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_organizer_suggest_rules" '
                 'targetNamespace="https://etzhayyim.com/bpmn/organizer">\n'
                 '  <bpmn:process id="organizer_suggest_rules" name="organizer.suggestRules" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_Start_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_suggestRules" />\n'
                 '    <bpmn:serviceTask id="Task_suggestRules" name="organizer.suggestRules">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.organizer.suggestRules" '
                 'retries="2" />\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_suggestRules" '
                 'targetRef="End" />\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Task_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1145,
                 '00-contracts/bpmn/ai/gftd/organizer/suggestRules.bpmn',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-suggest-rules-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-suggest-rules-v1',
                 'did:web:organizer.etzhayyim.com',
                 'ai.gftd.apps.organizer.suggestRules',
                 'organizer_suggest_rules',
                 30000,
                 '',
                 '2026-05-07T01:25:00Z',
                 'did:web:organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'sys.bpmn.seed.organizer',
                 'did:web:organizer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-suggest-rules-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-tag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-tag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-add-to-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-add-to-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-analyze-subscriptions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-analyze-subscriptions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-create-rule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-create-rule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-delete-rule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-delete-rule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-detect-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-detect-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-recommendations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-recommendations-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-get-vault-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-get-vault-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-collections-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-collections-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-list-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-list-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-reclassify-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-reclassify-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-register-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-register-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-from-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-from-collection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-remove-tag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-remove-tag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-request-cancellation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-request-cancellation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-search-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-search-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/organizer-suggest-rules-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/organizer-suggest-rules-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
