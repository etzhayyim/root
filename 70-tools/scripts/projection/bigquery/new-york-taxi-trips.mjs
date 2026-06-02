#!/usr/bin/env node
/**
 * New York Taxi Trips → vertex_taxi_trip (city=nyc) adapter.
 * License: NYC-Open-Data. Yellow + green taxi tables.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:new_york_taxi_trips";
const ACTOR_HOST = "taxi";
const COLLECTION = "com.etzhayyim.apps.transport.taxi_trip";
const CITY = "nyc";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const YEAR = Number(args.year ?? 2023);
  const TABLE = args.table ?? `tlc_yellow_trips_${YEAR}`;
  const VENDOR = args.vendor ?? "tlc_yellow";
  const ROW_LIMIT = Number(args["row-limit"] ?? 100000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-nyctaxi-${YEAR}-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_taxi_trip" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const shardKey = `${TABLE}`;
  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey });
  const cursorPickup = (cursor?.cursor_value || "pickup_datetime=").replace(/^pickup_datetime=/, "");
  console.log(`[nyc-taxi] run=${RUN_ID} year=${YEAR} table=${TABLE} cursor=${cursorPickup || "(start)"}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey,
    cursorValue: `pickup_datetime=${cursorPickup}`, highWatermark: `pickup_datetime=${YEAR}-12-31`,
    runId: RUN_ID, status: "in_flight",
  });

  const cursorClause = cursorPickup
    ? `AND pickup_datetime > TIMESTAMP('${cursorPickup}')`
    : "";
  const sql = `
    SELECT
      vendor_id, CAST(pickup_datetime AS STRING) AS pickup_datetime,
      CAST(dropoff_datetime AS STRING) AS dropoff_datetime,
      passenger_count, trip_distance,
      pickup_latitude, pickup_longitude,
      dropoff_latitude, dropoff_longitude,
      fare_amount, tip_amount, total_amount, payment_type
    FROM \`bigquery-public-data.new_york_taxi_trips.${TABLE}\`
    WHERE pickup_datetime IS NOT NULL
      ${cursorClause}
    ORDER BY pickup_datetime ASC
    LIMIT ${ROW_LIMIT}
  `;
  let res, jobId, queryHash, maxPickup = cursorPickup;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: `projection.nyc_taxi.${TABLE}` });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: `projection.nyc_taxi.${TABLE}`, queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[nyc-taxi] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    maxPickup = rows.reduce((acc, r) => (r.pickup_datetime > acc ? r.pickup_datetime : acc), cursorPickup);
    const inserts = rows.map((r) => {
      const tripKey = sha256([CITY, VENDOR, r.pickup_datetime, r.dropoff_datetime, r.pickup_latitude, r.pickup_longitude].join("|"));
      return {
        vertex_id: vertexId(ACTOR_HOST, COLLECTION, tripKey),
        sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
        city: CITY, vendor: r.vendor_id ?? VENDOR,
        pickup_datetime: r.pickup_datetime, dropoff_datetime: r.dropoff_datetime,
        passenger_count: r.passenger_count === null ? null : Number(r.passenger_count),
        trip_distance_m: r.trip_distance === null ? null : Math.round(Number(r.trip_distance) * 1609.34),
        pickup_latitude: r.pickup_latitude === null ? null : Number(r.pickup_latitude),
        pickup_longitude: r.pickup_longitude === null ? null : Number(r.pickup_longitude),
        dropoff_latitude: r.dropoff_latitude === null ? null : Number(r.dropoff_latitude),
        dropoff_longitude: r.dropoff_longitude === null ? null : Number(r.dropoff_longitude),
        fare_amount_minor: r.fare_amount === null ? null : Math.round(Number(r.fare_amount) * 100),
        tip_amount_minor: r.tip_amount === null ? null : Math.round(Number(r.tip_amount) * 100),
        total_amount_minor: r.total_amount === null ? null : Math.round(Number(r.total_amount) * 100),
        currency: "USD", payment_type: r.payment_type, trip_id: tripKey,
        props: null,
        actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
        created_at: new Date().toISOString(),
      };
    });
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
      console.log(`[nyc-taxi] → vertex_taxi_trip n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: TABLE,
        exportUri: `rw://vertex_taxi_trip?run=${RUN_ID}&city=${CITY}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${TABLE}|${written}`), license: "NYC-Open-Data",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey,
      cursorValue: `pickup_datetime=${maxPickup}`,
      highWatermark: `pickup_datetime=${YEAR}-12-31`,
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
  console.log(`[nyc-taxi] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[nyc-taxi] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
