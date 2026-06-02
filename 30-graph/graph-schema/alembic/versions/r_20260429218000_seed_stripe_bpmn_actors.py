"""Captured from Kysely migration 20260429218000_seed_stripe_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429218000_seed_stripe_bpmn_actors"
down_revision = 'r_20260429217000_seed_mailer_bpmn_actors'
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
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-create-cardholder-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_create_cardholder',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_create_cardholder" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_create_cardholder" name="stripe createCardholder" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.createCardholder", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="create cardholder"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.createCardholder"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1031,
                 '00-contracts/bpmn/com/etzhayyim/stripe/createCardholder.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-create-cardholder-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-createCardholder-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.createCardholder',
                 'stripe_create_cardholder',
                 120000,
                 'vertex_stripe_cardholder',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-createCardholder-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-issue-card-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_issue_card',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_issue_card" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_issue_card" name="stripe issueCard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.issueCard", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="issue card"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.issueCard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 989,
                 '00-contracts/bpmn/com/etzhayyim/stripe/issueCard.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-issue-card-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-issueCard-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.issueCard',
                 'stripe_issue_card',
                 120000,
                 'vertex_stripe_cardholder,vertex_stripe_issued_card,vertex_stripe_authorization,vertex_stripe_card_credit_allocation,vertex_stripe_card_credit_consumption,vertex_stripe_spending_limit,vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-issueCard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-assign-card-credits-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_assign_card_credits',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_assign_card_credits" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_assign_card_credits" name="stripe assignCardCredits" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.assignCardCredits", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="assign card credits"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.assignCardCredits"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1040,
                 '00-contracts/bpmn/com/etzhayyim/stripe/assignCardCredits.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-assign-card-credits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-assignCardCredits-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.assignCardCredits',
                 'stripe_assign_card_credits',
                 120000,
                 'vertex_stripe_cardholder,vertex_stripe_issued_card,vertex_stripe_authorization,vertex_stripe_card_credit_allocation,vertex_stripe_card_credit_consumption,vertex_stripe_spending_limit,vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-assignCardCredits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-credits-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_get_card_credits',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_get_card_credits" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_get_card_credits" name="stripe getCardCredits" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.getCardCredits", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get card credits"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.getCardCredits"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1021,
                 '00-contracts/bpmn/com/etzhayyim/stripe/getCardCredits.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-credits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardCredits-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.getCardCredits',
                 'stripe_get_card_credits',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardCredits-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-authorization-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_handle_authorization',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_handle_authorization" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_handle_authorization" name="stripe handleAuthorization" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.handleAuthorization", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="handle authorization"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.handleAuthorization"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/com/etzhayyim/stripe/handleAuthorization.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-authorization-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleAuthorization-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.handleAuthorization',
                 'stripe_handle_authorization',
                 120000,
                 'vertex_stripe_authorization,vertex_stripe_card_credit_consumption',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleAuthorization-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_get_card',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_get_card" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process id="stripe_get_card" '
                 'name="stripe getCard" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.getCard", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get card"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.getCard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 976,
                 '00-contracts/bpmn/com/etzhayyim/stripe/getCard.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCard-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.getCard',
                 'stripe_get_card',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-cards-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_list_cards',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_list_cards" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_list_cards" name="stripe listCards" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.listCards", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list cards"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.listCards"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 988,
                 '00-contracts/bpmn/com/etzhayyim/stripe/listCards.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-cards-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listCards-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.listCards',
                 'stripe_list_cards',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listCards-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-freeze-card-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_freeze_card',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_freeze_card" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_freeze_card" name="stripe freezeCard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.freezeCard", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="freeze card"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.freezeCard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 995,
                 '00-contracts/bpmn/com/etzhayyim/stripe/freezeCard.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-freeze-card-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-freezeCard-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.freezeCard',
                 'stripe_freeze_card',
                 120000,
                 'vertex_stripe_issued_card',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-freezeCard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-unfreeze-card-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_unfreeze_card',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_unfreeze_card" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_unfreeze_card" name="stripe unfreezeCard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.unfreezeCard", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="unfreeze card"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.unfreezeCard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1007,
                 '00-contracts/bpmn/com/etzhayyim/stripe/unfreezeCard.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-unfreeze-card-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-unfreezeCard-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.unfreezeCard',
                 'stripe_unfreeze_card',
                 120000,
                 'vertex_stripe_issued_card',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-unfreezeCard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-cancel-card-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_cancel_card',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_cancel_card" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_cancel_card" name="stripe cancelCard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.cancelCard", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cancel card"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.cancelCard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 995,
                 '00-contracts/bpmn/com/etzhayyim/stripe/cancelCard.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-cancel-card-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-cancelCard-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.cancelCard',
                 'stripe_cancel_card',
                 120000,
                 'vertex_stripe_issued_card',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-cancelCard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-update-spending-limit-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_update_spending_limit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_update_spending_limit" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_update_spending_limit" name="stripe updateSpendingLimit" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.updateSpendingLimit", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="update spending limit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.updateSpendingLimit"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1052,
                 '00-contracts/bpmn/com/etzhayyim/stripe/updateSpendingLimit.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-update-spending-limit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-updateSpendingLimit-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.updateSpendingLimit',
                 'stripe_update_spending_limit',
                 120000,
                 'vertex_stripe_spending_limit',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-updateSpendingLimit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-transactions-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_list_transactions',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_list_transactions" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_list_transactions" name="stripe listTransactions" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.listTransactions", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list transactions"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.listTransactions"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1030,
                 '00-contracts/bpmn/com/etzhayyim/stripe/listTransactions.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-transactions-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listTransactions-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.listTransactions',
                 'stripe_list_transactions',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listTransactions-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-cardholder-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_get_cardholder',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_get_cardholder" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_get_cardholder" name="stripe getCardholder" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.getCardholder", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get cardholder"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.getCardholder"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/com/etzhayyim/stripe/getCardholder.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-cardholder-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardholder-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.getCardholder',
                 'stripe_get_cardholder',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardholder-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-wave-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_wave',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_stripe_wave" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process id="stripe_wave" '
                 'name="stripe wave" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.wave", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="wave"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.wave"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 955,
                 '00-contracts/bpmn/com/etzhayyim/stripe/wave.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-wave-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-wave-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.wave',
                 'stripe_wave',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-wave-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-stats-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_stripe_stats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process id="stripe_stats" '
                 'name="stripe stats" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.stats", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="stats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.stats"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 961,
                 '00-contracts/bpmn/com/etzhayyim/stripe/stats.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-stats-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.stats',
                 'stripe_stats',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-commit-v1',
                 'did:web:stripe.etzhayyim.com',
                 'stripe_handle_commit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_stripe_handle_commit" '
                 'targetNamespace="https://etzhayyim.com/bpmn/stripe"><bpmn:process '
                 'id="stripe_handle_commit" name="stripe handleCommit" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.stripe.handleCommit", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="handle commit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="stripe.handleCommit"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1006,
                 '00-contracts/bpmn/com/etzhayyim/stripe/handleCommit.bpmn',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-commit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleCommit-v1',
                 'did:web:stripe.etzhayyim.com',
                 'com.etzhayyim.apps.stripe.handleCommit',
                 'stripe_handle_commit',
                 30000,
                 '',
                 '2026-04-29T22:20:00+09:00',
                 'did:web:stripe.etzhayyim.com',
                 'did:web:stripe.etzhayyim.com',
                 'sys.bpmn.seed.stripe',
                 'did:web:stripe.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleCommit-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-createCardholder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-create-cardholder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-issueCard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-issue-card-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-assignCardCredits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-assign-card-credits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardCredits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-credits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleAuthorization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-authorization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-card-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listCards-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-cards-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-freezeCard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-freeze-card-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-unfreezeCard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-unfreeze-card-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-cancelCard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-cancel-card-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-updateSpendingLimit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-update-spending-limit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-listTransactions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-list-transactions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-getCardholder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-get-cardholder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-wave-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-wave-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/stripe-handleCommit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/stripe-handle-commit-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
