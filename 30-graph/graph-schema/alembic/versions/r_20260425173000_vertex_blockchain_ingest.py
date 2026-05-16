"""Captured from Kysely migration 20260425173000_vertex_blockchain_ingest."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425173000_vertex_blockchain_ingest"
down_revision = 'r_20260425172000_seed_pharma_supply_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_blockchain_block (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      chain VARCHAR,\n'
         '      source_id VARCHAR,\n'
         '      height BIGINT,\n'
         '      block_hash VARCHAR,\n'
         '      parent_hash VARCHAR,\n'
         '      block_time VARCHAR,\n'
         '      tx_count BIGINT,\n'
         '      raw_artifact_uri VARCHAR,\n'
         '      raw_sha256 VARCHAR,\n'
         '      raw_json VARCHAR,\n'
         '      canonical_status VARCHAR,\n'
         '      ingested_at VARCHAR,\n'
         '      run_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_block_chain_height ON vertex_blockchain_block '
         '(chain, height)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_block_hash ON vertex_blockchain_block '
         '(block_hash)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_block_run ON vertex_blockchain_block (run_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_blockchain_tx (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      chain VARCHAR,\n'
         '      source_id VARCHAR,\n'
         '      block_hash VARCHAR,\n'
         '      block_height BIGINT,\n'
         '      tx_hash VARCHAR,\n'
         '      tx_index BIGINT,\n'
         '      from_addr VARCHAR,\n'
         '      to_addr VARCHAR,\n'
         '      value_wei VARCHAR,\n'
         '      raw_artifact_uri VARCHAR,\n'
         '      raw_sha256 VARCHAR,\n'
         '      raw_json VARCHAR,\n'
         '      canonical_status VARCHAR,\n'
         '      ingested_at VARCHAR,\n'
         '      run_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_tx_chain_height ON vertex_blockchain_tx '
         '(chain, block_height)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_tx_hash ON vertex_blockchain_tx (tx_hash)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_blockchain_tx_run ON vertex_blockchain_tx (run_id)',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             1, $4, CAST($5 AS integer), $6, 'active',\n"
         '             $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-bitcoin-head-delta-v1',
                 'did:web:blockchain.gftd.ai',
                 'blockchain_bitcoin_head_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_blockchain_bitcoin_head_delta"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/ingest/blockchain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="blockchain_bitcoin_head_delta" name="blockchain bitcoin head '
                 'delta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="start">\n'
                 '      <bpmn:outgoing>Flow_Health</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health" sourceRef="Start" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="Task_Health" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest bitcoin head">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="blockchain.head.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=&quot;bitcoin-mainnet&quot;" '
                 'target="sourceId"/>\n'
                 '          <zeebe:input source="=string(inputJson)" target="inputJson"/>\n'
                 '          <zeebe:input source="=3" target="maxBlocks"/>\n'
                 '          <zeebe:output source="=blocksRead" target="recordsRead"/>\n'
                 '          <zeebe:output source="=rowsWritten" target="recordsWritten"/>\n'
                 '          <zeebe:output source="=transactionsRead" target="transactionsRead"/>\n'
                 '          <zeebe:output source="=latest" target="latestHeight"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bitcoin ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:blockchain.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;blockchain.bitcoin.head.delta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, sourceId: sourceId, recordsRead: '
                 'recordsRead, recordsWritten: recordsWritten, transactionsRead: transactionsRead, '
                 'latestHeight: latestHeight}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_MarkCompleted</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_MarkCompleted" sourceRef="Task_Audit" '
                 'targetRef="Task_MarkCompleted"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_MarkCompleted" name="mark run completed">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ingest.run.markCompleted"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=&quot;completed&quot;" target="status"/>\n'
                 '          <zeebe:input source="=recordsRead" target="recordsRead"/>\n'
                 '          <zeebe:input source="=recordsWritten" target="recordsWritten"/>\n'
                 '          <zeebe:input source="=0" target="recordsSkipped"/>\n'
                 '          <zeebe:input source="=0" target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_MarkCompleted</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_MarkCompleted" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="completed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3918,
                 '00-contracts/bpmn/ai/gftd/ingest/blockchainBitcoinHeadDelta.bpmn',
                 '2026-04-25T17:30:00Z',
                 'did:web:blockchain.gftd.ai',
                 'did:web:blockchain.gftd.ai',
                 'sys.bpmn.seed.blockchain-ingest',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-bitcoin-head-delta-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, write_table_allowlist\n'
         '      )\n'
         "      SELECT $1, $2, 'ai.gftd.apps.ingest.start',\n"
         "             $3, 1, CAST(0 AS integer), 'active',\n"
         '             $4, 1, $5, $6, $7,\n'
         '             '
         "'vertex_blockchain_block,vertex_blockchain_tx,vertex_ingest_cursor,vertex_ingest_run,vertex_ingest_artifact'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-bitcoin-head-delta-v1',
                 'did:web:ingest.gftd.ai',
                 'blockchain_bitcoin_head_delta',
                 '2026-04-25T17:30:00Z',
                 'did:web:ingest.gftd.ai',
                 'did:web:ingest.gftd.ai',
                 'sys.bpmn.seed.blockchain-ingest',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-bitcoin-head-delta-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             1, $4, CAST($5 AS integer), $6, 'active',\n"
         '             $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-ethereum-head-delta-v1',
                 'did:web:blockchain.gftd.ai',
                 'blockchain_ethereum_head_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_blockchain_ethereum_head_delta"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/ingest/blockchain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="blockchain_ethereum_head_delta" name="blockchain ethereum '
                 'head delta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="start">\n'
                 '      <bpmn:outgoing>Flow_Health</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health" sourceRef="Start" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="Task_Health" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest ethereum head">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="blockchain.head.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=&quot;ethereum-mainnet&quot;" '
                 'target="sourceId"/>\n'
                 '          <zeebe:input source="=string(inputJson)" target="inputJson"/>\n'
                 '          <zeebe:input source="=3" target="maxBlocks"/>\n'
                 '          <zeebe:output source="=blocksRead" target="recordsRead"/>\n'
                 '          <zeebe:output source="=rowsWritten" target="recordsWritten"/>\n'
                 '          <zeebe:output source="=transactionsRead" target="transactionsRead"/>\n'
                 '          <zeebe:output source="=latest" target="latestHeight"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ethereum ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:blockchain.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;blockchain.ethereum.head.delta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, sourceId: sourceId, recordsRead: '
                 'recordsRead, recordsWritten: recordsWritten, transactionsRead: transactionsRead, '
                 'latestHeight: latestHeight}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_MarkCompleted</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_MarkCompleted" sourceRef="Task_Audit" '
                 'targetRef="Task_MarkCompleted"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_MarkCompleted" name="mark run completed">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ingest.run.markCompleted"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=&quot;completed&quot;" target="status"/>\n'
                 '          <zeebe:input source="=recordsRead" target="recordsRead"/>\n'
                 '          <zeebe:input source="=recordsWritten" target="recordsWritten"/>\n'
                 '          <zeebe:input source="=0" target="recordsSkipped"/>\n'
                 '          <zeebe:input source="=0" target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_MarkCompleted</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_MarkCompleted" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="completed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3925,
                 '00-contracts/bpmn/ai/gftd/ingest/blockchainEthereumHeadDelta.bpmn',
                 '2026-04-25T17:30:00Z',
                 'did:web:blockchain.gftd.ai',
                 'did:web:blockchain.gftd.ai',
                 'sys.bpmn.seed.blockchain-ingest',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-ethereum-head-delta-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, write_table_allowlist\n'
         '      )\n'
         "      SELECT $1, $2, 'ai.gftd.apps.ingest.start',\n"
         "             $3, 1, CAST(0 AS integer), 'active',\n"
         '             $4, 1, $5, $6, $7,\n'
         '             '
         "'vertex_blockchain_block,vertex_blockchain_tx,vertex_ingest_cursor,vertex_ingest_run,vertex_ingest_artifact'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-ethereum-head-delta-v1',
                 'did:web:ingest.gftd.ai',
                 'blockchain_ethereum_head_delta',
                 '2026-04-25T17:30:00Z',
                 'did:web:ingest.gftd.ai',
                 'did:web:ingest.gftd.ai',
                 'sys.bpmn.seed.blockchain-ingest',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-ethereum-head-delta-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-bitcoin-head-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-bitcoin-head-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-blockchain-ethereum-head-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/blockchain-ethereum-head-delta-v1']},
 {'sql': 'DROP TABLE IF EXISTS vertex_blockchain_tx', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_blockchain_block', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
