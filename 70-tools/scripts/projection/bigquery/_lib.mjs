/**
 * Shared helpers for `70-tools/scripts/projection/bigquery/*.mjs` P2 adapters.
 *
 * ADR-2605101000 §D1 adapter contract:
 *   1. validate edge_dataset_produces_vertex_type binding exists
 *   2. emit narrow projection query / queries (no SELECT *, partition filter
 *      where available, maximumBytesBilled enforced)
 *   3. write rows to RW vertex_ / edge_ tables via Kysely / pg.Pool
 *   4. record vertex_bigquery_ingest_job + vertex_ingest_artifact lineage
 *   5. return summary { rows_written, bytes_billed, cost_usd, errors }
 */

import { createHash, randomUUID } from "node:crypto";
import { execSync } from "node:child_process";

export const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
export const COLLECTOR_DID = "did:web:bigquery.etzhayyim.com";
export const BQ_API = "https://bigquery.googleapis.com/bigquery/v2";

// ── auth ───────────────────────────────────────────────────────────────────

let _token = null;
export function getBqToken() {
  if (_token) return _token;
  if (process.env.BQ_ACCESS_TOKEN) { _token = process.env.BQ_ACCESS_TOKEN; return _token; }
  _token = execSync("gcloud auth application-default print-access-token", {
    encoding: "utf8",
  }).trim();
  return _token;
}

export function refreshBqToken() {
  _token = null;
  return getBqToken();
}

// ── BigQuery REST ──────────────────────────────────────────────────────────

