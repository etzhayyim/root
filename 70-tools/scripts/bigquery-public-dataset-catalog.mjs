#!/usr/bin/env node
/**
 * BigQuery public dataset → RisingWave P0 catalog/sample runner.
 *
 * ADR 2605092700 §P0 Catalog/Sample. Discovers public BigQuery datasets,
 * captures schema / size / license metadata, takes bounded samples, and
 * lands rows in:
 *
 *   vertex_bigquery_profile_run        ← run header
 *   vertex_public_dataset_catalog      ← per (provider, dataset)
 *   vertex_public_dataset_table        ← per BQ table
 *   vertex_public_dataset_sample       ← per sample artifact
 *   vertex_bigquery_ingest_job         ← per BQ query job (cost ledger)
 *   vertex_bigquery_export_artifact    ← per artifact URI
 *   vertex_ingest_run / _artifact      ← generic ingest spine
 *
 * The script never full-scans a public table. Every sampling query is
 * guarded with `maximumBytesBilled` (default 100 GiB) and metadata
 * queries hit `INFORMATION_SCHEMA` only.
 *
 * Auth:
 *   - BQ_ACCESS_TOKEN env var, OR
 *   - `gcloud auth application-default print-access-token`
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-catalog.mjs \
 *     --project etzhayyim-bq-ingest \
 *     --providers bigquery-public-data \
 *     --datasets github_repos,gdelt-bq:gdeltv2 \
 *     --max-tables-per-dataset 50 \
 *     --sample-row-limit 200 \
 *     --max-bytes-billed 107374182400 \
 *     --artifact-dir /tmp/bq-p0-catalog \
 *     --dry-run
 *
 * Notes:
 *   - `--dry-run` skips RW writes and BQ sample queries; metadata queries
 *     still execute (bytes_billed=0 — INFORMATION_SCHEMA is free).
 *   - `--mode catalog` skips sample queries even on a real run (cheapest
 *     pass; ~$56 budget per ADR cost table at 10 TiB / month).
 *   - `--mode sample` (default) catalogs + samples up to N rows per table.
 *   - Resume / cursor: caller passes a stable `--run-id`. The script keeps
 *     the run header up to date on each batch via implicit upsert
 *     (record-log semantics — no ON CONFLICT).
 */

