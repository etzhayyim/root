#!/usr/bin/env node
/**
 * Dogecoin chain → vertex_blockchain_block + vertex_blockchain_tx adapter.
 * ADR-2605101000 §"Adapter Catalog (initial)" Tier 1.
 * Same shape as crypto-litecoin.mjs; chain_id="doge".
 */

import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:crypto_dogecoin";
const CHAIN_ID = "doge";
const ACTOR_HOST = "blockchain";
const COLLECTION_BLOCK = "com.etzhayyim.apps.blockchain.block";
const COLLECTION_TX = "com.etzhayyim.apps.blockchain.tx";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const SINCE_DAYS = Number(args["since-days"] ?? 7);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-doge-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  console.log(`[doge] run_id=${RUN_ID} project=${PROJECT} since_days=${SINCE_DAYS}`);
  const blockBinding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_blockchain_block" });
  const txBinding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_blockchain_tx" });
  console.log(`[doge] bindings ok`);

  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  // ── blocks ─────────────────────────────────────────────────────────────
  const blockCursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks" });
  const blockCursorHeight = Number((blockCursor?.cursor_value || "block_height=0").replace(/^block_height=/, "")) || 0;
  console.log(`[doge] blocks cursor=${blockCursorHeight}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks",
    cursorValue: `block_height=${blockCursorHeight}`,
    highWatermark: `now-${SINCE_DAYS}d`,
    runId: RUN_ID, status: "in_flight",
    windowFrom: `block_height>${blockCursorHeight}`, windowTo: `now-${SINCE_DAYS}d`,
  });

  let blockMaxHeight = blockCursorHeight;
  const blocksSql = `
    SELECT \`number\` AS block_height, \`hash\` AS block_hash,
           CAST(\`timestamp\` AS STRING) AS block_time,
           transaction_count, \`size\`
    FROM \`bigquery-public-data.crypto_dogecoin.blocks\`
    WHERE timestamp_month >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL ${SINCE_DAYS} DAY), MONTH)
      AND \`timestamp\` >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ${SINCE_DAYS} DAY)
      AND \`number\` > ${blockCursorHeight}
  `;
  const bRes = await projectShard({
    sql: blocksSql, project: PROJECT, maxBytes: MAX_BYTES, runId: RUN_ID,
    queryKind: "projection.doge.blocks", label: "blocks",
  });
  totalBytesBilled += bRes.bytesBilled;
  if (bRes.errorMessage) errorMessage = bRes.errorMessage;
  if (bRes.rows) {
    blockMaxHeight = bRes.rows.reduce(
      (acc, r) => (r.block_height !== null && Number(r.block_height) > acc ? Number(r.block_height) : acc),
      blockMaxHeight,
    );
    const inserts = bRes.rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION_BLOCK, `${CHAIN_ID}-${r.block_height}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      chain_id: CHAIN_ID,
      block_height: r.block_height === null ? null : Number(r.block_height),
      block_hash: r.block_hash, parent_hash: null, block_time: r.block_time,
      tx_count: r.transaction_count === null ? null : Number(r.transaction_count),
      size_bytes: r.size === null ? null : Number(r.size),
      difficulty: null, reward_satoshis: null, miner: null, props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN) {
      const written = await rwBatchInsert({
        table: "vertex_blockchain_block",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","chain_id",
                  "block_height","block_hash","parent_hash","block_time","tx_count","size_bytes",
                  "difficulty","reward_satoshis","miner","props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[doge] blocks → vertex_blockchain_block n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId: bRes.jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: "blocks",
        exportUri: `rw://vertex_blockchain_block?run=${RUN_ID}&chain=doge`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|blocks|${written}`),
        license: "Public-Chain-No-Copyright",
      });
    }
  }
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks",
    cursorValue: `block_height=${blockMaxHeight}`, highWatermark: `block_height=${blockMaxHeight}`,
    runId: RUN_ID, status: errorMessage ? "partial" : "complete",
    windowFrom: `block_height>${blockCursorHeight}`, windowTo: `now-${SINCE_DAYS}d`,
    lastRowCount: totalRows,
  });

  // ── transactions ───────────────────────────────────────────────────────
  const txCursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions" });
  const txCursorHeight = Number((txCursor?.cursor_value || "block_height=0").replace(/^block_height=/, "")) || 0;
  console.log(`[doge] transactions cursor=${txCursorHeight}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions",
    cursorValue: `block_height=${txCursorHeight}`, highWatermark: `now-${SINCE_DAYS}d`,
    runId: RUN_ID, status: "in_flight",
    windowFrom: `block_height>${txCursorHeight}`, windowTo: `now-${SINCE_DAYS}d`,
  });

  let txMaxHeight = txCursorHeight;
  const txSql = `
    SELECT \`hash\` AS tx_hash, block_hash, block_number AS block_height,
           CAST(block_timestamp AS STRING) AS block_time,
           input_count, output_count, input_value, output_value, fee, is_coinbase
    FROM \`bigquery-public-data.crypto_dogecoin.transactions\`
    WHERE block_timestamp_month >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL ${SINCE_DAYS} DAY), MONTH)
      AND block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ${SINCE_DAYS} DAY)
      AND block_number > ${txCursorHeight}
  `;
  const tRes = await projectShard({
    sql: txSql, project: PROJECT, maxBytes: MAX_BYTES, runId: RUN_ID,
    queryKind: "projection.doge.transactions", label: "transactions",
  });
  totalBytesBilled += tRes.bytesBilled;
  if (tRes.errorMessage) errorMessage = tRes.errorMessage;
  if (tRes.rows) {
    txMaxHeight = tRes.rows.reduce(
      (acc, r) => (r.block_height !== null && Number(r.block_height) > acc ? Number(r.block_height) : acc),
      txMaxHeight,
    );
    const inserts = tRes.rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION_TX, `${CHAIN_ID}-${r.tx_hash}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      chain_id: CHAIN_ID, tx_hash: r.tx_hash,
      block_height: r.block_height === null ? null : Number(r.block_height),
      block_hash: r.block_hash, block_time: r.block_time,
      input_count: r.input_count === null ? null : Number(r.input_count),
      output_count: r.output_count === null ? null : Number(r.output_count),
      input_value_satoshis: r.input_value === null ? null : Math.round(Number(r.input_value)),
      output_value_satoshis: r.output_value === null ? null : Math.round(Number(r.output_value)),
      fee_satoshis: r.fee === null ? null : Math.round(Number(r.fee)),
      is_coinbase: r.is_coinbase === null ? null : String(Boolean(r.is_coinbase)),
      props: null, actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN) {
      const written = await rwBatchInsert({
        table: "vertex_blockchain_tx",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","chain_id","tx_hash",
                  "block_height","block_hash","block_time","input_count","output_count",
                  "input_value_satoshis","output_value_satoshis","fee_satoshis","is_coinbase",
                  "props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[doge] transactions → vertex_blockchain_tx n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId: tRes.jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: "transactions",
        exportUri: `rw://vertex_blockchain_tx?run=${RUN_ID}&chain=doge`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|transactions|${written}`),
        license: "Public-Chain-No-Copyright",
      });
    }
  }
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions",
    cursorValue: `block_height=${txMaxHeight}`, highWatermark: `block_height=${txMaxHeight}`,
    runId: RUN_ID, status: errorMessage ? "partial" : "complete",
    windowFrom: `block_height>${txCursorHeight}`, windowTo: `now-${SINCE_DAYS}d`,
    lastRowCount: totalRows,
  });

  if (!DRY_RUN) await rwFlush();
  await recordRunHeader({
    runId: RUN_ID, mode: "projection", project: PROJECT,
    providerFilter: "bigquery-public-data", datasetFilter: DATASET_ID,
    startedAt: runStartedAt, finishedAt: new Date().toISOString(),
    status: errorMessage ? "completed_with_errors" : "completed",
    datasetsSeen: 1, tablesSeen: 2, samplesTaken: totalRows,
    totalBytesBilled, maxBytesBilledPerQuery: Number(MAX_BYTES),
    monthlyScanBudgetTib: Number(blockBinding.scan_budget_tib ?? 0.1),
    monthlyScanUsedTib: totalBytesBilled / 1024 ** 4,
    approvalNote: blockBinding.approved_by ?? null, errorMessage,
  });
  console.log(`[doge] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

async function projectShard({ sql, project, maxBytes, runId, queryKind, label }) {
  console.log(`[doge] table=${label}`);
  let r;
  try {
    r = await bqQueryAll({ project, query: sql, maximumBytesBilled: maxBytes, queryKind });
    if (!r.ok) throw r.error;
  } catch (e) {
    console.error(`[doge] ${label} query failed: ${e.message}`);
    return { errorMessage: String(e.message).slice(0, 1000), bytesBilled: 0, rows: null };
  }
  await recordIngestJob({
    jobId: r.jobId, runId, queryKind, queryHash: r.queryHash,
    project, location: "US",
    maximumBytesBilled: maxBytes, totalBytesBilled: r.bytesBilled,
    cacheHit: false, status: "done", errorReason: null, errorMessage: null,
    startedAt: r.startedAt, finishedAt: r.finishedAt,
  });
  const rows = flattenRows(r.schema, r.rows);
  console.log(`[doge] ${label} rows=${rows.length} bytes_billed=${r.bytesBilled}`);
  return { rows, bytesBilled: r.bytesBilled, jobId: r.jobId };
}

main().catch(async (e) => {
  console.error(`[doge] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
