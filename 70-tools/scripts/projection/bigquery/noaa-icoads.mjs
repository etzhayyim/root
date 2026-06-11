#!/usr/bin/env node
/**
 * NOAA ICOADS → vertex_marine_observation adapter.
 * License: US-Public-Domain.
 * Table: `noaa_icoads.icoads_core_2017` (latest mature release).
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:noaa_icoads";
const ACTOR_HOST = "marine";
const COLLECTION = "com.etzhayyim.apps.marine.observation";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const TABLE = args.table ?? "icoads_core_2017";
  const ROW_LIMIT = Number(args["row-limit"] ?? 100000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-icoads-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_marine_observation" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE });
  const cursorRow = Number((cursor?.cursor_value || "row_offset=0").replace(/^row_offset=/, "")) || 0;
  console.log(`[icoads] run=${RUN_ID} table=${TABLE} cursor_offset=${cursorRow} limit=${ROW_LIMIT}`);

  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE,
    cursorValue: `row_offset=${cursorRow}`, highWatermark: `row_offset=${cursorRow + ROW_LIMIT}`,
    runId: RUN_ID, status: "in_flight",
  });

  const sql = `
    SELECT
      year, month, day, hour, latitude, longitude,
      sea_surface_temp, air_temperature,
      wind_direction_true, wind_speed,
      sea_level_pressure, callsign, country_id
    FROM \`bigquery-public-data.noaa_icoads.${TABLE}\`
    WHERE year IS NOT NULL
    LIMIT ${ROW_LIMIT}
    OFFSET ${cursorRow}
  `;
  let res, jobId, queryHash;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: `projection.icoads.${TABLE}` });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: `projection.icoads.${TABLE}`, queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    console.error(`[icoads] ${TABLE} failed: ${e.message}`);
    errorMessage = String(e.message).slice(0, 1000);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    console.log(`[icoads] ${TABLE} rows=${rows.length} bytes_billed=${res.bytesBilled}`);
    const inserts = rows.map((r, idx) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, sha256([TABLE, cursorRow + idx, r.year, r.month, r.day, r.hour, r.latitude, r.longitude, r.callsign].join("|"))),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      observed_at: (r.year && r.month && r.day) ? `${r.year}-${String(r.month).padStart(2,"0")}-${String(r.day).padStart(2,"0")}T${String(r.hour ?? 0).padStart(2,"0")}:00:00Z` : null,
      year: r.year === null ? null : Number(r.year),
      month: r.month === null ? null : Number(r.month),
      day: r.day === null ? null : Number(r.day),
      hour: r.hour === null ? null : Number(r.hour),
      latitude: r.latitude === null ? null : Number(r.latitude),
      longitude: r.longitude === null ? null : Number(r.longitude),
      sea_surface_temp_c: r.sea_surface_temp === null ? null : Number(r.sea_surface_temp),
      air_temp_c: r.air_temperature === null ? null : Number(r.air_temperature),
      wind_direction_deg: r.wind_direction_true === null ? null : Number(r.wind_direction_true),
      wind_speed_mps: r.wind_speed === null ? null : Number(r.wind_speed),
      pressure_hpa: r.sea_level_pressure === null ? null : Number(r.sea_level_pressure),
      platform_id: null, callsign: r.callsign, country_code: r.country_id,
      props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_marine_observation",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","observed_at",
                  "year","month","day","hour","latitude","longitude",
                  "sea_surface_temp_c","air_temp_c","wind_direction_deg","wind_speed_mps","pressure_hpa",
                  "platform_id","callsign","country_code","props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[icoads] ${TABLE} → vertex_marine_observation n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: TABLE,
        exportUri: `rw://vertex_marine_observation?run=${RUN_ID}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${TABLE}|${written}`), license: "US-Public-Domain",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE,
      cursorValue: `row_offset=${cursorRow + rows.length}`,
      highWatermark: `row_offset=${cursorRow + rows.length}`,
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
  console.log(`[icoads] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[icoads] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
