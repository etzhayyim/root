#!/usr/bin/env node
/**
 * EPA Historical Air Quality → vertex_air_quality_observation adapter.
 *
 * ADR-2605101000 §"Adapter Catalog (initial)" Tier 1.
 *
 * Source: bigquery-public-data:epa_historical_air_quality (US-Public-Domain).
 *
 * Strategy:
 *   - One projection query per daily_summary table covering the six
 *     standard EPA criteria pollutants (O3 / PM2.5 / PM10 / CO / NO2 / SO2).
 *   - Bound by `--year-from` (default 2024) and `--year-to` (default current
 *     year) on `date_local` to make the slice deterministic and re-runnable.
 *   - Narrow column projection: state_code, county_code, site_num,
 *     parameter_code, parameter_name, date_local, arithmetic_mean,
 *     units_of_measure, observation_count, latitude, longitude.
 *   - vertex_id = at://did:web:airquality.etzhayyim.com/com.etzhayyim.apps.airquality.observation/
 *                 sha256(state|county|site|parameter|date)
 *   - Record-log upsert: re-running with same window overwrites in place.
 *
 * Usage:
 *   node 70-tools/scripts/projection/bigquery/epa-historical-air-quality.mjs \
 *     --project etzhayyim-ws-ingest \
 *     [--year-from 2024] [--year-to 2025] \
 *     [--max-bytes-billed-per-query 107374182400]  # 100 GiB default \
 *     [--tables o3_daily_summary,pm25_frm_daily_summary,...] \
 *     [--dry-run]
 */

import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor, formatCursorKv,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";

const DEFAULT_TABLES = [
  "o3_daily_summary",
  "pm25_frm_daily_summary",
  "pm10_daily_summary",
  "co_daily_summary",
  "no2_daily_summary",
  "so2_daily_summary",
];

