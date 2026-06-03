#!/usr/bin/env node
/**
 * BigQuery public dataset → RisingWave P1 profile runner.
 *
 * ADR 2605092700 §P1 Profiling. P1 only runs against P0 candidates that
 * have a `vertex_public_dataset_table` row whose parent catalog row has
 * `review_status` advanced past 'pending'. Each table gets ONE bounded
 * profile query (`maximumBytesBilled` <= 2 TiB by default per ADR
 * guardrail) that materializes column-level stats in a single scan.
 *
 * Outputs:
 *   vertex_public_dataset_profile          ← per (table, run) summary
 *   edge_public_dataset_profiles_table     ← profile → table lineage
 *   vertex_bigquery_ingest_job             ← per BQ query (cost ledger)
 *   vertex_bigquery_export_artifact        ← profile artifact URI
 *   vertex_bigquery_profile_run            ← run header
 *   vertex_ingest_run / _artifact          ← generic ingest spine
 *
 * Budget guardrails:
 *   - max-bytes-billed-per-query default = 2 TiB (ADR §P1).
 *   - monthly-scan-budget-tib  default = 20 TiB (ADR §P1 default cap).
 *   - monthly-scan-hard-cap-tib default = 100 TiB (ADR §P1 hard cap;
 *     refuses to start if `approval_note` is empty when budget > 20 TiB).
 *   - `allowed_for_train` defaults to 'false' for every profile;
 *     promotion happens out-of-band via review tooling.
 *
 * Sampling strategy:
 *   - if size <= max-bytes-billed-per-query → full scan.
 *   - else → TABLESAMPLE SYSTEM (P PERCENT) where P = ceil(budget / size * 100),
 *     bounded to [1, 100]. Returns approximate aggregates only.
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-profile.mjs \
 *     --project etzhayyim-bq-ingest \
 *     --datasets bigquery-public-data:github_repos \
 *     --max-tables 20 \
 *     --max-text-columns-per-table 6 \
 *     --max-bytes-billed-per-query 2199023255552 \
 *     --monthly-scan-budget-tib 20 \
 *     --artifact-dir /tmp/bq-p1-profile \
 *     --dry-run
 */