import { mkdir, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { execSync } from "node:child_process";
import { join } from "node:path";

// ── Config ──────────────────────────────────────────────────────────────────

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const COLLECTOR_DID = "did:web:bigquery.etzhayyim.com";
const COLLECTION_CATALOG = "com.etzhayyim.apps.bigquery.publicDatasetCatalog";
const COLLECTION_TABLE = "com.etzhayyim.apps.bigquery.publicDatasetTable";
const COLLECTION_SAMPLE = "com.etzhayyim.apps.bigquery.publicDatasetSample";
const COLLECTION_JOB = "com.etzhayyim.apps.bigquery.ingestJob";
const COLLECTION_EXPORT = "com.etzhayyim.apps.bigquery.exportArtifact";
const COLLECTION_RUN = "com.etzhayyim.apps.bigquery.profileRun";
const INGEST_FAMILY = "bigquery.public_dataset";

const BQ_API = "https://bigquery.googleapis.com/bigquery/v2";

// ── CLI args ────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const PROJECT = arg("project", process.env.GOOGLE_CLOUD_PROJECT);
const PROVIDERS = (arg("providers", "bigquery-public-data") ?? "")
  .split(",").map((s) => s.trim()).filter(Boolean);
const DATASET_FILTER = (arg("datasets", "") ?? "")
  .split(",").map((s) => s.trim()).filter(Boolean);
const MAX_TABLES_PER_DATASET = Number(arg("max-tables-per-dataset", "50"));
const SAMPLE_ROW_LIMIT = Number(arg("sample-row-limit", "200"));
const MAX_BYTES_BILLED = String(arg("max-bytes-billed", String(100 * 1024 ** 3))); // 100 GiB
const ARTIFACT_DIR = arg("artifact-dir", "/tmp/bq-p0-catalog");
const ARTIFACT_PREFIX = arg("artifact-prefix", "");
const MODE = arg("mode", "sample"); // catalog | sample
const RUN_ID = arg("run-id", `bq-p0-${new Date().toISOString().replace(/[:.]/g, "-")}`);
const APPROVAL_NOTE = arg("approval-note", "");
const MONTHLY_BUDGET_TIB = Number(arg("monthly-scan-budget-tib", "10"));
const DRY_RUN = flag("dry-run");

if (!PROJECT) {
  console.error("[bq-p0] ERROR: --project required (or GOOGLE_CLOUD_PROJECT env var).");
  process.exit(1);
}
if (PROVIDERS.length === 0) {
  console.error("[bq-p0] ERROR: --providers must list at least one billing project.");
  process.exit(1);
}
if (!["catalog", "sample"].includes(MODE)) {
  console.error(`[bq-p0] ERROR: --mode must be 'catalog' or 'sample' (got '${MODE}').`);
  process.exit(1);
}

// ── Auth ────────────────────────────────────────────────────────────────────

function getBqToken() {
  if (process.env.BQ_ACCESS_TOKEN) return process.env.BQ_ACCESS_TOKEN;
  try {
    return execSync("gcloud auth application-default print-access-token", {
      encoding: "utf8",
    }).trim();
  } catch (e) {
    throw new Error(
      "BigQuery auth not available. Set BQ_ACCESS_TOKEN or run "
      + "`gcloud auth application-default login`.",
    );
  }
}

let _token = null;
const token = () => (_token ??= getBqToken());

// ── BigQuery REST helpers ───────────────────────────────────────────────────

async function bqFetch(path, init = {}) {
  const url = path.startsWith("http") ? path : `${BQ_API}${path}`;
  const resp = await fetch(url, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${token()}`,
      "Content-Type": "application/json",
    },
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`BQ ${resp.status} ${path}: ${text.slice(0, 400)}`);
  }
  return resp.json();
}

async function bqQuery({ query, location = "US", dryRun = false, maximumBytesBilled = MAX_BYTES_BILLED, queryKind = "metadata" }) {
  const body = {
    query,
    useLegacySql: false,
    location,
    dryRun,
    maximumBytesBilled,
  };
  const started = new Date().toISOString();
  const queryHash = sha256(query);
  let resp;
  let error = null;
  try {
    resp = await bqFetch(`/projects/${PROJECT}/queries`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (e) {
    error = e;
  }
  const finished = new Date().toISOString();
  const job = resp?.jobReference?.jobId
    ?? `dryrun-${randomUUID()}`;
  const totalBytesProcessed = Number(resp?.totalBytesProcessed ?? 0);
  const totalBytesBilled = Number(resp?.totalBytesBilled ?? totalBytesProcessed);
  const cacheHit = resp?.cacheHit === true;
  const status = error ? "error" : "done";

  // Always record the job, even on error.
  await recordIngestJob({
    jobId: job,
    runId: RUN_ID,
    queryKind,
    queryHash,
    queryText: query,
    project: PROJECT,
    location,
    statementType: resp?.statistics?.query?.statementType ?? null,
    destinationTable: null,
    maximumBytesBilled: Number(maximumBytesBilled),
    totalBytesProcessed,
    totalBytesBilled,
    slotMs: Number(resp?.statistics?.totalSlotMs ?? 0),
    cacheHit,
    dryRun,
    status,
    errorReason: error ? "REQUEST_ERROR" : null,
    errorMessage: error ? String(error.message ?? error).slice(0, 1000) : null,
    startedAt: started,
    finishedAt: finished,
  });

  if (error) throw error;
  return { resp, jobId: job, queryHash, totalBytesBilled, cacheHit };
}

function paginatedRows(resp) {
  // BigQuery `queries.insert` synchronous response carries inline rows for
  // small results. We never request more than `sampleRowLimit` so a single
  // page always suffices.
  const fields = resp.schema?.fields ?? [];
  const rows = resp.rows ?? [];
  return rows.map((r) => {
    const obj = {};
    fields.forEach((f, i) => {
      obj[f.name] = r.f?.[i]?.v ?? null;
    });
    return obj;
  });
}

// ── Hash + ID helpers ───────────────────────────────────────────────────────

function sha256(s) {
  return createHash("sha256").update(String(s)).digest("hex");
}

function vertexId(collection, rkey) {
  return `at://${COLLECTOR_DID}/${collection}/${rkey}`;
}

// ── RisingWave write path ───────────────────────────────────────────────────

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2 });
  return _pgPool;
}