const DATASET_ID = "bigquery-public-data:epa_historical_air_quality";
const TARGET_LABEL = "vertex_air_quality_observation";
const ACTOR_HOST = "airquality";
const COLLECTION = "com.etzhayyim.apps.airquality.observation";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const YEAR_FROM = Number(args["year-from"] ?? 2024);
  const YEAR_TO = Number(args["year-to"] ?? new Date().getUTCFullYear());
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const TABLES = (args.tables ?? DEFAULT_TABLES.join(",")).split(",").map((s) => s.trim()).filter(Boolean);
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-epa-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  console.log(`[epa-aq] run_id=${RUN_ID} project=${PROJECT} year_from=${YEAR_FROM} year_to=${YEAR_TO} dry_run=${DRY_RUN}`);

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: TARGET_LABEL });
  console.log(`[epa-aq] binding ok ingest_mode=${binding.ingest_mode} budget_tib=${binding.scan_budget_tib}`);

  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0;
  let totalRows = 0;
  let errorMessage = null;

  for (const bqTable of TABLES) {
    // Per-table cursor: window the WHERE clause to (cursor.date_local, year_to]
    // so a 2nd run only picks up dates we did not already commit.
    const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bqTable });
    const cursorDate = (cursor?.cursor_value || "").replace(/^date_local=/, "");
    const fromDateStr = cursorDate || `${YEAR_FROM}-01-01`;
    const toDateStr = `${YEAR_TO}-12-31`;
    if (cursorDate && cursorDate >= toDateStr) {
      console.log(`[epa-aq] table=${bqTable} cursor at ${cursorDate} >= ${toDateStr}; nothing to do`);
      continue;
    }
    console.log(`[epa-aq] table=${bqTable} window=${fromDateStr}..${toDateStr}${cursorDate ? ` (resume)` : ""}`);

    const sql = `
      SELECT
        state_code, county_code, site_num,
        parameter_code, parameter_name,
        CAST(date_local AS STRING) AS date_local,
        arithmetic_mean, units_of_measure, observation_count,
        latitude, longitude
      FROM \`bigquery-public-data.epa_historical_air_quality.${bqTable}\`
      WHERE date_local > DATE('${fromDateStr}')
        AND date_local <= DATE('${toDateStr}')
    `;
    const concrete = sql;
    // Pre-save "in-flight" cursor so a crash leaves clear evidence.
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bqTable,
      cursorValue: cursorDate ? `date_local=${cursorDate}` : "",
      highWatermark: `date_local=${toDateStr}`,
      runId: RUN_ID, status: "in_flight",
      windowFrom: fromDateStr, windowTo: toDateStr, lastRowCount: 0,
    });

    let rows = [];
    let bytesBilled = 0;
    let jobId = null;
    let queryHash = null;
    try {
      const result = await bqQueryAll({
        project: PROJECT,
        query: concrete,
        maximumBytesBilled: MAX_BYTES,
        queryKind: `projection.epa.${bqTable}`,
      });
      if (!result.ok) throw result.error;
      jobId = result.jobId;
      queryHash = result.queryHash;
      bytesBilled = result.bytesBilled;
      totalBytesBilled += bytesBilled;
      rows = flattenRows(result.schema, result.rows);

      await recordIngestJob({
        jobId, runId: RUN_ID, queryKind: `projection.epa.${bqTable}`, queryHash,
        project: PROJECT, location: "US",
        maximumBytesBilled: MAX_BYTES,
        totalBytesBilled: bytesBilled,
        cacheHit: false, status: "done",
        errorReason: null, errorMessage: null,
        startedAt: result.startedAt, finishedAt: result.finishedAt,
      });
    } catch (e) {
      console.error(`[epa-aq] ${bqTable} query failed: ${e.message}`);
      errorMessage = String(e.message).slice(0, 1000);
      try {
        await recordIngestJob({
          jobId: jobId ?? `err-${Date.now()}`, runId: RUN_ID,
          queryKind: `projection.epa.${bqTable}`, queryHash: queryHash ?? sha256(concrete),
          project: PROJECT, location: "US",
          maximumBytesBilled: MAX_BYTES, totalBytesBilled: 0,
          cacheHit: false, status: "error",
          errorReason: "QUERY_FAILED", errorMessage: errorMessage,
          startedAt: runStartedAt, finishedAt: new Date().toISOString(),
        });
      } catch { /* swallow */ }
      continue;
    }

    if (rows.length === 0) {
      console.warn(`[epa-aq] ${bqTable} returned 0 rows`);
      continue;
    }

    console.log(`[epa-aq] ${bqTable} rows=${rows.length} bytes_billed=${bytesBilled}`);

    const observedAt = new Date().toISOString();
    const inserts = rows.map((r) => {
      const rkey = sha256([
        r.state_code, r.county_code, r.site_num,
        r.parameter_code, r.date_local,
      ].join("|"));
      return {
        vertex_id: vertexId(ACTOR_HOST, COLLECTION, rkey),
        sensitivity_ord: 1,
        owner_did: COLLECTOR_DID,
        source_dataset_id: DATASET_ID,
        state_code: r.state_code,
        county_code: r.county_code,
        site_num: r.site_num,
        parameter_code: r.parameter_code,
        parameter_name: r.parameter_name,
        date_local: r.date_local,
        arithmetic_mean: r.arithmetic_mean === null || r.arithmetic_mean === undefined
          ? null : Number(r.arithmetic_mean),
        units_of_measure: r.units_of_measure,
        latitude: r.latitude === null || r.latitude === undefined
          ? null : Number(r.latitude),
        longitude: r.longitude === null || r.longitude === undefined
          ? null : Number(r.longitude),
        observation_count: r.observation_count === null || r.observation_count === undefined
          ? null : Number(r.observation_count),
        props: null,
        actor_did: COLLECTOR_DID,
        org_did: COLLECTOR_DID,
        at_did: null,
        created_at: observedAt,
      };
    });

    if (DRY_RUN) {
      console.log(`[epa-aq] dry-run skipping INSERT for ${bqTable}`);
    } else {
      const written = await rwBatchInsert({
        table: "vertex_air_quality_observation",
        columns: [
          "vertex_id", "sensitivity_ord", "owner_did", "source_dataset_id",
          "state_code", "county_code", "site_num",
          "parameter_code", "parameter_name", "date_local",
          "arithmetic_mean", "units_of_measure",
          "latitude", "longitude", "observation_count",
          "props", "actor_did", "org_did", "at_did", "created_at",
        ],
        rows: inserts,
        chunkSize: 200,
      });
      totalRows += written;
      console.log(`[epa-aq] ${bqTable} → vertex_air_quality_observation INSERT n=${written}`);

      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: bqTable,
        exportUri: `rw://vertex_air_quality_observation?run=${RUN_ID}&table=${bqTable}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${bqTable}|${written}`),
        license: "US-Public-Domain",
      });

      // Advance cursor to the max date_local actually inserted.
      const maxDate = rows.reduce(
        (acc, r) => (r.date_local && r.date_local > acc ? r.date_local : acc),
        fromDateStr,
      );
      await saveCursor({
        ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bqTable,
        cursorValue: `date_local=${maxDate}`,
        highWatermark: `date_local=${toDateStr}`,
        runId: RUN_ID, status: "complete",
        windowFrom: fromDateStr, windowTo: toDateStr, lastRowCount: written,
      });
    }
  }

  if (!DRY_RUN) await rwFlush();

  await recordRunHeader({
    runId: RUN_ID, mode: "projection", project: PROJECT,
    providerFilter: "bigquery-public-data",
    datasetFilter: DATASET_ID,
    startedAt: runStartedAt, finishedAt: new Date().toISOString(),
    status: errorMessage ? "completed_with_errors" : "completed",
    datasetsSeen: 1, tablesSeen: TABLES.length, samplesTaken: totalRows,
    totalBytesBilled, maxBytesBilledPerQuery: Number(MAX_BYTES),
    monthlyScanBudgetTib: Number(binding.scan_budget_tib ?? 0.1),
    monthlyScanUsedTib: totalBytesBilled / 1024 ** 4,
    approvalNote: binding.approved_by ?? null,
    errorMessage,
  });

  console.log(`[epa-aq] === COMPLETE ===`);
  console.log(`[epa-aq] tables=${TABLES.length} total_rows=${totalRows} total_bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[epa-aq] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