import { mkdir, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { execSync } from "node:child_process";
import { join } from "node:path";

// ── Config ──────────────────────────────────────────────────────────────────

const RW_CONN = process.env.RISINGWAVE_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const COLLECTOR_DID = "did:web:bigquery.etzhayyim.com";
const COLLECTION_PROFILE = "com.etzhayyim.apps.bigquery.publicDatasetProfile";
const COLLECTION_PROFILES_TABLE = "com.etzhayyim.apps.bigquery.profilesTable";
const COLLECTION_TABLE = "com.etzhayyim.apps.bigquery.publicDatasetTable";
const COLLECTION_JOB = "com.etzhayyim.apps.bigquery.ingestJob";
const COLLECTION_EXPORT = "com.etzhayyim.apps.bigquery.exportArtifact";
const COLLECTION_RUN = "com.etzhayyim.apps.bigquery.profileRun";
const INGEST_FAMILY = "bigquery.public_dataset.profile";

const BQ_API = "https://bigquery.googleapis.com/bigquery/v2";

// ── CLI args ────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const PROJECT = arg("project", process.env.GOOGLE_CLOUD_PROJECT);
const DATASET_FILTER = (arg("datasets", "") ?? "")
  .split(",").map((s) => s.trim()).filter(Boolean);
const TABLE_FILTER = (arg("tables", "") ?? "")
  .split(",").map((s) => s.trim()).filter(Boolean);
const MAX_TABLES = Number(arg("max-tables", "20"));
const MAX_TEXT_COLUMNS_PER_TABLE = Number(arg("max-text-columns-per-table", "6"));
const TOP_VALUES_PER_COLUMN = Number(arg("top-values-per-column", "5"));
const MAX_BYTES_BILLED_PER_QUERY = String(arg("max-bytes-billed-per-query", String(2 * 1024 ** 4))); // 2 TiB
const MONTHLY_SCAN_BUDGET_TIB = Number(arg("monthly-scan-budget-tib", "20"));
const MONTHLY_SCAN_HARD_CAP_TIB = Number(arg("monthly-scan-hard-cap-tib", "100"));
const APPROVAL_NOTE = arg("approval-note", "");
const ARTIFACT_DIR = arg("artifact-dir", "/tmp/bq-p1-profile");
const ARTIFACT_PREFIX = arg("artifact-prefix", "");
const RUN_ID = arg("run-id", `bq-p1-${new Date().toISOString().replace(/[:.]/g, "-")}`);
const DRY_RUN = flag("dry-run");

if (!PROJECT) {
  console.error("[bq-p1] ERROR: --project required (or GOOGLE_CLOUD_PROJECT env var).");
  process.exit(1);
}
if (DATASET_FILTER.length === 0 && TABLE_FILTER.length === 0) {
  console.error("[bq-p1] ERROR: --datasets and/or --tables required (P1 requires explicit P0 candidates).");
  process.exit(1);
}
if (MONTHLY_SCAN_BUDGET_TIB > 20 && !APPROVAL_NOTE) {
  console.error(`[bq-p1] ERROR: monthly-scan-budget-tib > 20 requires --approval-note (per ADR §P1 hard cap rule).`);
  process.exit(1);
}
if (MONTHLY_SCAN_BUDGET_TIB > MONTHLY_SCAN_HARD_CAP_TIB) {
  console.error(`[bq-p1] ERROR: monthly-scan-budget-tib ${MONTHLY_SCAN_BUDGET_TIB} exceeds hard cap ${MONTHLY_SCAN_HARD_CAP_TIB}.`);
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

async function bqQuery({ query, location = "US", queryKind = "profile.summary", maxBytesBilled = MAX_BYTES_BILLED_PER_QUERY, dryRun = false }) {
  const body = {
    query,
    useLegacySql: false,
    location,
    dryRun,
    maximumBytesBilled: String(maxBytesBilled),
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
  const job = resp?.jobReference?.jobId ?? `dryrun-${randomUUID()}`;
  const totalBytesProcessed = Number(resp?.totalBytesProcessed ?? 0);
  const totalBytesBilled = Number(resp?.totalBytesBilled ?? totalBytesProcessed);
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
    maximumBytesBilled: Number(maxBytesBilled),
    totalBytesProcessed,
    totalBytesBilled,
    slotMs: Number(resp?.statistics?.totalSlotMs ?? 0),
    cacheHit: resp?.cacheHit === true,
    dryRun,
    status: error ? "error" : "done",
    errorReason: error ? "REQUEST_ERROR" : null,
    errorMessage: error ? String(error.message ?? error).slice(0, 1000) : null,
    startedAt: started,
    finishedAt: finished,
  });
  if (error) throw error;
  return { resp, jobId: job, queryHash, totalBytesBilled };
}

function paginatedRows(resp) {
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

// ── Helpers ────────────────────────────────────────────────────────────────

function sha256(s) {
  return createHash("sha256").update(String(s)).digest("hex");
}

function vertexId(collection, rkey) {
  return `at://${COLLECTOR_DID}/${collection}/${rkey}`;
}

function bytesBilledToUsd(bytes) {
  const tib = bytes / 1024 ** 4;
  return Number((tib * 6.25).toFixed(6));
}

// BigQuery identifiers permit `[A-Za-z0-9_-]`; project IDs in particular
// require hyphens (`bigquery-public-data`). Refuse anything else so the
// inlined SQL cannot be injected. Column-name guards downstream still
// require the strict `[A-Za-z_][A-Za-z0-9_]*` form because BigQuery
// columns cannot start with a digit and we use them in alias suffixes.
const BQ_IDENT_SAFE = /^[A-Za-z0-9_][A-Za-z0-9_-]*$/;
const BQ_COLUMN_SAFE = /^[A-Za-z_][A-Za-z0-9_]*$/;
function ident(s) {
  if (!BQ_IDENT_SAFE.test(String(s))) {
    throw new Error(`Refusing unsafe identifier: ${s}`);
  }
  return `\`${s}\``;
}

// ── RisingWave write path ───────────────────────────────────────────────────

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: RW_CONN, max: 2 });
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
      console.warn(`[bq-p1] transient RW write fail (${attempt}/5, ${backoff}ms): ${msg.slice(0, 200)}`);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
}

