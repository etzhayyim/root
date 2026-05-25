"""Captured from Kysely migration 20260429216100_seed_credits_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429216100_seed_credits_bpmn_actors"
down_revision = 'r_20260429216000_credits_zeebe_support'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-check-spend-allowed-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_check_spend_allowed',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_check_spend_allowed" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_check_spend_allowed" '
                 'name="credits checkSpendAllowed" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "app.etzhayyim.apps.credits.checkSpendAllowed", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="check spend '
                 'allowed"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.checkSpendAllowed"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1127,
                 '00-contracts/bpmn/ai/gftd/credits/checkSpendAllowed.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-check-spend-allowed-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-checkSpendAllowed-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.checkSpendAllowed',
                 'credits_check_spend_allowed',
                 30000,
                 '',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-checkSpendAllowed-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-spend-credits-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_spend_credits',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_spend_credits" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_spend_credits" name="credits '
                 'spendCredits" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.credits.spendCredits", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="spend credits"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.spendCredits"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/ai/gftd/credits/spendCredits.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-spend-credits-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-spendCredits-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.spendCredits',
                 'credits_spend_credits',
                 30000,
                 'vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-spendCredits-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-compute-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_reward_from_compute',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_reward_from_compute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_reward_from_compute" '
                 'name="credits rewardFromCompute" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "app.etzhayyim.apps.credits.rewardFromCompute", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="reward from '
                 'compute"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.rewardFromCompute"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1127,
                 '00-contracts/bpmn/ai/gftd/credits/rewardFromCompute.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-compute-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromCompute-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.rewardFromCompute',
                 'credits_reward_from_compute',
                 30000,
                 'vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromCompute-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-hc-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_reward_from_hc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_reward_from_hc" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_reward_from_hc" name="credits '
                 'rewardFromHC" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.credits.rewardFromHC", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="reward from '
                 'hc"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.rewardFromHC"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1097,
                 '00-contracts/bpmn/ai/gftd/credits/rewardFromHC.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-hc-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromHC-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.rewardFromHC',
                 'credits_reward_from_hc',
                 30000,
                 'vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromHC-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-process-commit-spend-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_process_commit_spend',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_process_commit_spend" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_process_commit_spend" '
                 'name="credits processCommitSpend" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "app.etzhayyim.apps.credits.processCommitSpend", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="process commit '
                 'spend"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.processCommitSpend"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1133,
                 '00-contracts/bpmn/ai/gftd/credits/processCommitSpend.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-process-commit-spend-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-processCommitSpend-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.processCommitSpend',
                 'credits_process_commit_spend',
                 30000,
                 'vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-processCommitSpend-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-heartbeat-v1',
                 'did:web:credits.etzhayyim.com',
                 'credits_heartbeat',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_credits_heartbeat" '
                 'targetNamespace="https://etzhayyim.com/bpmn/credits" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="credits_heartbeat" name="credits '
                 'heartbeat" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.credits.heartbeat", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="heartbeat"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="credits.heartbeat"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1073,
                 '00-contracts/bpmn/ai/gftd/credits/heartbeat.bpmn',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-heartbeat-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-heartbeat-v1',
                 'did:web:credits.etzhayyim.com',
                 'app.etzhayyim.apps.credits.heartbeat',
                 'credits_heartbeat',
                 30000,
                 '',
                 '2026-04-29T22:01:00+09:00',
                 'did:web:credits.etzhayyim.com',
                 'did:web:credits.etzhayyim.com',
                 'sys.bpmn.seed.credits',
                 'did:web:credits.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-heartbeat-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-checkSpendAllowed-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-check-spend-allowed-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-spendCredits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-spend-credits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromCompute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-compute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-rewardFromHC-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-reward-from-hc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-processCommitSpend-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-process-commit-spend-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-heartbeat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-heartbeat-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
