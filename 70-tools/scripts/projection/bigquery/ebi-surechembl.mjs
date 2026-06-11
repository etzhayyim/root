#!/usr/bin/env node
/**
 * EBI SureChEMBL → vertex_chemistry_patent adapter.
 * License: CC-BY-SA-3.0. Chemistry mention extracted from patents.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:ebi_surechembl";
const ACTOR_HOST = "chemistry-patent";
const COLLECTION = "com.etzhayyim.apps.chemistry.patent_mention";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const TABLE = args.table ?? "molecule_patent";
  const ROW_LIMIT = Number(args["row-limit"] ?? 50000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(50 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-schembl-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_chemistry_patent" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE });
  const cursorOffset = Number((cursor?.cursor_value || "row_offset=0").replace(/^row_offset=/, "")) || 0;
  console.log(`[schembl] run=${RUN_ID} table=${TABLE} cursor_offset=${cursorOffset}`);
  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: TABLE,
    cursorValue: `row_offset=${cursorOffset}`, highWatermark: `row_offset=${cursorOffset + ROW_LIMIT}`,
    runId: RUN_ID, status: "in_flight",
  });

  // The dataset exposes molecule + patent + linking tables. v1 emits one
  // vertex per (schembl_id, patent_id) pair from the linking table.
  const sql = `
    SELECT schembl_id, patent_id,
           CAST(publication_date AS STRING) AS patent_publication_date,
           ipc_main_class AS ipc_code
    FROM \`bigquery-public-data.ebi_surechembl.${TABLE}\`
    ORDER BY schembl_id, patent_id
    LIMIT ${ROW_LIMIT} OFFSET ${cursorOffset}
  `;
  let res, jobId, queryHash;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: `projection.schembl.${TABLE}` });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: `projection.schembl.${TABLE}`, queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[schembl] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    const inserts = rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, `${r.schembl_id}-${r.patent_id}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      schembl_id: String(r.schembl_id), patent_id: r.patent_id,
      patent_publication_date: r.patent_publication_date,
      chembl_id: null, inchi_key: null, smiles: null,
      ipc_code: r.ipc_code, cpc_code: null, family_id: null,
      props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_chemistry_patent",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","schembl_id","patent_id",
                  "patent_publication_date","chembl_id","inchi_key","smiles","ipc_code","cpc_code","family_id",
                  "props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[schembl] → vertex_chemistry_patent n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: TABLE,
        exportUri: `rw://vertex_chemistry_patent?run=${RUN_ID}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${TABLE}|${written}`), license: "CC-BY-SA-3.0",
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
  console.log(`[schembl] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[schembl] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