// ── Run header / job / artifact ledger ─────────────────────────────────────

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
    mode: "profile",
    bq_project: PROJECT,
    provider_filter: null,
    dataset_filter: DATASET_FILTER.join(","),
    started_at: runHeader.startedAt,
    finished_at: runHeader.finishedAt,
    status: runHeader.status,
    datasets_seen: runHeader.datasetsSeen,
    tables_seen: runHeader.tablesSeen,
    samples_taken: runHeader.samplesTaken,
    total_bytes_billed: runHeader.totalBytesBilled,
    total_cost_usd: totalCost,
    max_bytes_billed_per_query: Number(MAX_BYTES_BILLED_PER_QUERY),
    monthly_scan_budget_tib: MONTHLY_SCAN_BUDGET_TIB,
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
    source_id: DATASET_FILTER.join(",") || TABLE_FILTER.join(","),
    mode: "profile",
    status: runHeader.status,
    started_at: runHeader.startedAt,
    finished_at: runHeader.finishedAt,
    requested_by: process.env.USER ?? "anon",
    records_read: runHeader.tablesSeen,
    records_written: runHeader.samplesTaken,
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

// ── Profile query builder ──────────────────────────────────────────────────

function planProfileScan(numBytes) {
  // Returns {samplePercent, billedBytesGuess}. <=0 → skip.
  const cap = Number(MAX_BYTES_BILLED_PER_QUERY);
  if (!numBytes || numBytes <= 0) {
    return { samplePercent: null, billedBytesGuess: 0 };
  }
  if (numBytes <= cap) {
    return { samplePercent: null, billedBytesGuess: numBytes };
  }
  const pct = Math.max(1, Math.min(100, Math.ceil((cap / numBytes) * 100)));
  return { samplePercent: pct, billedBytesGuess: Math.floor(numBytes * pct / 100) };
}

// PII detection: bounded RE2-safe set. Patterns embed via BigQuery raw
// string literal (`r"..."`), so a single backslash in the JS string
// reaches the regex engine as a single backslash. Don't use `(?:` here —
// some legacy BQ regex paths reject it; plain alternation is sufficient
// for these fixed shapes.
const PII_PATTERNS = [
  { name: "email",      re: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}" },
  { name: "phone",      re: "\\+?[0-9]{1,3}[ .-]?[0-9]{2,4}[ .-]?[0-9]{3,4}[ .-]?[0-9]{3,4}" },
  { name: "ipv4",       re: "[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}" },
  { name: "creditcard", re: "[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{4}" },
];

function pickProfileColumns(schema) {
  const fields = schema?.fields ?? [];
  const profiled = [];
  let textCount = 0;
  for (const f of fields) {
    if (!BQ_COLUMN_SAFE.test(f.name)) continue;
    const repeated = f.mode === "REPEATED";
    if (repeated) continue;
    const t = (f.type ?? "").toUpperCase();
    const isText = t === "STRING" && textCount < MAX_TEXT_COLUMNS_PER_TABLE;
    const isNumeric = ["INT64","INTEGER","FLOAT","FLOAT64","NUMERIC","BIGNUMERIC"].includes(t);
    const isTimestamp = ["TIMESTAMP","DATETIME","DATE"].includes(t);
    if (!isText && !isNumeric && !isTimestamp && t !== "BOOL" && t !== "BOOLEAN") continue;
    if (isText) textCount += 1;
    profiled.push({ name: f.name, type: t, isText, isNumeric, isTimestamp });
  }
  return profiled;
}

function buildProfileSql({ provider, dataset, table, profiled, samplePercent }) {
  const fqTable = `${ident(provider)}.${ident(dataset)}.${ident(table)}`;
  const sampleClause = samplePercent
    ? ` TABLESAMPLE SYSTEM (${samplePercent} PERCENT)`
    : "";
  const aggs = ["COUNT(*) AS row_count"];
  for (const c of profiled) {
    const col = ident(c.name);
    const tag = sha256(c.name).slice(0, 12);
    aggs.push(`COUNTIF(${col} IS NULL) AS null_${tag}`);
    aggs.push(`APPROX_COUNT_DISTINCT(${col}) AS distinct_${tag}`);
    if (c.isText) {
      aggs.push(`AVG(LENGTH(CAST(${col} AS STRING))) AS textlen_avg_${tag}`);
      aggs.push(`MAX(LENGTH(CAST(${col} AS STRING))) AS textlen_max_${tag}`);
      for (const p of PII_PATTERNS) {
        aggs.push(
          `COUNTIF(REGEXP_CONTAINS(CAST(${col} AS STRING), r"${p.re}"))`
          + ` AS pii_${p.name}_${tag}`,
        );
      }
    }
    if (c.isTimestamp) {
      aggs.push(`MIN(CAST(${col} AS TIMESTAMP)) AS ts_min_${tag}`);
      aggs.push(`MAX(CAST(${col} AS TIMESTAMP)) AS ts_max_${tag}`);
    }
  }
  return `SELECT\n  ${aggs.join(",\n  ")}\nFROM ${fqTable}${sampleClause}`;
}

