#!/usr/bin/env node
/**
 * Litecoin chain → vertex_blockchain_block + vertex_blockchain_tx adapter.
 *
 * ADR-2605101000 §"Adapter Catalog (initial)" Tier 1.
 *
 * Source: bigquery-public-data:crypto_litecoin (Public-Chain-No-Copyright).
 *
 * Schema in BQ:
 *   crypto_litecoin.blocks
 *     hash, size, stripped_size, weight, number, version, merkle_root,
 *     timestamp, timestamp_month, nonce, bits, coinbase_param, transaction_count
 *   crypto_litecoin.transactions
 *     hash, size, virtual_size, version, lock_time, block_hash, block_number,
 *     block_timestamp, block_timestamp_month, input_count, output_count,
 *     input_value, output_value, is_coinbase, fee
 *
 * Strategy:
 *   - Bound by `--since-days` (default 7) on `block_timestamp`.
 *   - Partition predicate via `block_timestamp_month >= ...` to exploit
 *     the table's clustering and keep maximumBytesBilled small.
 *   - chain_id = "ltc" (shared shape with dogecoin / ethereum)
 *
 * Usage:
 *   node 70-tools/scripts/projection/bigquery/crypto-litecoin.mjs \
 *     --project etzhayyim-ws-ingest \
 *     [--since-days 7] \
 *     [--max-bytes-billed-per-query 107374182400] \
 *     [--dry-run]
 */

import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";

