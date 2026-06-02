"""Captured from Kysely migration 20260429205000_seed_collector_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429205000_seed_collector_bpmn_actors"
down_revision = 'r_20260429204000_seed_arms_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-netintel-dns-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_collect_netintel_dns',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_collect_netintel_dns" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_collect_netintel_dns" '
                 'name="collector collectNetintelDns" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.collectNetintelDns", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="collect netintel '
                 'dns"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.collectNetintelDns"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1146,
                 '00-contracts/bpmn/com/etzhayyim/collector/collectNetintelDns.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-netintel-dns-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-netintel-dns-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.collectNetintelDns',
                 'collector_collect_netintel_dns',
                 120000,
                 'vertex_collector_run,vertex_collector_dns_observation,vertex_collector_dns_snapshot,vertex_collector_organization',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-netintel-dns-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-btc-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_collect_blockchain_btc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_collect_blockchain_btc" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_collect_blockchain_btc" '
                 'name="collector collectBlockchainBtc" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.collectBlockchainBtc", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="collect blockchain '
                 'btc"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.collectBlockchainBtc"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1158,
                 '00-contracts/bpmn/com/etzhayyim/collector/collectBlockchainBtc.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-btc-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-btc-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.collectBlockchainBtc',
                 'collector_collect_blockchain_btc',
                 120000,
                 'vertex_collector_run,vertex_collector_blockchain_actor,vertex_collector_risk_signal',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-btc-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-eth-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_collect_blockchain_eth',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_collect_blockchain_eth" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_collect_blockchain_eth" '
                 'name="collector collectBlockchainEth" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.collectBlockchainEth", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="collect blockchain '
                 'eth"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.collectBlockchainEth"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1158,
                 '00-contracts/bpmn/com/etzhayyim/collector/collectBlockchainEth.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-eth-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-eth-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.collectBlockchainEth',
                 'collector_collect_blockchain_eth',
                 120000,
                 'vertex_collector_run,vertex_collector_blockchain_actor,vertex_collector_risk_signal',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-eth-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-common-crawl-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_collect_common_crawl',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_collect_common_crawl" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_collect_common_crawl" '
                 'name="collector collectCommonCrawl" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.collectCommonCrawl", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="collect common '
                 'crawl"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.collectCommonCrawl"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1146,
                 '00-contracts/bpmn/com/etzhayyim/collector/collectCommonCrawl.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-common-crawl-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-common-crawl-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.collectCommonCrawl',
                 'collector_collect_common_crawl',
                 120000,
                 'vertex_collector_archive_snapshot',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-common-crawl-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-archive-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_collect_archive',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_collect_archive" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_collect_archive" '
                 'name="collector collectArchive" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.collectArchive", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="collect '
                 'archive"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.collectArchive"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/com/etzhayyim/collector/collectArchive.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-archive-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-archive-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.collectArchive',
                 'collector_collect_archive',
                 120000,
                 'vertex_collector_archive_snapshot',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-archive-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-ingest-scan-result-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_ingest_scan_result',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_ingest_scan_result" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_ingest_scan_result" '
                 'name="collector ingestScanResult" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.collector.ingestScanResult", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="ingest scan '
                 'result"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.ingestScanResult"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1133,
                 '00-contracts/bpmn/com/etzhayyim/collector/ingestScanResult.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-ingest-scan-result-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-ingest-scan-result-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.ingestScanResult',
                 'collector_ingest_scan_result',
                 30000,
                 'vertex_collector_scan_result',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-ingest-scan-result-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-trigger-run-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_trigger_run',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_trigger_run" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_trigger_run" name="collector '
                 'triggerRun" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.collector.triggerRun", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="trigger run"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.triggerRun"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/collector/triggerRun.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-trigger-run-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-trigger-run-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.triggerRun',
                 'collector_trigger_run',
                 120000,
                 'vertex_collector_run,vertex_collector_dns_observation,vertex_collector_dns_snapshot,vertex_collector_organization,vertex_collector_blockchain_actor,vertex_collector_archive_snapshot',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-trigger-run-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-get-dashboard-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_get_dashboard',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_get_dashboard" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_get_dashboard" name="collector '
                 'getDashboard" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.collector.getDashboard", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get dashboard"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.getDashboard"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/com/etzhayyim/collector/getDashboard.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-get-dashboard-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-get-dashboard-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.getDashboard',
                 'collector_get_dashboard',
                 30000,
                 '',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-get-dashboard-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-list-jobs-v1',
                 'did:web:collector.etzhayyim.com',
                 'collector_list_jobs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_collector_list_jobs" '
                 'targetNamespace="https://etzhayyim.com/bpmn/collector" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="collector_list_jobs" name="collector '
                 'listJobs" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.collector.listJobs", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list jobs"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="collector.listJobs"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/collector/listJobs.bpmn',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-list-jobs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-list-jobs-v1',
                 'did:web:collector.etzhayyim.com',
                 'com.etzhayyim.apps.collector.listJobs',
                 'collector_list_jobs',
                 30000,
                 '',
                 '2026-04-29T20:50:00+09:00',
                 'did:web:collector.etzhayyim.com',
                 'did:web:collector.etzhayyim.com',
                 'sys.bpmn.seed.collector',
                 'did:web:collector.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-list-jobs-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-netintel-dns-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-netintel-dns-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-btc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-btc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-blockchain-eth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-blockchain-eth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-common-crawl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-common-crawl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-collect-archive-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-collect-archive-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-ingest-scan-result-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-ingest-scan-result-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-trigger-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-trigger-run-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/collector-list-jobs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/collector-list-jobs-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