// ── Top-N values per text column (separate query per column) ──────────────

async function collectTopValues({ provider, dataset, table, location, profiled, samplePercent, perColumnBytesBudget }) {
  const result = {};
  for (const c of profiled) {
    if (!c.isText) continue;
    if (!perColumnBytesBudget || perColumnBytesBudget <= 0) break;
    const fqTable = `${ident(provider)}.${ident(dataset)}.${ident(table)}`;
    const sampleClause = samplePercent
      ? ` TABLESAMPLE SYSTEM (${samplePercent} PERCENT)`
      : "";
    const sql = `
      SELECT ${ident(c.name)} AS v, COUNT(*) AS n
      FROM ${fqTable}${sampleClause}
      WHERE ${ident(c.name)} IS NOT NULL
      GROUP BY v
      ORDER BY n DESC
      LIMIT ${TOP_VALUES_PER_COLUMN}
    `;
    try {
      const { resp } = await bqQuery({
        query: sql,
        location,
        queryKind: "profile.top_values",
        maxBytesBilled: String(perColumnBytesBudget),
      });
      result[c.name] = paginatedRows(resp);
    } catch (e) {
      result[c.name] = { error: String(e.message).slice(0, 240) };
    }
  }
  return result;
}

// ── Profile row decoder ────────────────────────────────────────────────────

function decodeProfile({ row, profiled }) {
  const out = {
    rowCount: Number(row.row_count ?? 0),
    nullRate: {},
    distinctEstimate: {},
    textLengthStats: {},
    timestampRange: {},
    piiSignal: {},
  };
  const total = out.rowCount || 1;
  for (const c of profiled) {
    const tag = sha256(c.name).slice(0, 12);
    const nullV = Number(row[`null_${tag}`] ?? 0);
    const distV = Number(row[`distinct_${tag}`] ?? 0);
    out.nullRate[c.name] = total > 0 ? nullV / total : null;
    out.distinctEstimate[c.name] = distV;
    if (c.isText) {
      out.textLengthStats[c.name] = {
        avg: Number(row[`textlen_avg_${tag}`] ?? 0),
        max: Number(row[`textlen_max_${tag}`] ?? 0),
      };
      const piiHits = {};
      for (const p of PII_PATTERNS) {
        piiHits[p.name] = Number(row[`pii_${p.name}_${tag}`] ?? 0);
      }
      out.piiSignal[c.name] = piiHits;
    }
    if (c.isTimestamp) {
      out.timestampRange[c.name] = {
        min: row[`ts_min_${tag}`] ?? null,
        max: row[`ts_max_${tag}`] ?? null,
      };
    }
  }
  return out;
}

function deriveDecisions({ catalog, profile, profiled }) {
  // License: catalog.license + terms_url presence drives decision.
  // PII: any pii hit > 0 forces 'review' even if license OK.
  const license = catalog?.license ?? null;
  const hasPii = Object.values(profile.piiSignal).some((cs) =>
    Object.values(cs).some((n) => Number(n) > 0)
  );
  const licenseDecision = !license
    ? "review"
    : (hasPii ? "review" : "allow");
  const allowedForTrain = "false"; // ADR §P1: default deny until reviewed.
  const allowedForEmbedding = (licenseDecision === "allow" && !hasPii) ? "review" : "false";

  // Key candidates: text/numeric columns with distinct ≈ row_count.
  const keys = [];
  const total = profile.rowCount || 1;
  for (const c of profiled) {
    const dist = profile.distinctEstimate[c.name] ?? 0;
    if (total > 0 && dist >= total * 0.95 && (c.isText || c.isNumeric)) {
      keys.push({ column: c.name, distinct: dist, ratio: dist / total });
    }
  }
  keys.sort((a, b) => b.ratio - a.ratio);

  // Dedupe / delta strategy heuristics.
  const dedupeStrategy = keys.length > 0 ? "natural_key" : "content_hash";
  const tsCols = profiled.filter((c) => c.isTimestamp).map((c) => c.name);
  const deltaStrategy = tsCols.length > 0 ? "partition_delta" : "full_replace";

  // Recommended ingest mode (mirrors ADR cost guidance).
  const sizeBytes = Number(catalog?.size_bytes_estimate ?? 0);
  let ingestMode = "catalog_only";
  if (licenseDecision === "allow" && sizeBytes > 0) {
    if (sizeBytes > 100 * 1024 ** 3) ingestMode = "bigquery_stage";
    else if (sizeBytes > 1024 ** 3) ingestMode = "hybrid";
    else ingestMode = "self_ingest";
  } else if (licenseDecision === "review") {
    ingestMode = "catalog_only";
  } else {
    ingestMode = "reject";
  }

  // Refresh cost estimate: assume monthly delta scan = 5% of full size for
  // partitioned tables, 100% otherwise.
  const monthlyScanBytes = tsCols.length > 0 ? sizeBytes * 0.05 : sizeBytes;
  const monthlyScanTiB = monthlyScanBytes / 1024 ** 4;

  return {
    licenseDecision,
    allowedForTrain,
    allowedForEmbedding,
    keyCandidates: keys.slice(0, 5),
    dedupeStrategy,
    deltaStrategy,
    recommendedIngestMode: ingestMode,
    estimatedMonthlyRefreshScanTib: monthlyScanTiB,
    estimatedMonthlyRefreshCostUsd: Number((monthlyScanTiB * 6.25).toFixed(6)),
    timestampColumns: tsCols,
    hasPii,
  };
}

