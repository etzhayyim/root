#!/usr/bin/env node
/**
 * Open Targets Platform → vertex_target_evidence adapter.
 * License: CC0-1.0. Drug-target evidence rows.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:open_targets_platform";
const ACTOR_HOST = "open-targets";
const COLLECTION = "com.etzhayyim.apps.bio.target_evidence";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const TABLE = args.table ?? "association_overall_direct";
  const ROW_LIMIT = Number(args["row-limit"] ?? 100000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(50 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-ot-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_target_evidence" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE });
  const cursorOffset = Number((cursor?.cursor_value || "row_offset=0").replace(/^row_offset=/, "")) || 0;
  console.log(`[ot] run=${RUN_ID} table=${TABLE} cursor_offset=${cursorOffset}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE,
    cursorValue: `row_offset=${cursorOffset}`, highWatermark: `row_offset=${cursorOffset + ROW_LIMIT}`,
    runId: RUN_ID, status: "in_flight",
  });

  const sql = `
    SELECT targetId AS target_id, diseaseId AS disease_id, score
    FROM \`bigquery-public-data.open_targets_platform.${TABLE}\`
    ORDER BY targetId, diseaseId
    LIMIT ${ROW_LIMIT} OFFSET ${cursorOffset}
  `;
  let res, jobId, queryHash;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: `projection.ot.${TABLE}` });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: `projection.ot.${TABLE}`, queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[ot] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    const inserts = rows.map((r, idx) => {
      const evidenceId = sha256([TABLE, cursorOffset + idx, r.target_id, r.disease_id].join("|"));
      return {
        vertex_id: vertexId(ACTOR_HOST, COLLECTION, evidenceId),
        sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
        evidence_id: evidenceId,
        target_id: r.target_id, disease_id: r.disease_id,
        datatype_id: "association.overall_direct", datasource_id: "open_targets",
        score: r.score === null ? null : Number(r.score),
        evidence_origin: "open_targets.platform",
        literature_pmids: null, release_year: null,
        props: null,
        actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
        created_at: new Date().toISOString(),
      };
    });
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_target_evidence",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","evidence_id",
                  "target_id","disease_id","datatype_id","datasource_id","score","evidence_origin",
                  "literature_pmids","release_year","props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[ot] → vertex_target_evidence n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: TABLE,
        exportUri: `rw://vertex_target_evidence?run=${RUN_ID}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${TABLE}|${written}`), license: "CC0-1.0",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE,
      cursorValue: `row_offset=${cursorOffset + rows.length}`,
      highWatermark: `row_offset=${cursorOffset + rows.length}`,
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
  console.log(`[ot] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[ot] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
