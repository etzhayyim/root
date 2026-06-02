#!/usr/bin/env node
/**
 * Chicago Taxi Trips → vertex_taxi_trip (city=chicago) adapter.
 * License: Chicago-Open-Data.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:chicago_taxi_trips";
const ACTOR_HOST = "taxi";
const COLLECTION = "com.etzhayyim.apps.transport.taxi_trip";
const CITY = "chicago";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const ROW_LIMIT = Number(args["row-limit"] ?? 100000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-chitaxi-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_taxi_trip" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "taxi_trips" });
  const cursorStart = (cursor?.cursor_value || "trip_start_timestamp=").replace(/^trip_start_timestamp=/, "");
  console.log(`[chi-taxi] run=${RUN_ID} cursor=${cursorStart || "(start)"}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "taxi_trips",
    cursorValue: `trip_start_timestamp=${cursorStart}`,
    highWatermark: `trip_start_timestamp=+inf`,
    runId: RUN_ID, status: "in_flight",
  });

  const cursorClause = cursorStart
    ? `AND trip_start_timestamp > TIMESTAMP('${cursorStart}')`
    : "";
  const sql = `
    SELECT unique_key AS trip_id, taxi_id AS vendor,
           CAST(trip_start_timestamp AS STRING) AS pickup_datetime,
           CAST(trip_end_timestamp AS STRING) AS dropoff_datetime,
           trip_miles, pickup_latitude, pickup_longitude,
           dropoff_latitude, dropoff_longitude,
           fare, tips, trip_total AS total_fare, payment_type
    FROM \`bigquery-public-data.chicago_taxi_trips.taxi_trips\`
    WHERE trip_start_timestamp IS NOT NULL
      ${cursorClause}
    ORDER BY trip_start_timestamp ASC
    LIMIT ${ROW_LIMIT}
  `;
  let res, jobId, queryHash, maxStart = cursorStart;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: "projection.chi_taxi.taxi_trips" });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: "projection.chi_taxi.taxi_trips", queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[chi-taxi] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    maxStart = rows.reduce((acc, r) => (r.pickup_datetime > acc ? r.pickup_datetime : acc), cursorStart);
    const inserts = rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, `${CITY}-${r.trip_id}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      city: CITY, vendor: r.vendor,
      pickup_datetime: r.pickup_datetime, dropoff_datetime: r.dropoff_datetime,
      passenger_count: null,
      trip_distance_m: r.trip_miles === null ? null : Math.round(Number(r.trip_miles) * 1609.34),
      pickup_latitude: r.pickup_latitude === null ? null : Number(r.pickup_latitude),
      pickup_longitude: r.pickup_longitude === null ? null : Number(r.pickup_longitude),
      dropoff_latitude: r.dropoff_latitude === null ? null : Number(r.dropoff_latitude),
      dropoff_longitude: r.dropoff_longitude === null ? null : Number(r.dropoff_longitude),
      fare_amount_minor: r.fare === null ? null : Math.round(Number(r.fare) * 100),
      tip_amount_minor: r.tips === null ? null : Math.round(Number(r.tips) * 100),
      total_amount_minor: r.total_fare === null ? null : Math.round(Number(r.total_fare) * 100),
      currency: "USD", payment_type: r.payment_type, trip_id: r.trip_id,
      props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_taxi_trip",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","city","vendor",
                  "pickup_datetime","dropoff_datetime","passenger_count","trip_distance_m",
                  "pickup_latitude","pickup_longitude","dropoff_latitude","dropoff_longitude",
                  "fare_amount_minor","tip_amount_minor","total_amount_minor","currency","payment_type","trip_id",
                  "props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[chi-taxi] → vertex_taxi_trip n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: "taxi_trips",
        exportUri: `rw://vertex_taxi_trip?run=${RUN_ID}&city=${CITY}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|taxi_trips|${written}`), license: "Chicago-Open-Data",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "taxi_trips",
      cursorValue: `trip_start_timestamp=${maxStart}`,
      highWatermark: `trip_start_timestamp=${maxStart}`,
      runId: RUN_ID, status: rows.length === ROW_LIMIT ? "partial" : "complete",
      lastRowCount: totalRows,
    });
  }

  if (!DRY_RUN) await rwFlush();
  await recordRunHeader({
    runId: RUN_ID, mode: "projection", project: PROJECT,
    providerFilter: "bigquery-public-data", datasetFilter: DATASET_ID,
    startedAt: runStartedAt, finishedAt: new Date().toISOString(),
    status: errorMessage ? "completed_with_errors" : "completed",
    datasetsSeen: 1, tablesSeen: 1, samplesTaken: totalRows,
    totalBytesBilled, maxBytesBilledPerQuery: Number(MAX_BYTES),
    monthlyScanBudgetTib: Number(binding.scan_budget_tib ?? 0.1),
    monthlyScanUsedTib: totalBytesBilled / 1024 ** 4,
    approvalNote: binding.approved_by ?? null, errorMessage,
  });
  console.log(`[chi-taxi] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[chi-taxi] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