async function rwInsert(table, row) {
  if (DRY_RUN) return;
  const cols = Object.keys(row);
  const placeholders = cols.map((_, i) => `$${i + 1}`);
  const values = cols.map((c) => row[c]);
  const sql = `INSERT INTO ${table} (${cols.join(",")}) VALUES (${placeholders.join(",")})`;
  const isTransient = (msg) =>
    /table reader closed|cluster recovery|connection closed before message|connection terminated|gRPC.*Internal error|Scheduler error/i.test(msg);
  const pool = await getRwPool();
  let attempt = 0;
  while (true) {
    try {
      await pool.query(sql, values);
      return;
    } catch (e) {
      attempt++;
      const msg = String(e?.message ?? e);
      if (attempt >= 5 || !isTransient(msg)) throw e;
      const backoff = Math.min(15000, 1000 * 2 ** (attempt - 1));
      console.warn(`[bq-p0] transient RW write fail (${attempt}/5, ${backoff}ms): ${msg.slice(0, 200)}`);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
}

// ── Run / job / artifact ledger ─────────────────────────────────────────────

let runHeader = {
  datasetsSeen: 0,
  tablesSeen: 0,
  samplesTaken: 0,
  totalBytesBilled: 0,
  status: "running",
  startedAt: new Date().toISOString(),
  finishedAt: null,
  errorMessage: null,
};

async function upsertProfileRun() {
  const totalCost = bytesBilledToUsd(runHeader.totalBytesBilled);
  const monthlyUsedTib = runHeader.totalBytesBilled / 1024 ** 4;
  await rwInsert("vertex_bigquery_profile_run", {
    vertex_id: vertexId(COLLECTION_RUN, RUN_ID),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: RUN_ID,
    mode: MODE,
    bq_project: PROJECT,
    provider_filter: PROVIDERS.join(","),
    dataset_filter: DATASET_FILTER.join(","),
    started_at: runHeader.startedAt,
    finished_at: runHeader.finishedAt,
    status: runHeader.status,
    datasets_seen: runHeader.datasetsSeen,
    tables_seen: runHeader.tablesSeen,
    samples_taken: runHeader.samplesTaken,
    total_bytes_billed: runHeader.totalBytesBilled,
    total_cost_usd: totalCost,
    max_bytes_billed_per_query: Number(MAX_BYTES_BILLED),
    monthly_scan_budget_tib: MONTHLY_BUDGET_TIB,
    monthly_scan_used_tib: monthlyUsedTib,
    approval_note: APPROVAL_NOTE || null,
    error_message: runHeader.errorMessage,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: runHeader.startedAt,
  });
  await rwInsert("vertex_ingest_run", {
    vertex_id: vertexId("com.etzhayyim.apps.ingest.run", RUN_ID),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: RUN_ID,
    ingest_family: INGEST_FAMILY,
    source_id: PROVIDERS.join(","),
    mode: MODE,
    status: runHeader.status,
    started_at: runHeader.startedAt,
    finished_at: runHeader.finishedAt,
    requested_by: process.env.USER ?? "anon",
    records_read: runHeader.datasetsSeen + runHeader.tablesSeen,
    records_written: runHeader.tablesSeen + runHeader.samplesTaken,
    records_skipped: 0,
    error_count: runHeader.errorMessage ? 1 : 0,
    last_error: runHeader.errorMessage,
    created_at: runHeader.startedAt,
    updated_at: new Date().toISOString(),
  });
}

async function recordIngestJob(j) {
  runHeader.totalBytesBilled += j.totalBytesBilled;
  await rwInsert("vertex_bigquery_ingest_job", {
    vertex_id: vertexId(COLLECTION_JOB, j.jobId),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    job_id: j.jobId,
    run_id: j.runId,
    query_kind: j.queryKind,
    query_hash: j.queryHash,
    query_text_uri: null,
    bq_project: j.project,
    bq_location: j.location,
    statement_type: j.statementType,
    destination_table: j.destinationTable,
    maximum_bytes_billed: j.maximumBytesBilled,
    total_bytes_processed: j.totalBytesProcessed,
    total_bytes_billed: j.totalBytesBilled,
    slot_ms: j.slotMs,
    cache_hit: j.cacheHit ? "true" : "false",
    dry_run: j.dryRun ? "true" : "false",
    status: j.status,
    error_reason: j.errorReason,
    error_message: j.errorMessage,
    started_at: j.startedAt,
    finished_at: j.finishedAt,
    estimated_cost_usd: bytesBilledToUsd(j.totalBytesBilled),
    observed_at: j.finishedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: j.startedAt,
  });
}

async function recordExportArtifact({ runId, jobId, artifactKind, datasetId, table, exportUri, format, byteSize, rowCount, sha, license }) {
  const id = sha256(`${exportUri}|${sha ?? ""}|${runId}`);
  const observedAt = new Date().toISOString();
  await rwInsert("vertex_bigquery_export_artifact", {
    vertex_id: vertexId(COLLECTION_EXPORT, id),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: runId,
    job_id: jobId ?? null,
    artifact_kind: artifactKind,
    source_dataset_id: datasetId ?? null,
    source_table: table ?? null,
    export_uri: exportUri,
    format,
    byte_size: byteSize ?? null,
    row_count: rowCount ?? null,
    sha256: sha ?? null,
    license: license ?? null,
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });
  await rwInsert("vertex_ingest_artifact", {
    vertex_id: vertexId("com.etzhayyim.apps.ingest.artifact", id),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: runId,
    artifact_kind: artifactKind,
    source_id: datasetId ?? PROVIDERS.join(","),
    uri: exportUri,
    sha256: sha ?? null,
    byte_size: byteSize ?? null,
    record_count: rowCount ?? null,
    created_at: observedAt,
  });
}

function bytesBilledToUsd(bytes) {
  // ADR cost model: USD 6.25 / TiB scanned, first 1 TiB / month free.
  // The free tier is enforced at the project level, not per query, so the
  // run-level cost ledger does not subtract it; the profile-run row
  // exposes monthly_scan_used_tib so callers can subtract 1 TiB once at
  // billing rollup time.
  const tib = bytes / 1024 ** 4;
  return Number((tib * 6.25).toFixed(6));
}

// ── Catalog discovery ──────────────────────────────────────────────────────

async function listDatasets(provider) {
  // Use REST datasets.list — public datasets are listable with BQ User
  // role on the billing project. INFORMATION_SCHEMA.SCHEMATA on the
  // source project requires bigquery.metadataViewer there, which
  // bigquery-public-data does not grant. REST metadata calls are free
  // and do not produce a job, so they are not booked into
  // vertex_bigquery_ingest_job.
  const out = [];
  let pageToken;
  do {
    const params = new URLSearchParams({ maxResults: "1000" });
    if (pageToken) params.set("pageToken", pageToken);
    const resp = await bqFetch(`/projects/${provider}/datasets?${params}`);
    for (const d of resp.datasets ?? []) {
      out.push({
        bq_project: d.datasetReference?.projectId ?? provider,
        bq_dataset: d.datasetReference?.datasetId,
        location: d.location ?? "US",
        creation_time: null,
        last_modified_time: null,
      });
    }
    pageToken = resp.nextPageToken;
  } while (pageToken);
  return out;
}

async function listTables(provider, dataset, location) {
  // tables.list REST — same authorization story as datasets.list.
  const out = [];
  let pageToken;
  do {
    const params = new URLSearchParams({ maxResults: "1000" });
    if (pageToken) params.set("pageToken", pageToken);
    const resp = await bqFetch(
      `/projects/${provider}/datasets/${dataset}/tables?${params}`,
    );
    for (const t of resp.tables ?? []) {
      out.push({
        bq_project: t.tableReference?.projectId ?? provider,
        bq_dataset: t.tableReference?.datasetId ?? dataset,
        bq_table: t.tableReference?.tableId,
        table_type: t.type ?? "BASE TABLE",
        creation_time: t.creationTime ?? null,
        ddl: null,
      });
      if (out.length >= MAX_TABLES_PER_DATASET) return out;
    }
    pageToken = resp.nextPageToken;
  } while (pageToken);
  return out;
}

async function tableMeta(provider, dataset, table, location) {
  // tables.get is metadata-only and exposes numRows, numBytes, schema,
  // timePartitioning, clustering, description. Cheaper than a SELECT.
  return bqFetch(`/projects/${provider}/datasets/${dataset}/tables/${table}`);
}

async function sampleTable({ provider, dataset, table, location }) {
  if (MODE === "catalog" || DRY_RUN) {
    return { jobId: null, rows: [], bytesBilled: 0 };
  }
  const sql = `
    SELECT * FROM \`${provider}.${dataset}.${table}\`
    LIMIT ${SAMPLE_ROW_LIMIT}
  `;
  const { resp, jobId, totalBytesBilled } = await bqQuery({
    query: sql,
    location,
    queryKind: "catalog.sample",
  });
  const rows = paginatedRows(resp);
  return { jobId, rows, bytesBilled: totalBytesBilled };
}

// ── Catalog row builders ────────────────────────────────────────────────────

function recommendIngestMode(table, datasetMeta) {
  const sizeBytes = Number(table.numBytes ?? 0);
  const license = datasetMeta?.license ?? "";
  if (license === "" && sizeBytes > 1024 ** 4) return "catalog_only"; // unknown license + >1 TiB
  if (sizeBytes > 100 * 1024 ** 3) return "bigquery_stage";           // >100 GiB → BQ projection
  if (sizeBytes > 0) return "hybrid";
  return "catalog_only";
}

async function writeCatalogRow({ provider, dataset, location, datasetMeta, tableCount, sizeTotal, lastModified }) {
  const datasetId = `${provider}:${dataset}`;
  const observedAt = new Date().toISOString();
  await rwInsert("vertex_public_dataset_catalog", {
    vertex_id: vertexId(COLLECTION_CATALOG, sha256(datasetId)),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    dataset_id: datasetId,
    provider,
    bq_project: provider,
    bq_dataset: dataset,
    description: datasetMeta?.description ?? null,
    homepage_url: datasetMeta?.labels?.homepage_url ?? null,
    marketplace_url: datasetMeta?.labels?.marketplace_url ?? null,
    license: datasetMeta?.labels?.license ?? null,
    terms_url: datasetMeta?.labels?.terms_url ?? null,
    last_modified_at: lastModified ?? null,
    table_count: tableCount,
    total_size_bytes_estimate: sizeTotal,
    pii_tier_guess: 1,
    allowed_for_train_guess: "false",
    allowed_for_embedding_guess: "false",
    recommended_ingest_mode: "catalog_only",
    candidate_vertex_targets_json: null,
    candidate_edge_targets_json: null,
    review_status: "pending",
    review_note: null,
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });
}

async function writeTableRow({ datasetVertexId, datasetId, provider, dataset, table, meta }) {
  const sizeBytes = Number(meta?.numBytes ?? 0);
  const rowCount = Number(meta?.numRows ?? 0);
  const fullScanCost = bytesBilledToUsd(sizeBytes);
  const observedAt = new Date().toISOString();
  await rwInsert("vertex_public_dataset_table", {
    vertex_id: vertexId(COLLECTION_TABLE, sha256(`${provider}.${dataset}.${table}`)),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    dataset_vertex_id: datasetVertexId,
    dataset_id: datasetId,
    bq_project: provider,
    bq_dataset: dataset,
    bq_table: table,
    description: meta?.description ?? null,
    table_kind: meta?.type ?? null,
    schema_json: meta?.schema ? JSON.stringify(meta.schema).slice(0, 65535) : null,
    partitioning_json: meta?.timePartitioning ? JSON.stringify(meta.timePartitioning) : null,
    clustering_json: meta?.clustering ? JSON.stringify(meta.clustering) : null,
    row_count_estimate: rowCount,
    size_bytes_estimate: sizeBytes,
    last_modified_at: meta?.lastModifiedTime
      ? new Date(Number(meta.lastModifiedTime)).toISOString()
      : null,
    estimated_full_scan_cost_usd: fullScanCost,
    estimated_delta_scan_cost_usd: null,
    review_status: "pending",
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });
}

async function writeSampleRow({ tableVertexId, datasetId, runId, jobId, queryHash, exportUri, rowCount, byteSize, sampleHash, format, bytesBilled }) {
  const observedAt = new Date().toISOString();
  await rwInsert("vertex_public_dataset_sample", {
    vertex_id: vertexId(COLLECTION_SAMPLE, sha256(exportUri)),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    table_vertex_id: tableVertexId,
    dataset_id: datasetId,
    run_id: runId,
    job_id: jobId,
    query_hash: queryHash,
    query_text_uri: null,
    sample_rows_uri: exportUri,
    sample_format: format,
    sample_row_count: rowCount,
    sample_byte_size: byteSize,
    sample_hash: sampleHash,
    bytes_billed: bytesBilled,
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });
}

// ── Artifact materialization ────────────────────────────────────────────────

async function writeSampleArtifact({ provider, dataset, table, rows }) {
  const fname = `${provider}__${dataset}__${table}.jsonl`;
  const localPath = join(ARTIFACT_DIR, RUN_ID, fname);
  await mkdir(join(ARTIFACT_DIR, RUN_ID), { recursive: true });
  const body = rows.map((r) => JSON.stringify(r)).join("\n") + "\n";
  if (!DRY_RUN) {
    await writeFile(localPath, body, "utf8");
  }
  const sha = sha256(body);
  const byteSize = Buffer.byteLength(body, "utf8");
  const exportUri = ARTIFACT_PREFIX
    ? `${ARTIFACT_PREFIX.replace(/\/$/, "")}/${RUN_ID}/${fname}`
    : `file://${localPath}`;
  return { exportUri, sha, byteSize, format: "jsonl" };
}

// ── Main loop ───────────────────────────────────────────────────────────────

async function main() {
  console.log(`[bq-p0] run_id=${RUN_ID} project=${PROJECT} mode=${MODE} dry_run=${DRY_RUN}`);
  console.log(`[bq-p0] providers=${PROVIDERS.join(",")} dataset_filter=${DATASET_FILTER.join(",") || "(all)"}`);
  console.log(`[bq-p0] max_bytes_billed=${MAX_BYTES_BILLED} sample_row_limit=${SAMPLE_ROW_LIMIT} max_tables=${MAX_TABLES_PER_DATASET}`);

  await upsertProfileRun();

  for (const provider of PROVIDERS) {
    console.log(`[bq-p0] provider=${provider} — listing datasets`);
    let datasets;
    try {
      datasets = await listDatasets(provider);
    } catch (e) {
      console.error(`[bq-p0] listDatasets(${provider}) failed: ${e.message}`);
      runHeader.errorMessage = String(e.message).slice(0, 1000);
      continue;
    }
    if (DATASET_FILTER.length > 0) {
      const allow = new Set(DATASET_FILTER.map((d) => d.replace(/^.*:/, "")));
      datasets = datasets.filter((d) => allow.has(String(d.bq_dataset)));
    }
    console.log(`[bq-p0]   found ${datasets.length} dataset(s)`);

    for (const ds of datasets) {
      const dataset = String(ds.bq_dataset);
      const location = String(ds.location ?? "US");
      const datasetId = `${provider}:${dataset}`;
      runHeader.datasetsSeen += 1;
      let datasetMeta = null;
      try {
        datasetMeta = await bqFetch(`/projects/${provider}/datasets/${dataset}`);
      } catch (e) {
        console.warn(`[bq-p0]   dataset.get(${datasetId}) failed: ${e.message}`);
      }

      let tables = [];
      try {
        tables = await listTables(provider, dataset, location);
      } catch (e) {
        console.warn(`[bq-p0]   listTables(${datasetId}) failed: ${e.message}`);
        continue;
      }
      console.log(`[bq-p0]   dataset=${dataset} location=${location} tables=${tables.length}`);

      let sizeTotal = 0;
      let lastModified = null;
      const datasetVid = vertexId(COLLECTION_CATALOG, sha256(datasetId));

      for (const t of tables) {
        const table = String(t.bq_table);
        let meta = null;
        try {
          meta = await tableMeta(provider, dataset, table, location);
        } catch (e) {
          console.warn(`[bq-p0]     tableMeta(${datasetId}.${table}) failed: ${e.message}`);
          continue;
        }
        runHeader.tablesSeen += 1;
        sizeTotal += Number(meta?.numBytes ?? 0);
        if (meta?.lastModifiedTime) {
          const ts = new Date(Number(meta.lastModifiedTime)).toISOString();
          if (!lastModified || ts > lastModified) lastModified = ts;
        }
        await writeTableRow({
          datasetVertexId: datasetVid,
          datasetId,
          provider,
          dataset,
          table,
          meta,
        });

        // Sampling pass — bounded LIMIT, max bytes billed enforced upstream.
        try {
          const { jobId, rows, bytesBilled } = await sampleTable({ provider, dataset, table, location });
          if (rows.length > 0) {
            const artifact = await writeSampleArtifact({ provider, dataset, table, rows });
            const tableVid = vertexId(COLLECTION_TABLE, sha256(`${provider}.${dataset}.${table}`));
            await writeSampleRow({
              tableVertexId: tableVid,
              datasetId,
              runId: RUN_ID,
              jobId,
              queryHash: sha256(`SELECT * LIMIT ${SAMPLE_ROW_LIMIT} FROM ${provider}.${dataset}.${table}`),
              exportUri: artifact.exportUri,
              rowCount: rows.length,
              byteSize: artifact.byteSize,
              sampleHash: artifact.sha,
              format: artifact.format,
              bytesBilled,
            });
            await recordExportArtifact({
              runId: RUN_ID,
              jobId,
              artifactKind: "bigquery.catalog_sample",
              datasetId,
              table,
              exportUri: artifact.exportUri,
              format: artifact.format,
              byteSize: artifact.byteSize,
              rowCount: rows.length,
              sha: artifact.sha,
              license: datasetMeta?.labels?.license ?? null,
            });
            runHeader.samplesTaken += 1;
          }
        } catch (e) {
          console.warn(`[bq-p0]     sample(${datasetId}.${table}) failed: ${e.message}`);
        }

        // Refresh run header every table so a long pass leaves a live trail.
        await upsertProfileRun();
      }

      await writeCatalogRow({
        provider,
        dataset,
        location,
        datasetMeta,
        tableCount: tables.length,
        sizeTotal,
        lastModified,
      });
    }
  }

  runHeader.status = runHeader.errorMessage ? "completed_with_errors" : "completed";
  runHeader.finishedAt = new Date().toISOString();
  await upsertProfileRun();

  // RisingWave buffers DML between checkpoints; explicit FLUSH at the end
  // of a run guarantees catalog/table/sample/job rows are visible to the
  // next reader (review tooling, P1 profiler, coverage MV).
  if (!DRY_RUN) {
    try {
      const pool = await getRwPool();
      await pool.query("FLUSH");
    } catch (e) {
      console.warn(`[bq-p0] FLUSH failed (rows will become visible at next checkpoint): ${e.message}`);
    }
  }

  console.log(`[bq-p0] === COMPLETE ===`);
  console.log(`[bq-p0] datasets_seen=${runHeader.datasetsSeen}`);
  console.log(`[bq-p0] tables_seen=${runHeader.tablesSeen}`);
  console.log(`[bq-p0] samples_taken=${runHeader.samplesTaken}`);
  console.log(`[bq-p0] total_bytes_billed=${runHeader.totalBytesBilled}`);
  console.log(`[bq-p0] est_cost_usd=${bytesBilledToUsd(runHeader.totalBytesBilled).toFixed(4)}`);
  console.log(`[bq-p0] artifact_dir=${ARTIFACT_DIR}/${RUN_ID}`);

  if (_pgPool) await _pgPool.end();
}

main().catch(async (e) => {
  console.error(`[bq-p0] FATAL: ${e.stack ?? e.message ?? e}`);
  runHeader.status = "failed";
  runHeader.errorMessage = String(e.message ?? e).slice(0, 1000);
  runHeader.finishedAt = new Date().toISOString();
  try { await upsertProfileRun(); } catch { /* ignore */ }
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});
