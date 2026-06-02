#!/usr/bin/env node
/**
 * CMS Synthetic OMOP → vertex_synthetic_patient adapter.
 * License: US-Public-Domain. OMOP CDM `person` table.
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:cms_synthetic_patient_data_omop";
const ACTOR_HOST = "synthetic-patient";
const COLLECTION = "com.etzhayyim.apps.healthcare.synthetic_patient";

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const ROW_LIMIT = Number(args["row-limit"] ?? 50000);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(50 * 1024 ** 3));
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-cms-omop-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_synthetic_patient" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "person" });
  const cursorPerson = Number((cursor?.cursor_value || "person_id=0").replace(/^person_id=/, "")) || 0;
  console.log(`[cms-omop] run=${RUN_ID} cursor_person_id=${cursorPerson}`);

  await saveCursor({
    ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "person",
    cursorValue: `person_id=${cursorPerson}`, highWatermark: `person_id=+inf`,
    runId: RUN_ID, status: "in_flight",
  });

  const sql = `
    SELECT person_id, gender_concept_id, year_of_birth, month_of_birth,
           race_concept_id, ethnicity_concept_id, location_id, provider_id, care_site_id
    FROM \`bigquery-public-data.cms_synthetic_patient_data_omop.person\`
    WHERE person_id > ${cursorPerson}
    ORDER BY person_id ASC
    LIMIT ${ROW_LIMIT}
  `;
  let res, jobId, queryHash, maxPerson = cursorPerson;
  try {
    res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: "projection.cms_omop.person" });
    if (!res.ok) throw res.error;
    jobId = res.jobId; queryHash = res.queryHash;
    totalBytesBilled += res.bytesBilled;
    await recordIngestJob({
      jobId, runId: RUN_ID, queryKind: "projection.cms_omop.person", queryHash,
      project: PROJECT, location: "US",
      maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
      cacheHit: false, status: "done", errorReason: null, errorMessage: null,
      startedAt: res.startedAt, finishedAt: res.finishedAt,
    });
  } catch (e) {
    errorMessage = String(e.message).slice(0, 1000);
    console.error(`[cms-omop] failed: ${e.message}`);
  }

  if (res?.ok) {
    const rows = flattenRows(res.schema, res.rows);
    maxPerson = rows.reduce((acc, r) => Math.max(acc, Number(r.person_id || 0)), cursorPerson);
    const inserts = rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, `cms-${r.person_id}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      person_id: String(r.person_id),
      gender_concept_id: r.gender_concept_id === null ? null : Number(r.gender_concept_id),
      year_of_birth: r.year_of_birth === null ? null : Number(r.year_of_birth),
      month_of_birth: r.month_of_birth === null ? null : Number(r.month_of_birth),
      race_concept_id: r.race_concept_id === null ? null : Number(r.race_concept_id),
      ethnicity_concept_id: r.ethnicity_concept_id === null ? null : Number(r.ethnicity_concept_id),
      location_id: r.location_id, provider_id: r.provider_id, care_site_id: r.care_site_id,
      condition_concept_id: null, drug_concept_id: null, visit_concept_id: null,
      condition_start_date: null,
      props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));
    if (!DRY_RUN && inserts.length > 0) {
      const written = await rwBatchInsert({
        table: "vertex_synthetic_patient",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","person_id",
                  "gender_concept_id","year_of_birth","month_of_birth",
                  "race_concept_id","ethnicity_concept_id","location_id","provider_id","care_site_id",
                  "condition_concept_id","drug_concept_id","visit_concept_id","condition_start_date",
                  "props","actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[cms-omop] → vertex_synthetic_patient n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: "person",
        exportUri: `rw://vertex_synthetic_patient?run=${RUN_ID}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|person|${written}`), license: "US-Public-Domain",
      });
    }
    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: "person",
      cursorValue: `person_id=${maxPerson}`, highWatermark: `person_id=${maxPerson}`,
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
  console.log(`[cms-omop] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[cms-omop] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