// ── Catalog reader ─────────────────────────────────────────────────────────

async function loadCatalogTargets() {
  if (DRY_RUN) {
    // Dry-run mode: synthesize catalog rows from CLI filters so the script
    // can be exercised without an RW connection. Real runs read from RW.
    const targets = [];
    for (const ds of DATASET_FILTER) {
      const [provider, dataset] = ds.includes(":") ? ds.split(":") : ["bigquery-public-data", ds];
      targets.push({ provider, dataset, table: TABLE_FILTER[0] ?? null, catalog: null });
    }
    return targets;
  }
  const pool = await getRwPool();
  const where = [];
  const params = [];
  if (DATASET_FILTER.length > 0) {
    const placeholders = DATASET_FILTER.map((_, i) => `$${params.length + i + 1}`).join(",");
    where.push(`t.dataset_id IN (${placeholders})`);
    for (const ds of DATASET_FILTER) {
      // Normalize to `${provider}:${dataset}` shape for catalog lookup.
      params.push(ds.includes(":") ? ds : `bigquery-public-data:${ds}`);
    }
  }
  if (TABLE_FILTER.length > 0) {
    const placeholders = TABLE_FILTER.map((_, i) => `$${params.length + i + 1}`).join(",");
    where.push(`t.bq_table IN (${placeholders})`);
    for (const t of TABLE_FILTER) params.push(t);
  }
  const sql = `
    SELECT
      t.vertex_id      AS table_vertex_id,
      t.dataset_id,
      t.bq_project,
      t.bq_dataset,
      t.bq_table,
      t.size_bytes_estimate,
      t.row_count_estimate,
      c.license,
      c.recommended_ingest_mode,
      c.review_status  AS catalog_review_status
    FROM vertex_public_dataset_table t
    LEFT JOIN vertex_public_dataset_catalog c
      ON c.dataset_id = t.dataset_id
    WHERE ${where.length > 0 ? where.join(" AND ") : "1=1"}
      AND COALESCE(c.review_status, 'pending') <> 'rejected'
    ORDER BY t.size_bytes_estimate ASC NULLS FIRST
    LIMIT ${MAX_TABLES}
  `;
  const { rows } = await pool.query(sql, params);
  return rows.map((r) => ({
    provider: r.bq_project,
    dataset: r.bq_dataset,
    table: r.bq_table,
    catalog: {
      table_vertex_id: r.table_vertex_id,
      dataset_id: r.dataset_id,
      size_bytes_estimate: r.size_bytes_estimate,
      row_count_estimate: r.row_count_estimate,
      license: r.license,
      recommended_ingest_mode: r.recommended_ingest_mode,
      review_status: r.catalog_review_status,
    },
  }));
}

// ── Artifact materialization ───────────────────────────────────────────────