export async function bqFetch(path, init = {}, { project } = {}) {
  const url = path.startsWith("http")
    ? path
    : `${BQ_API}${path.startsWith("/") ? path : `/projects/${project}/${path}`}`;
  const resp = await fetch(url, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${getBqToken()}`,
      "Content-Type": "application/json",
    },
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`BQ ${resp.status} ${path}: ${text.slice(0, 500)}`);
  }
  return resp.json();
}

export async function bqQueryAll({
  project, location = "US", query, maximumBytesBilled,
  pageSize = 5000, queryKind = "projection.run", dryRun = false,
}) {
  const startedAt = new Date().toISOString();
  let resp;
  try {
    resp = await bqFetch(`/projects/${project}/queries`, {
      method: "POST",
      body: JSON.stringify({
        query, useLegacySql: false, location, dryRun,
        maximumBytesBilled: String(maximumBytesBilled),
        maxResults: pageSize,
      }),
    });
  } catch (e) {
    return {
      ok: false,
      error: e,
      startedAt,
      finishedAt: new Date().toISOString(),
      jobId: `dryrun-${randomUUID()}`,
      queryHash: sha256(query),
      bytesBilled: 0,
      schema: null,
      rows: [],
    };
  }
  const jobId = resp.jobReference?.jobId ?? `dryrun-${randomUUID()}`;
  const queryHash = sha256(query);
  const bytesBilled = Number(resp.totalBytesBilled ?? resp.totalBytesProcessed ?? 0);
  let schema = resp.schema ?? null;
  const allRows = [];
  if (resp.rows) allRows.push(...resp.rows);

  // Continue paging until done.
  let pageToken = resp.pageToken;
  while (pageToken && resp.jobComplete !== false) {
    const next = await bqFetch(
      `/projects/${project}/queries/${jobId}?pageToken=${encodeURIComponent(pageToken)}&maxResults=${pageSize}`,
      {},
    );
    if (next.schema) schema = next.schema;
    if (next.rows) allRows.push(...next.rows);
    pageToken = next.pageToken;
  }

  return {
    ok: true,
    startedAt,
    finishedAt: new Date().toISOString(),
    jobId,
    queryHash,
    bytesBilled,
    schema,
    rows: allRows,
  };
}

// rows[i].f[j].v → flat row { col: value } using schema field names + type coercion
export function flattenRows(schema, rows) {
  const fields = schema?.fields ?? [];
  return rows.map((r) => {
    const obj = {};
    fields.forEach((f, i) => {
      let v = r.f?.[i]?.v;
      if (v === undefined || v === null) { obj[f.name] = null; return; }
      switch ((f.type ?? "").toUpperCase()) {
        case "INTEGER": case "INT64":
          obj[f.name] = v === null ? null : Number(v); break;
        case "FLOAT": case "FLOAT64": case "NUMERIC": case "BIGNUMERIC":
          obj[f.name] = v === null ? null : Number(v); break;
        case "BOOLEAN": case "BOOL":
          obj[f.name] = String(v).toLowerCase() === "true"; break;
        case "TIMESTAMP":
          // BQ returns epoch seconds as string; coerce to ISO
          obj[f.name] = isFinite(Number(v))
            ? new Date(Number(v) * 1000).toISOString()
            : String(v);
          break;
        default:
          obj[f.name] = String(v);
      }
    });
    return obj;
  });
}

// ── RisingWave pool ────────────────────────────────────────────────────────

let _pgPool = null;
export async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({
    connectionString: KOTOBA_URL,
    max: 4,
    idleTimeoutMillis: 0,           // never reap idle (RW can be silent for >30s during BQ wait)
    connectionTimeoutMillis: 30_000,
    keepAlive: true,                // TCP keepalive
    keepAliveInitialDelayMillis: 10_000,
    statement_timeout: 0,
    query_timeout: 0,
  });
  // Silence "Connection terminated unexpectedly" so the pool keeps trying.
  _pgPool.on("error", (err) => {
    console.warn(`[adapter] pool error (will recreate on next acquire): ${err.message}`);
  });
  return _pgPool;
}

// Fresh single-shot client per call avoids pg-pool's "Connection terminated
// unexpectedly" race against RW silent idle-drops (observed at >30s gaps
// between queries while the adapter waits for BigQuery).
let _pgModule = null;
async function getPg() {
  if (_pgModule) return _pgModule;
  const m = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgModule = m.default ?? m;
  return _pgModule;
}

export async function rwQuery(sql, params) {
  const isTransient = (msg) =>
    /Connection terminated|connection closed|table reader closed|cluster recovery|gRPC.*Internal error|Scheduler error|barrier latency|ECONNRESET|ETIMEDOUT/i
      .test(msg);
  let attempt = 0;
  while (true) {
    const pg = await getPg();
    const client = new pg.Client({
      connectionString: KOTOBA_URL,
      keepAlive: true,
      keepAliveInitialDelayMillis: 5000,
      statement_timeout: 0,
      query_timeout: 0,
      connectionTimeoutMillis: 30_000,
    });
    client.on("error", () => { /* suppress async client errors; retry will surface them */ });
    try {
      await client.connect();
      const result = await client.query(sql, params);
      await client.end().catch(() => {});
      return result;
    } catch (e) {
      try { await client.end(); } catch { /* ignore */ }
      attempt++;
      const msg = String(e?.message ?? e);
      if (attempt >= 6 || !isTransient(msg)) throw e;
      const backoff = Math.min(8000, 500 * 2 ** (attempt - 1));
      console.warn(`[adapter] transient pg error (${attempt}/6, ${backoff}ms): ${msg.slice(0, 200)}`);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
}

export async function rwFlush() {
  try {
    await rwQuery("FLUSH");
  } catch (e) {
    console.warn(`[adapter] FLUSH failed: ${e.message}`);
  }
}

export async function rwEnd() {
  if (_pgPool) {
    await _pgPool.end().catch(() => {});
    _pgPool = null;
  }
}

// Batch INSERT — N rows × M columns. Splits into chunks of `chunkSize`.
async function _resetPool() {
  if (_pgPool) {
    try { await _pgPool.end(); } catch { /* ignore */ }
  }
  _pgPool = null;
  return getRwPool();
}

// Long-running INSERT loop: maintain a single client across many chunks
// (more efficient than fresh-per-chunk) but reconnect on every transient
// error. RW silently drops idle connections during BQ wait, so connection
// resilience is essential.
//
// `flushEveryNChunks` (default 20) forces a global checkpoint barrier so
// cluster recovery loses at most that many chunks worth of rows. Combined
// with record-log upsert this gives "at-least-once with bounded redo".
//
// `onChunkFlush({ slice, totalWritten })` fires AFTER each successful
// periodic FLUSH so adapters can advance their durable cursor mid-run.
// `slice` is the array of rows committed in the current flush window —
// adapters typically scan it to find max(date) / max(block_height) /
// max(person_id) and call saveCursor() with `status="partial"`.
export async function rwBatchInsert({ table, columns, rows, chunkSize = 100, sleepMsBetweenChunks = 50, flushEveryNChunks = 20, onChunkFlush = null }) {
  if (rows.length === 0) return 0;
  const pg = await getPg();
  let client = null;
  const fresh = async () => {
    if (client) { try { await client.end(); } catch { /* ignore */ } }
    client = new pg.Client({
      connectionString: KOTOBA_URL,
      keepAlive: true,
      keepAliveInitialDelayMillis: 5000,
      statement_timeout: 0,
      query_timeout: 0,
      connectionTimeoutMillis: 30_000,
    });
    client.on("error", () => { /* suppress async client errors */ });
    await client.connect();
  };
  await fresh();

  const isTransient = (msg) =>
    /Connection terminated|connection closed|table reader closed|cluster recovery|gRPC.*Internal error|Scheduler error|barrier latency|ECONNRESET|ETIMEDOUT/i
      .test(msg);

  let written = 0;
  let chunksSinceFlush = 0;
  let flushWindow = []; // rows committed in current flush window, drained on FLUSH
  for (let i = 0; i < rows.length; i += chunkSize) {
    const slice = rows.slice(i, i + chunkSize);
    const placeholders = [];
    const values = [];
    let p = 1;
    for (const row of slice) {
      const cells = columns.map(() => `$${p++}`);
      placeholders.push(`(${cells.join(",")})`);
      for (const c of columns) values.push(row[c] ?? null);
    }
    const sql = `INSERT INTO ${table} (${columns.join(",")}) VALUES ${placeholders.join(",")}`;
    let attempt = 0;
    while (true) {
      try {
        await client.query(sql, values);
        written += slice.length;
        chunksSinceFlush += 1;
        flushWindow.push(...slice);
        break;
      } catch (e) {
        attempt++;
        const msg = String(e?.message ?? e);
        if (attempt >= 6 || !isTransient(msg)) {
          try { await client.end(); } catch { /* ignore */ }
          throw e;
        }
        const backoff = Math.min(15000, 1000 * 2 ** (attempt - 1));
        console.warn(`[adapter] transient RW insert fail (${attempt}/6, ${backoff}ms): ${msg.slice(0, 200)}`);
        await fresh();
        await new Promise((r) => setTimeout(r, backoff));
      }
    }
    // Periodic FLUSH so cluster recovery loses at most flushEveryNChunks
    // chunks. Best-effort: a failed FLUSH does not abort the run; the next
    // FLUSH attempt or rwFlush() at the end recovers durability.
    if (flushEveryNChunks > 0 && chunksSinceFlush >= flushEveryNChunks) {
      let flushOk = false;
      try {
        await client.query("FLUSH");
        flushOk = true;
      } catch (e) {
        const msg = String(e?.message ?? e);
        console.warn(`[adapter] periodic FLUSH failed (${msg.slice(0, 200)}); reconnecting and continuing`);
        await fresh();
      }
      chunksSinceFlush = 0;
      const justCommitted = flushWindow;
      flushWindow = [];
      // Cursor advance hook: fires only when FLUSH succeeded so the cursor
      // never overshoots durable state. The callback's own errors are
      // swallowed so they cannot abort the INSERT loop.
      if (flushOk && onChunkFlush) {
        try {
          await onChunkFlush({ slice: justCommitted, totalWritten: written });
        } catch (e) {
          console.warn(`[adapter] onChunkFlush callback failed: ${String(e.message).slice(0, 200)}`);
        }
      }
    }
    if (sleepMsBetweenChunks > 0 && i + chunkSize < rows.length) {
      await new Promise((r) => setTimeout(r, sleepMsBetweenChunks));
    }
  }
  // Final tail: any rows committed after the last periodic FLUSH still
  // need a cursor advance once the wrapping rwFlush() succeeds at run-end.
  // Adapters can detect this via onChunkFlush firing with the tail window.
  if (onChunkFlush && flushWindow.length > 0) {
    try {
      await client.query("FLUSH");
      await onChunkFlush({ slice: flushWindow, totalWritten: written });
    } catch (e) {
      console.warn(`[adapter] tail FLUSH failed: ${String(e.message).slice(0, 200)}`);
    }
  }
  try { await client.end(); } catch { /* ignore */ }
  return written;
}

// ── ID + hash helpers ──────────────────────────────────────────────────────

export function sha256(s) {
  return createHash("sha256").update(String(s)).digest("hex");
}

export function vertexId(actorHost, collection, rkey) {
  return `at://did:web:${actorHost}.etzhayyim.com/${collection}/${rkey}`;
}

// ── cursor + window state (vertex_ingest_cursor) ───────────────────────────
//
// Each adapter persists per-shard cursors so a 2nd run picks up from where
// the prior one stopped, AND so partial-failure (RW recovery mid-INSERT)
// can be resumed without rescanning the whole window. Layout:
//
//   ingest_family = "bigquery.public_dataset.projection"
//   source_id     = dataset_id (e.g. "bigquery-public-data:crypto_litecoin")
//   shard_key     = adapter-specific sub-shard (e.g. "blocks", "transactions",
//                                                "co_daily_summary")
//   cursor_value  = the last successfully-committed point in the shard
//                   (e.g. "block_height=3104576" or "date_local=2025-06-30")
//   high_watermark = the upper bound the run *intended* to reach
//                   (e.g. window_to). Saved before INSERT so a crash leaves
//                   high_watermark > cursor_value, signalling "in-flight".
//   content_hash  = sha256 of (shard_key|cursor_value|high_watermark) for
//                   change detection across runs.
//   props (varchar) = JSON string carrying window_from / window_to / run_id /
//                     last_row_count / partial flag.
//
// Status values: "complete" / "partial" / "failed" / "in_flight".

const COLLECTION_CURSOR = "com.etzhayyim.apps.ingest.cursor";

function cursorVertexId(ingestFamily, sourceId, shardKey) {
  const rkey = sha256([ingestFamily, sourceId, shardKey].join("|"));
  return `at://${COLLECTOR_DID}/${COLLECTION_CURSOR}/${rkey}`;
}

export async function loadCursor({ ingestFamily, sourceId, shardKey }) {
  const vid = cursorVertexId(ingestFamily, sourceId, shardKey);
  const { rows } = await rwQuery(
    `SELECT cursor_value, cursor_hash, high_watermark, content_hash,
            updated_at, locked_by_run_id, lock_expires_at,
            status, fail_count, last_error, props
       FROM vertex_ingest_cursor WHERE vertex_id = $1 LIMIT 1`,
    [vid],
  );
  return rows[0] ?? null;
}

export async function saveCursor({
  ingestFamily, sourceId, shardKey,
  cursorValue, highWatermark, runId,
  status = "complete", failCount = null, lastError = null,
  windowFrom = null, windowTo = null, lastRowCount = null,
}) {
  const vid = cursorVertexId(ingestFamily, sourceId, shardKey);
  const observedAt = new Date().toISOString();
  const contentHash = sha256([shardKey, cursorValue, highWatermark].join("|"));
  const propsObj = {
    run_id: runId,
    window_from: windowFrom,
    window_to: windowTo,
    last_row_count: lastRowCount,
    partial: status !== "complete",
  };
  const props = JSON.stringify(propsObj).slice(0, 65535);

  await rwQuery(
    `INSERT INTO vertex_ingest_cursor (
       vertex_id, sensitivity_ord, owner_did,
       ingest_family, source_id, shard_key,
       cursor_value, cursor_hash, high_watermark, content_hash,
       updated_at, locked_by_run_id, lock_expires_at,
       status, fail_count, last_error, props
     ) VALUES (
       $1, 1, $2, $3, $4, $5,
       $6, $7, $8, $9,
       $10, $11, NULL,
       $12, $13, $14, $15
     )`,
    [
      vid, COLLECTOR_DID,
      ingestFamily, sourceId, shardKey,
      String(cursorValue ?? ""), sha256(String(cursorValue ?? "")),
      String(highWatermark ?? ""), contentHash,
      observedAt, runId,
      status, failCount, lastError, props,
    ],
  );
}

// Convenience: parse a cursor row's cursor_value into the typed shape an
// adapter expects. For range cursors we store "key=value" strings to keep
// the column varchar-only.
export function parseCursorKv(cursorValue) {
  if (!cursorValue) return null;
  const idx = String(cursorValue).indexOf("=");
  if (idx === -1) return { _: cursorValue };
  return { [cursorValue.slice(0, idx)]: cursorValue.slice(idx + 1) };
}

export function formatCursorKv(key, value) {
  return `${key}=${value}`;
}

// ── binding gate (ADR-2605101000 §D3) ──────────────────────────────────────

export async function loadBindingOrThrow({ datasetId, targetVertexLabel }) {
  const { rows } = await rwQuery(
    `SELECT src_vid, dst_vid, dataset_id, target_vertex_label, ingest_mode,
            approved_by, approved_at, scan_budget_tib, observed_at
       FROM edge_dataset_produces_vertex_type
       WHERE dataset_id = $1 AND target_vertex_label = $2`,
    [datasetId, targetVertexLabel],
  );
  if (rows.length === 0) {
    throw new Error(
      `binding_missing: no edge_dataset_produces_vertex_type for (`
      + `dataset_id=${datasetId}, target_vertex_label=${targetVertexLabel}). `
      + `Apply via 70-tools/scripts/bigquery-public-dataset-bindings-apply.mjs first.`,
    );
  }
  return rows[0];
}

// ── ingest job / artifact / run header ledger ──────────────────────────────

const COLLECTION_JOB = "com.etzhayyim.apps.bigquery.ingestJob";
const COLLECTION_RUN = "com.etzhayyim.apps.bigquery.profileRun";
const COLLECTION_ARTIFACT = "com.etzhayyim.apps.bigquery.exportArtifact";

export function bytesBilledToUsd(bytes) {
  const tib = bytes / 1024 ** 4;
  return Number((tib * 6.25).toFixed(6));
}

export async function recordIngestJob({
  jobId, runId, queryKind, queryHash, project, location,
  maximumBytesBilled, totalBytesBilled, cacheHit, status,
  errorReason, errorMessage, startedAt, finishedAt,
}) {
  const observedAt = finishedAt ?? new Date().toISOString();
  const vid = `at://${COLLECTOR_DID}/${COLLECTION_JOB}/${jobId}`;
  await rwQuery(
    `INSERT INTO vertex_bigquery_ingest_job (
       vertex_id, sensitivity_ord, owner_did,
       job_id, run_id, query_kind, query_hash, query_text_uri,
       bq_project, bq_location, statement_type, destination_table,
       maximum_bytes_billed, total_bytes_processed, total_bytes_billed, slot_ms,
       cache_hit, dry_run, status, error_reason, error_message,
       started_at, finished_at, estimated_cost_usd, observed_at,
       actor_did, org_did, created_at
     ) VALUES (
       $1, 1, $2, $3, $4, $5, $6, NULL,
       $7, $8, NULL, NULL,
       $9, $10, $10, NULL,
       $11, 'false', $12, $13, $14,
       $15, $16, $17, $18, $2, $2, $15
     )`,
    [
      vid, COLLECTOR_DID,
      jobId, runId, queryKind, queryHash,
      project, location,
      Number(maximumBytesBilled), Number(totalBytesBilled),
      cacheHit ? "true" : "false", status, errorReason, errorMessage,
      startedAt, finishedAt, bytesBilledToUsd(totalBytesBilled), observedAt,
    ],
  );
}

export async function recordRunHeader({
  runId, mode, project, providerFilter, datasetFilter,
  startedAt, finishedAt, status, datasetsSeen, tablesSeen, samplesTaken,
  totalBytesBilled, maxBytesBilledPerQuery, monthlyScanBudgetTib,
  monthlyScanUsedTib, approvalNote, errorMessage,
}) {
  const vid = `at://${COLLECTOR_DID}/${COLLECTION_RUN}/${runId}`;
  await rwQuery(
    `INSERT INTO vertex_bigquery_profile_run (
       vertex_id, sensitivity_ord, owner_did,
       run_id, mode, bq_project, provider_filter, dataset_filter,
       started_at, finished_at, status,
       datasets_seen, tables_seen, samples_taken,
       total_bytes_billed, total_cost_usd, max_bytes_billed_per_query,
       monthly_scan_budget_tib, monthly_scan_used_tib,
       approval_note, error_message, actor_did, org_did, created_at
     ) VALUES (
       $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
       $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $2, $2, $8
     )`,
    [
      vid, COLLECTOR_DID,
      runId, mode, project, providerFilter, datasetFilter,
      startedAt, finishedAt, status,
      datasetsSeen, tablesSeen, samplesTaken,
      Number(totalBytesBilled), bytesBilledToUsd(totalBytesBilled),
      Number(maxBytesBilledPerQuery),
      monthlyScanBudgetTib, monthlyScanUsedTib,
      approvalNote, errorMessage,
    ],
  );

  // Also record into generic vertex_ingest_run for parity with P0/P1 spine.
  const ingestVid = `at://${COLLECTOR_DID}/com.etzhayyim.apps.ingest.run/${runId}`;
  await rwQuery(
    `INSERT INTO vertex_ingest_run (
       vertex_id, sensitivity_ord, owner_did,
       run_id, ingest_family, source_id, mode, status,
       started_at, finished_at, requested_by,
       records_read, records_written, records_skipped, error_count, last_error,
       created_at, updated_at
     ) VALUES (
       $1, 1, $2, $3, 'bigquery.public_dataset.projection', $4, $5, $6,
       $7, $8, $9, $10, $11, 0, $12, $13, $7, $8
     )`,
    [
      ingestVid, COLLECTOR_DID,
      runId, datasetFilter, mode, status,
      startedAt, finishedAt, process.env.USER ?? "anon",
      datasetsSeen, samplesTaken,
      errorMessage ? 1 : 0, errorMessage,
    ],
  );
}

export async function recordExportArtifact({
  runId, jobId, artifactKind, datasetId, table, exportUri,
  format, byteSize, rowCount, sha, license,
}) {
  const id = sha256(`${runId}|${exportUri ?? jobId}|${rowCount}`);
  const observedAt = new Date().toISOString();
  const vid = `at://${COLLECTOR_DID}/${COLLECTION_ARTIFACT}/${id}`;
  await rwQuery(
    `INSERT INTO vertex_bigquery_export_artifact (
       vertex_id, sensitivity_ord, owner_did,
       run_id, job_id, artifact_kind, source_dataset_id, source_table,
       export_uri, format, byte_size, row_count, sha256, license,
       observed_at, actor_did, org_did, created_at
     ) VALUES (
       $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
       $14, $2, $2, $14
     )`,
    [
      vid, COLLECTOR_DID,
      runId, jobId, artifactKind, datasetId, table,
      exportUri, format, byteSize, rowCount, sha, license,
      observedAt,
    ],
  );

  const ingestVid = `at://${COLLECTOR_DID}/com.etzhayyim.apps.ingest.artifact/${id}`;
  await rwQuery(
    `INSERT INTO vertex_ingest_artifact (
       vertex_id, sensitivity_ord, owner_did,
       run_id, artifact_kind, source_id, uri, sha256, byte_size, record_count, created_at
     ) VALUES (
       $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10
     )`,
    [
      ingestVid, COLLECTOR_DID,
      runId, artifactKind, datasetId, exportUri,
      sha, byteSize, rowCount, observedAt,
    ],
  );
}

// ── CLI argv helpers ───────────────────────────────────────────────────────

export function parseArgs(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (t.startsWith("--")) {
      const k = t.slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
      a[k] = v;
    }
  }
  return a;
}
