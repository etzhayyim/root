#!/usr/bin/env node
/**
 * USFS FIA → vertex_forest_inventory adapter.
 * License: US-Public-Domain. Tables: plot + condition_class.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:usfs_fia";
const ACTOR_HOST = "forest-inventory";
const COLLECTION = "com.etzhayyim.apps.forestry.plot";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const ROW_LIMIT = Number(args["row-limit"] ?? 50000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(50 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-fia-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_forest_inventory" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "plot_joined" });
  const cursorCn = (cursor?.cursor_value || "cn=").replace(/^cn=/, "");
  console.log(`[fia] run=${RUN_ID} cursor_cn=${cursorCn || "(start)"}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "plot_joined",
    cursorValue: `cn=${cursorCn}`, highWatermark: "cn=+inf",
    runId: RUN_ID, status: "in_flight",
  });

  const sql = `
    SELECT p.cn AS plot_cn, p.statecd, p.countycd, p.invyr, p.lat, p.lon,
           c.fortypcd AS forest_type_code, c.stdage AS stand_age_years,
           c.stdszcd AS stand_size_class, c.owngrpcd AS ownership_group_code
    FROM \`bigquery-public-data.usfs_fia.plot\` AS p
    LEFT JOIN \`bigquery-public-data.usfs_fia.condition_class\` AS c
      ON p.cn = c.plt_cn
    WHERE p.cn > '${cursorCn}'
    ORDER BY p.cn ASC
    LIMIT ${ROW_LIMIT}
  `;
  let res, jobId, queryHash, maxCn = cursorCn;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: "projection.fia.plot_joined" });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: "projection.fia.plot_joined", queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[fia] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    maxCn = rows.reduce((acc, r) => (String(r.plot_cn) > acc ? String(r.plot_cn) : acc), cursorCn);
    const inserts = rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, `fia-${r.plot_cn}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      plot_id: String(r.plot_cn), state_code: String(r.statecd ?? ""),
      county_code: String(r.countycd ?? ""),
      inventory_year: r.invyr === null ? null : Number(r.invyr),
      latitude: r.lat === null ? null : Number(r.lat),
      longitude: r.lon === null ? null : Number(r.lon),
      forest_type_code: r.forest_type_code === null ? null : String(r.forest_type_code),
      stand_age_years: r.stand_age_years === null ? null : Number(r.stand_age_years),
      stand_size_class: r.stand_size_class === null ? null : String(r.stand_size_class),
      ownership_group_code: r.ownership_group_code === null ? null : String(r.ownership_group_code),
      biomass_dry_kg: null, carbon_dry_kg: null, props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_forest_inventory",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","plot_id",
                  "state_code","county_code","inventory_year","latitude","longitude",
                  "forest_type_code","stand_age_years","stand_size_class","ownership_group_code",
                  "biomass_dry_kg","carbon_dry_kg","props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[fia] → vertex_forest_inventory n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: "plot_joined",
        exportUri: `rw://vertex_forest_inventory?run=${RUN_ID}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|plot_joined|${written}`), license: "US-Public-Domain",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "plot_joined",
      cursorValue: `cn=${maxCn}`, highWatermark: `cn=${maxCn}`,
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
  console.log(`[fia] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[fia] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