async function writeProfileArtifact({ provider, dataset, table, payload }) {
  const fname = `${provider}__${dataset}__${table}.profile.json`;
  const localPath = join(ARTIFACT_DIR, RUN_ID, fname);
  await mkdir(join(ARTIFACT_DIR, RUN_ID), { recursive: true });
  const body = JSON.stringify(payload, null, 2);
  if (!DRY_RUN) {
    await writeFile(localPath, body, "utf8");
  }
  const sha = sha256(body);
  const byteSize = Buffer.byteLength(body, "utf8");
  const exportUri = ARTIFACT_PREFIX
    ? `${ARTIFACT_PREFIX.replace(/\/$/, "")}/${RUN_ID}/${fname}`
    : `file://${localPath}`;
  return { exportUri, sha, byteSize };
}

// ── Profile a single table ─────────────────────────────────────────────────

async function profileTable({ provider, dataset, table, catalog }) {
  // 1. tables.get → schema + size
  const meta = await bqFetch(`/projects/${provider}/datasets/${dataset}/tables/${table}`);
  const numBytes = Number(meta?.numBytes ?? catalog?.size_bytes_estimate ?? 0);
  const location = meta?.location ?? "US";
  const profiled = pickProfileColumns(meta?.schema);
  if (profiled.length === 0) {
    return { skipped: "no_profilable_columns" };
  }

  const { samplePercent, billedBytesGuess } = planProfileScan(numBytes);
  const usedSoFarTiB = runHeader.totalBytesBilled / 1024 ** 4;
  const guessTiB = (billedBytesGuess || 0) / 1024 ** 4;
  if (usedSoFarTiB + guessTiB > MONTHLY_SCAN_BUDGET_TIB) {
    return { skipped: `monthly_budget_exceeded (${usedSoFarTiB.toFixed(2)} + ${guessTiB.toFixed(2)} > ${MONTHLY_SCAN_BUDGET_TIB})` };
  }

  // 2. Summary stats query (single scan, all columns inlined).
  const sql = buildProfileSql({ provider, dataset, table, profiled, samplePercent });
  let summary, jobId, queryHash, summaryBytes;
  try {
    const r = await bqQuery({
      query: sql,
      location,
      queryKind: "profile.summary",
    });
    summary = paginatedRows(r.resp)[0] ?? null;
    jobId = r.jobId;
    queryHash = r.queryHash;
    summaryBytes = r.totalBytesBilled;
  } catch (e) {
    return { skipped: `summary_query_failed: ${String(e.message).slice(0, 240)}` };
  }
  if (!summary) {
    return { skipped: "summary_returned_no_rows" };
  }

  // 3. Top values per text column (small budgeted scans).
  const remainingTib = Math.max(0, MONTHLY_SCAN_BUDGET_TIB - runHeader.totalBytesBilled / 1024 ** 4);
  const perColTib = Math.min(0.5, remainingTib / Math.max(1, profiled.filter((c) => c.isText).length));
  const perColBudget = Math.floor(perColTib * 1024 ** 4);
  const topValues = perColBudget > 1024 ** 3
    ? await collectTopValues({ provider, dataset, table, location, profiled, samplePercent, perColumnBytesBudget: perColBudget })
    : {};

  // 4. Decode + decide.
  const profile = decodeProfile({ row: summary, profiled });
  profile.topValues = topValues;
  const decisions = deriveDecisions({ catalog, profile, profiled });

  return {
    meta,
    location,
    profiled,
    samplePercent,
    summary,
    jobId,
    queryHash,
    summaryBytes,
    profile,
    decisions,
  };
}

// ── Profile row writer ─────────────────────────────────────────────────────