const DATASET_ID = "bigquery-public-data:crypto_litecoin";
const CHAIN_ID = "ltc";
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
  const RUN_ID = args["run-id"] ?? `p2-ltc-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  console.log(`[ltc] run_id=${RUN_ID} project=${PROJECT} since_days=${SINCE_DAYS} dry_run=${DRY_RUN}`);

  // Bindings — block + tx are two separate decided bindings.
  const blockBinding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_blockchain_block" });
  const txBinding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_blockchain_tx" });
  console.log(`[ltc] bindings ok block_mode=${blockBinding.ingest_mode} tx_mode=${txBinding.ingest_mode}`);

  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0;
  let totalRows = 0;
  let errorMessage = null;

  // ── blocks ─────────────────────────────────────────────────────────────
  // Cursor: block_height = max already committed (or 0 on first run).
  const blockCursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks" });
  const blockCursorHeight = Number((blockCursor?.cursor_value || "block_height=0").replace(/^block_height=/, "")) || 0;
  console.log(`[ltc] blocks cursor=${blockCursorHeight} (resume? ${blockCursor ? "yes" : "no"})`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks",
    cursorValue: `block_height=${blockCursorHeight}`,
    highWatermark: `block_height=+inf-${SINCE_DAYS}d`,
    runId: RUN_ID, status: "in_flight",
    windowFrom: `block_height>${blockCursorHeight}`,
    windowTo: `now-${SINCE_DAYS}d`,
  });

  const blocksSql = `
    SELECT
      \`number\` AS block_height,
      \`hash\` AS block_hash,
      version,
      merkle_root,
      CAST(\`timestamp\` AS STRING) AS block_time,
      CAST(timestamp_month AS STRING) AS timestamp_month,
      transaction_count,
      \`size\`,
      nonce,
      bits
    FROM \`bigquery-public-data.crypto_litecoin.blocks\`
    WHERE timestamp_month >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL ${SINCE_DAYS} DAY), MONTH)
      AND \`timestamp\` >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ${SINCE_DAYS} DAY)
      AND \`number\` > ${blockCursorHeight}
  `;

  let blockMaxHeight = blockCursorHeight;
  await projectTable({
    label: "blocks",
    sql: blocksSql,
    project: PROJECT, maxBytes: MAX_BYTES, runId: RUN_ID,
    onRows: async (rows) => {
      const observedAt = new Date().toISOString();
      blockMaxHeight = rows.reduce(
        (acc, r) => (r.block_height !== null && Number(r.block_height) > acc ? Number(r.block_height) : acc),
        blockMaxHeight,
      );
      const inserts = rows.map((r) => ({
        vertex_id: vertexId(ACTOR_HOST, COLLECTION_BLOCK, `${CHAIN_ID}-${r.block_height}`),
        sensitivity_ord: 1,
        owner_did: COLLECTOR_DID,
        source_dataset_id: DATASET_ID,
        chain_id: CHAIN_ID,
        block_height: r.block_height === null ? null : Number(r.block_height),
        block_hash: r.block_hash,
        parent_hash: null,
        block_time: r.block_time,
        tx_count: r.transaction_count === null ? null : Number(r.transaction_count),
        size_bytes: r.size === null ? null : Number(r.size),
        difficulty: null,
        reward_satoshis: null,
        miner: null,
        props: null,
        actor_did: COLLECTOR_DID,
        org_did: COLLECTOR_DID,
        at_did: null,
        created_at: observedAt,
      }));
      if (DRY_RUN) return inserts.length;
      const written = await rwBatchInsert({
        table: "vertex_blockchain_block",
        columns: [
          "vertex_id","sensitivity_ord","owner_did","source_dataset_id",
          "chain_id","block_height","block_hash","parent_hash","block_time",
          "tx_count","size_bytes","difficulty","reward_satoshis","miner",
          "props","actor_did","org_did","at_did","created_at",
        ],
        rows: inserts,
        chunkSize: 250,
        // Mid-run cursor advance: after each periodic FLUSH commits a
        // batch, persist the max block_height so a crash resumes from the
        // last durable point instead of re-scanning the full window.
        onChunkFlush: async ({ slice, totalWritten }) => {
          const maxH = slice.reduce(
            (a, r) => (r.block_height !== null && r.block_height > a ? r.block_height : a),
            blockCursorHeight,
          );
          if (maxH > blockCursorHeight) {
            await saveCursor({
              ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks",
              cursorValue: `block_height=${maxH}`,
              highWatermark: `block_height=${maxH}`,
              runId: RUN_ID, status: "partial",
              windowFrom: `block_height>${blockCursorHeight}`,
              windowTo: `now-${SINCE_DAYS}d`,
              lastRowCount: totalWritten,
            });
          }
        },
      });
      return written;
    },
    onResult: (r) => { totalBytesBilled += r.bytesBilled; },
  }).then((res) => {
    if (res?.errorMessage) errorMessage = res.errorMessage;
    if (res?.rowsWritten) totalRows += res.rowsWritten;
  });
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "blocks",
    cursorValue: `block_height=${blockMaxHeight}`,
    highWatermark: `block_height=${blockMaxHeight}`,
    runId: RUN_ID, status: errorMessage ? "partial" : "complete",
    windowFrom: `block_height>${blockCursorHeight}`,
    windowTo: `now-${SINCE_DAYS}d`,
    lastRowCount: totalRows,
  });

  // ── transactions ───────────────────────────────────────────────────────
  const txCursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions" });
  const txCursorHeight = Number((txCursor?.cursor_value || "block_height=0").replace(/^block_height=/, "")) || 0;
  console.log(`[ltc] transactions cursor=${txCursorHeight} (resume? ${txCursor ? "yes" : "no"})`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions",
    cursorValue: `block_height=${txCursorHeight}`,
    highWatermark: `block_height=+inf-${SINCE_DAYS}d`,
    runId: RUN_ID, status: "in_flight",
    windowFrom: `block_height>${txCursorHeight}`,
    windowTo: `now-${SINCE_DAYS}d`,
  });

  const txSql = `
    SELECT
      \`hash\` AS tx_hash,
      block_hash, block_number AS block_height,
      CAST(block_timestamp AS STRING) AS block_time,
      input_count, output_count,
      input_value, output_value, fee,
      is_coinbase
    FROM \`bigquery-public-data.crypto_litecoin.transactions\`
    WHERE block_timestamp_month >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL ${SINCE_DAYS} DAY), MONTH)
      AND block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ${SINCE_DAYS} DAY)
      AND block_number > ${txCursorHeight}
  `;

  let txMaxHeight = txCursorHeight;
  await projectTable({
    label: "transactions",
    sql: txSql,
    project: PROJECT, maxBytes: MAX_BYTES, runId: RUN_ID,
    onRows: async (rows) => {
      const observedAt = new Date().toISOString();
      txMaxHeight = rows.reduce(
        (acc, r) => (r.block_height !== null && Number(r.block_height) > acc ? Number(r.block_height) : acc),
        txMaxHeight,
      );
      const inserts = rows.map((r) => ({
        vertex_id: vertexId(ACTOR_HOST, COLLECTION_TX, `${CHAIN_ID}-${r.tx_hash}`),
        sensitivity_ord: 1,
        owner_did: COLLECTOR_DID,
        source_dataset_id: DATASET_ID,
        chain_id: CHAIN_ID,
        tx_hash: r.tx_hash,
        block_height: r.block_height === null ? null : Number(r.block_height),
        block_hash: r.block_hash,
        block_time: r.block_time,
        input_count: r.input_count === null ? null : Number(r.input_count),
        output_count: r.output_count === null ? null : Number(r.output_count),
        input_value_satoshis: r.input_value === null ? null : Math.round(Number(r.input_value)),
        output_value_satoshis: r.output_value === null ? null : Math.round(Number(r.output_value)),
        fee_satoshis: r.fee === null ? null : Math.round(Number(r.fee)),
        is_coinbase: r.is_coinbase === null || r.is_coinbase === undefined
          ? null : String(Boolean(r.is_coinbase)),
        props: null,
        actor_did: COLLECTOR_DID,
        org_did: COLLECTOR_DID,
        at_did: null,
        created_at: observedAt,
      }));
      if (DRY_RUN) return inserts.length;
      const written = await rwBatchInsert({
        table: "vertex_blockchain_tx",
        columns: [
          "vertex_id","sensitivity_ord","owner_did","source_dataset_id",
          "chain_id","tx_hash","block_height","block_hash","block_time",
          "input_count","output_count","input_value_satoshis",
          "output_value_satoshis","fee_satoshis","is_coinbase",
          "props","actor_did","org_did","at_did","created_at",
        ],
        rows: inserts,
        chunkSize: 250,
        onChunkFlush: async ({ slice, totalWritten }) => {
          const maxH = slice.reduce(
            (a, r) => (r.block_height !== null && r.block_height > a ? r.block_height : a),
            txCursorHeight,
          );
          if (maxH > txCursorHeight) {
            await saveCursor({
              ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions",
              cursorValue: `block_height=${maxH}`,
              highWatermark: `block_height=${maxH}`,
              runId: RUN_ID, status: "partial",
              windowFrom: `block_height>${txCursorHeight}`,
              windowTo: `now-${SINCE_DAYS}d`,
              lastRowCount: totalWritten,
            });
          }
        },
      });
      return written;
    },
    onResult: (r) => { totalBytesBilled += r.bytesBilled; },
  }).then((res) => {
    if (res?.errorMessage) errorMessage = res.errorMessage;
    if (res?.rowsWritten) totalRows += res.rowsWritten;
  });
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "transactions",
    cursorValue: `block_height=${txMaxHeight}`,
    highWatermark: `block_height=${txMaxHeight}`,
    runId: RUN_ID, status: errorMessage ? "partial" : "complete",
    windowFrom: `block_height>${txCursorHeight}`,
    windowTo: `now-${SINCE_DAYS}d`,
    lastRowCount: totalRows,
  });

  if (!DRY_RUN) await rwFlush();

  await recordRunHeader({
    runId: RUN_ID, mode: "projection", project: PROJECT,
    providerFilter: "bigquery-public-data",
    datasetFilter: DATASET_ID,
    startedAt: runStartedAt, finishedAt: new Date().toISOString(),
    status: errorMessage ? "completed_with_errors" : "completed",
    datasetsSeen: 1, tablesSeen: 2, samplesTaken: totalRows,
    totalBytesBilled,
    maxBytesBilledPerQuery: Number(MAX_BYTES),
    monthlyScanBudgetTib: Number(blockBinding.scan_budget_tib ?? 0.1),
    monthlyScanUsedTib: totalBytesBilled / 1024 ** 4,
    approvalNote: blockBinding.approved_by ?? null,
    errorMessage,
  });

  console.log(`[ltc] === COMPLETE ===`);
  console.log(`[ltc] total_rows=${totalRows} total_bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

async function projectTable({ label, sql, project, maxBytes, runId, onRows, onResult }) {
  console.log(`[ltc] table=${label}`);
  const startedAt = new Date().toISOString();
  let result;
  try {
    result = await bqQueryAll({
      project, query: sql, maximumBytesBilled: maxBytes, queryKind: `projection.ltc.${label}`,
    });
    if (!result.ok) throw result.error;
  } catch (e) {
    console.error(`[ltc] ${label} query failed: ${e.message}`);
    return { errorMessage: String(e.message).slice(0, 1000) };
  }
  onResult({ bytesBilled: result.bytesBilled });

  await recordIngestJob({
    jobId: result.jobId, runId, queryKind: `projection.ltc.${label}`, queryHash: result.queryHash,
    project, location: "US",
    maximumBytesBilled: maxBytes, totalBytesBilled: result.bytesBilled,
    cacheHit: false, status: "done",
    errorReason: null, errorMessage: null,
    startedAt: result.startedAt, finishedAt: result.finishedAt,
  });

  const rows = flattenRows(result.schema, result.rows);
  if (rows.length === 0) {
    console.warn(`[ltc] ${label} returned 0 rows`);
    return { rowsWritten: 0 };
  }
  console.log(`[ltc] ${label} rows=${rows.length} bytes_billed=${result.bytesBilled}`);
  const written = await onRows(rows);
  await recordExportArtifact({
    runId, jobId: result.jobId, artifactKind: "bigquery.projection",
    datasetId: DATASET_ID, table: label,
    exportUri: `rw://vertex_blockchain_${label === "blocks" ? "block" : "tx"}?run=${runId}&table=${label}`,
    format: "rw-inline", byteSize: null, rowCount: written,
    sha: sha256(`${runId}|${label}|${written}`),
    license: "Public-Chain-No-Copyright",
  });
  console.log(`[ltc] ${label} → RW INSERT n=${written}`);
  return { rowsWritten: written };
}

main().catch(async (e) => {
  console.error(`[ltc] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
