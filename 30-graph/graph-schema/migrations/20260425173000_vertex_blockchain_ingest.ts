import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:blockchain.etzhayyim.com";
const ingestDid = "did:web:ingest.etzhayyim.com";
const createdAt = "2026-04-25T17:30:00Z";
const actorTag = "sys.bpmn.seed.blockchain-ingest";

const seeds = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/blockchain-bitcoin-head-delta-v1",
    bindingId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/ingest-start-blockchain-bitcoin-head-delta-v1",
    processId: "blockchain_bitcoin_head_delta",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/ingest/blockchainBitcoinHeadDelta.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/blockchain-ethereum-head-delta-v1",
    bindingId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/ingest-start-blockchain-ethereum-head-delta-v1",
    processId: "blockchain_ethereum_head_delta",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/ingest/blockchainEthereumHeadDelta.bpmn",
  },
];

function readXml(sourcePath: string): string {
  return readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_blockchain_block (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      chain VARCHAR,
      source_id VARCHAR,
      height BIGINT,
      block_hash VARCHAR,
      parent_hash VARCHAR,
      block_time VARCHAR,
      tx_count BIGINT,
      raw_artifact_uri VARCHAR,
      raw_sha256 VARCHAR,
      raw_json VARCHAR,
      canonical_status VARCHAR,
      ingested_at VARCHAR,
      run_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_block_chain_height ON vertex_blockchain_block (chain, height)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_block_hash ON vertex_blockchain_block (block_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_block_run ON vertex_blockchain_block (run_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_blockchain_tx (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      chain VARCHAR,
      source_id VARCHAR,
      block_hash VARCHAR,
      block_height BIGINT,
      tx_hash VARCHAR,
      tx_index BIGINT,
      from_addr VARCHAR,
      to_addr VARCHAR,
      value_wei VARCHAR,
      raw_artifact_uri VARCHAR,
      raw_sha256 VARCHAR,
      raw_json VARCHAR,
      canonical_status VARCHAR,
      ingested_at VARCHAR,
      run_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_tx_chain_height ON vertex_blockchain_tx (chain, block_height)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_tx_hash ON vertex_blockchain_tx (tx_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_blockchain_tx_run ON vertex_blockchain_tx (run_id)`.execute(db);

  for (const seed of seeds) {
    const body = readXml(seed.sourcePath);
    const size = Buffer.byteLength(body, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${seed.vertexId}, ${ownerDid}, ${seed.processId},
             1, ${body}, CAST(${size} AS integer), ${seed.sourcePath}, 'active',
             ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId})
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
        actor_id, write_table_allowlist
      )
      SELECT ${seed.bindingId}, ${ingestDid}, 'com.etzhayyim.apps.ingest.start',
             ${seed.processId}, 1, CAST(0 AS integer), 'active',
             ${createdAt}, 1, ${ingestDid}, ${ingestDid}, ${actorTag},
             'vertex_blockchain_block,vertex_blockchain_tx,vertex_ingest_cursor,vertex_ingest_run,vertex_ingest_artifact'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
  await sql`DROP TABLE IF EXISTS vertex_blockchain_tx`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_blockchain_block`.execute(db);
}