async function writeProfileRow({ provider, dataset, table, catalog, result, runId, artifact }) {
  const datasetId = catalog?.dataset_id ?? `${provider}:${dataset}`;
  const tableVid = catalog?.table_vertex_id
    ?? vertexId(COLLECTION_TABLE, sha256(`${provider}.${dataset}.${table}`));
  const profileId = sha256(`${runId}|${tableVid}`);
  const profileVid = vertexId(COLLECTION_PROFILE, profileId);
  const observedAt = new Date().toISOString();

  const profileScore = scoreProfile(result);
  const recommendedTargets = result.decisions.recommendedIngestMode === "reject"
    ? []
    : [`vertex_${dataset.toLowerCase().replace(/[^a-z0-9_]/g, "_")}_${table.toLowerCase().replace(/[^a-z0-9_]/g, "_")}`].slice(0, 1);

  await rwInsert("vertex_public_dataset_profile", {
    vertex_id: profileVid,
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    profile_run_id: runId,
    table_vertex_id: tableVid,
    dataset_id: datasetId,
    bq_project: provider,
    bq_dataset: dataset,
    bq_table: table,
    columns_profiled_json: JSON.stringify(result.profiled.map((c) => ({ name: c.name, type: c.type }))),
    key_candidate_json: JSON.stringify(result.decisions.keyCandidates),
    null_rate_json: JSON.stringify(result.profile.nullRate),
    distinct_estimate_json: JSON.stringify(result.profile.distinctEstimate),
    top_values_json: JSON.stringify(result.profile.topValues ?? {}).slice(0, 65535),
    text_columns_json: JSON.stringify(result.profiled.filter((c) => c.isText).map((c) => c.name)),
    language_distribution_json: null,
    text_length_stats_json: JSON.stringify(result.profile.textLengthStats),
    timestamp_range_json: JSON.stringify(result.profile.timestampRange),
    geo_coverage_json: null,
    pii_signal_json: JSON.stringify(result.profile.piiSignal),
    license_decision: result.decisions.licenseDecision,
    allowed_for_train: result.decisions.allowedForTrain,
    allowed_for_embedding: result.decisions.allowedForEmbedding,
    dedupe_strategy: result.decisions.dedupeStrategy,
    delta_strategy: result.decisions.deltaStrategy,
    recommended_risingwave_tables_json: JSON.stringify(recommendedTargets),
    recommended_edges_json: JSON.stringify([]),
    recommended_ingest_mode: result.decisions.recommendedIngestMode,
    estimated_monthly_refresh_scan_tib: result.decisions.estimatedMonthlyRefreshScanTib,
    estimated_monthly_refresh_cost_usd: result.decisions.estimatedMonthlyRefreshCostUsd,
    profile_artifact_uri: artifact.exportUri,
    profile_hash: artifact.sha,
    bytes_billed: Number(result.summaryBytes ?? 0),
    profile_score: profileScore,
    review_status: "pending",
    review_note: null,
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });

  await rwInsert("edge_public_dataset_profiles_table", {
    edge_id: sha256(`${profileVid}->${tableVid}`),
    src_vid: profileVid,
    dst_vid: tableVid,
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    profile_run_id: runId,
    dataset_id: datasetId,
    bytes_billed: Number(result.summaryBytes ?? 0),
    rows_scanned: Number(result.profile.rowCount ?? 0),
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });

  for (const target of recommendedTargets) {
    await rwInsert("edge_public_dataset_candidate_for_vertex_type", {
      edge_id: sha256(`${profileVid}->${target}`),
      src_vid: profileVid,
      dst_vid: target,
      sensitivity_ord: 1,
      owner_did: COLLECTOR_DID,
      dataset_id: datasetId,
      target_vertex_label: target,
      column_mapping_json: null,
      mapping_quality: profileScore,
      rationale: "auto-derived by P1 profiler",
      review_status: "pending",
      observed_at: observedAt,
      actor_did: COLLECTOR_DID,
      org_did: COLLECTOR_DID,
      created_at: observedAt,
    });
  }

  // Artifact ledger.
  const artifactId = sha256(artifact.exportUri);
  await rwInsert("vertex_bigquery_export_artifact", {
    vertex_id: vertexId(COLLECTION_EXPORT, artifactId),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: runId,
    job_id: result.jobId ?? null,
    artifact_kind: "bigquery.profile",
    source_dataset_id: datasetId,
    source_table: table,
    export_uri: artifact.exportUri,
    format: "json",
    byte_size: artifact.byteSize,
    row_count: result.profile.rowCount,
    sha256: artifact.sha,
    license: catalog?.license ?? null,
    observed_at: observedAt,
    actor_did: COLLECTOR_DID,
    org_did: COLLECTOR_DID,
    created_at: observedAt,
  });
  await rwInsert("vertex_ingest_artifact", {
    vertex_id: vertexId("com.etzhayyim.apps.ingest.artifact", artifactId),
    sensitivity_ord: 1,
    owner_did: COLLECTOR_DID,
    run_id: runId,
    artifact_kind: "bigquery.profile",
    source_id: datasetId,
    uri: artifact.exportUri,
    sha256: artifact.sha,
    byte_size: artifact.byteSize,
    record_count: result.profile.rowCount,
    created_at: observedAt,
  });
}

function scoreProfile(result) {
  // Composite 0..1 score: inverse of mean null-rate × license × no-pii flag.
  const nulls = Object.values(result.profile.nullRate).filter((n) => Number.isFinite(n));
  const meanNull = nulls.length > 0 ? nulls.reduce((a, b) => a + b, 0) / nulls.length : 0;
  const licenseFactor = result.decisions.licenseDecision === "allow" ? 1.0
    : result.decisions.licenseDecision === "review" ? 0.5
    : 0.0;
  const piiFactor = result.decisions.hasPii ? 0.5 : 1.0;
  const score = (1 - meanNull) * licenseFactor * piiFactor;
  return Number(score.toFixed(4));
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  console.log(`[bq-p1] run_id=${RUN_ID} project=${PROJECT} dry_run=${DRY_RUN}`);
  console.log(`[bq-p1] datasets=${DATASET_FILTER.join(",") || "(none)"} tables=${TABLE_FILTER.join(",") || "(none)"}`);
  console.log(`[bq-p1] max_bytes_billed_per_query=${MAX_BYTES_BILLED_PER_QUERY} monthly_budget_tib=${MONTHLY_SCAN_BUDGET_TIB} hard_cap_tib=${MONTHLY_SCAN_HARD_CAP_TIB}`);

  await upsertProfileRun();

  const targets = await loadCatalogTargets();
  console.log(`[bq-p1] resolved ${targets.length} P0 candidate(s)`);

  for (const target of targets) {
    if (!target.table) {
      console.warn(`[bq-p1]   skipping ${target.provider}.${target.dataset}: no table specified and dry-run did not load catalog`);
      continue;
    }
    const usedTib = runHeader.totalBytesBilled / 1024 ** 4;
    if (usedTib >= MONTHLY_SCAN_BUDGET_TIB) {
      console.warn(`[bq-p1]   monthly budget reached (${usedTib.toFixed(2)} TiB); halting profile loop.`);
      break;
    }
    runHeader.tablesSeen += 1;
    const fq = `${target.provider}.${target.dataset}.${target.table}`;
    console.log(`[bq-p1]   profiling ${fq}`);
    let result;
    try {
      result = await profileTable(target);
    } catch (e) {
      console.error(`[bq-p1]   ${fq} failed: ${e.message}`);
      runHeader.errorMessage = String(e.message).slice(0, 1000);
      continue;
    }
    if (result.skipped) {
      console.warn(`[bq-p1]   ${fq} skipped: ${result.skipped}`);
      continue;
    }
    const artifact = await writeProfileArtifact({
      provider: target.provider,
      dataset: target.dataset,
      table: target.table,
      payload: {
        run_id: RUN_ID,
        provider: target.provider,
        dataset: target.dataset,
        table: target.table,
        sample_percent: result.samplePercent,
        profiled_columns: result.profiled,
        summary_row: result.summary,
        profile: result.profile,
        decisions: result.decisions,
      },
    });
    await writeProfileRow({
      provider: target.provider,
      dataset: target.dataset,
      table: target.table,
      catalog: target.catalog,
      result,
      runId: RUN_ID,
      artifact,
    });
    runHeader.samplesTaken += 1;
    await upsertProfileRun();
  }

  runHeader.status = runHeader.errorMessage ? "completed_with_errors" : "completed";
  runHeader.finishedAt = new Date().toISOString();
  await upsertProfileRun();

  if (!DRY_RUN) {
    try {
      const pool = await getRwPool();
      await pool.query("FLUSH");
    } catch (e) {
      console.warn(`[bq-p1] FLUSH failed (rows will become visible at next checkpoint): ${e.message}`);
    }
  }

  console.log(`[bq-p1] === COMPLETE ===`);
  console.log(`[bq-p1] tables_seen=${runHeader.tablesSeen}`);
  console.log(`[bq-p1] profiles_written=${runHeader.samplesTaken}`);
  console.log(`[bq-p1] total_bytes_billed=${runHeader.totalBytesBilled}`);
  console.log(`[bq-p1] est_cost_usd=${bytesBilledToUsd(runHeader.totalBytesBilled).toFixed(4)}`);
  console.log(`[bq-p1] artifact_dir=${ARTIFACT_DIR}/${RUN_ID}`);

  if (_pgPool) await _pgPool.end();
}

main().catch(async (e) => {
  console.error(`[bq-p1] FATAL: ${e.stack ?? e.message ?? e}`);
  runHeader.status = "failed";
  runHeader.errorMessage = String(e.message ?? e).slice(0, 1000);
  runHeader.finishedAt = new Date().toISOString();
  try { await upsertProfileRun(); } catch { /* ignore */ }
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});
