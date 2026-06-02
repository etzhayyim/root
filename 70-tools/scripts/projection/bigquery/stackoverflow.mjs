#!/usr/bin/env node
/**
 * Stack Overflow → vertex_qa_post adapter.
 * ADR-2605101000 §"Adapter Catalog (initial)" Tier 1.
 * License: CC-BY-SA-4.0 (ShareAlike propagates downstream).
 *
 * Tables: posts_questions, posts_answers (the two primary post types).
 *   Body is stored by sha256 + byte_size; full text URI left NULL for v1
 *   (large body strings would blow up the row width).
 */
import {
  COLLECTOR_DID, sha256, vertexId, parseArgs,
  bqQueryAll, flattenRows, loadBindingOrThrow,
  rwBatchInsert, rwFlush, rwEnd, recordIngestJob, recordRunHeader, recordExportArtifact,
  loadCursor, saveCursor,
} from "./_lib.mjs";

const INGEST_FAMILY = "bigquery.public_dataset.projection";
const DATASET_ID = "bigquery-public-data:stackoverflow";
const ACTOR_HOST = "qa";
const COLLECTION = "com.etzhayyim.apps.qa.post";

const TABLES = [
  { bq: "posts_questions", post_type: "question" },
  { bq: "posts_answers", post_type: "answer" },
];

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const PROJECT = args.project ?? process.env.GOOGLE_CLOUD_PROJECT;
  if (!PROJECT) throw new Error("--project required");
  const FROM_DATE = args["from-date"] ?? "2024-01-01";
  const TO_DATE = args["to-date"] ?? new Date().toISOString().slice(0, 10);
  const MAX_BYTES = String(args["max-bytes-billed-per-query"] ?? String(100 * 1024 ** 3));
  const ROW_LIMIT = Number(args["row-limit"] ?? 200000);
  const DRY_RUN = args["dry-run"] === "true";
  const RUN_ID = args["run-id"] ?? `p2-so-${new Date().toISOString().replace(/[:.]/g, "-")}`;

  console.log(`[so] run_id=${RUN_ID} project=${PROJECT} window=${FROM_DATE}..${TO_DATE} limit=${ROW_LIMIT}`);
  const binding = await loadBindingOrThrow({ datasetId: DATASET_ID, targetVertexLabel: "vertex_qa_post" });
  const runStartedAt = new Date().toISOString();
  let totalBytesBilled = 0, totalRows = 0, errorMessage = null;

  for (const { bq, post_type } of TABLES) {
    const cursor = await loadCursor({ ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bq });
    const cursorDate = (cursor?.cursor_value || "").replace(/^creation_date=/, "");
    const fromDate = cursorDate || FROM_DATE;
    if (cursorDate && cursorDate >= TO_DATE) { console.log(`[so] ${bq} caught up`); continue; }
    console.log(`[so] table=${bq} window=${fromDate}..${TO_DATE}`);

    await saveCursor({
      ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bq,
      cursorValue: cursorDate ? `creation_date=${cursorDate}` : "",
      highWatermark: `creation_date=${TO_DATE}`,
      runId: RUN_ID, status: "in_flight",
      windowFrom: fromDate, windowTo: TO_DATE,
    });

    const sql = `
      SELECT
        id AS post_id, parent_id AS parent_post_id, accepted_answer_id,
        title, body,
        score, view_count, answer_count, comment_count, favorite_count,
        tags, owner_user_id,
        CAST(creation_date AS STRING) AS posted_at,
        CAST(last_activity_date AS STRING) AS last_activity_at,
        CAST(last_edit_date AS STRING) AS last_edit_at
      FROM \`bigquery-public-data.stackoverflow.${bq}\`
      WHERE creation_date > TIMESTAMP('${fromDate}')
        AND creation_date <= TIMESTAMP('${TO_DATE}')
      ORDER BY creation_date ASC
      LIMIT ${ROW_LIMIT}
    `;
    let res, jobId, queryHash;
    try {
      res = await bqQueryAll({ project: PROJECT, query: sql, maximumBytesBilled: MAX_BYTES, queryKind: `projection.so.${bq}` });
      if (!res.ok) throw res.error;
      jobId = res.jobId; queryHash = res.queryHash;
      totalBytesBilled += res.bytesBilled;
      await recordIngestJob({
        jobId, runId: RUN_ID, queryKind: `projection.so.${bq}`, queryHash,
        project: PROJECT, location: "US",
        maximumBytesBilled: MAX_BYTES, totalBytesBilled: res.bytesBilled,
        cacheHit: false, status: "done", errorReason: null, errorMessage: null,
        startedAt: res.startedAt, finishedAt: res.finishedAt,
      });
    } catch (e) {
      console.error(`[so] ${bq} failed: ${e.message}`);
      errorMessage = String(e.message).slice(0, 1000);
      continue;
    }
    const rows = flattenRows(res.schema, res.rows);
    if (rows.length === 0) { console.warn(`[so] ${bq} empty`); continue; }
    console.log(`[so] ${bq} rows=${rows.length} bytes_billed=${res.bytesBilled}`);

    const inserts = rows.map((r) => ({
      vertex_id: vertexId(ACTOR_HOST, COLLECTION, `so-${post_type}-${r.post_id}`),
      sensitivity_ord: 1, owner_did: COLLECTOR_DID, source_dataset_id: DATASET_ID,
      community: "stackoverflow", post_type, post_id: r.post_id,
      parent_post_id: r.parent_post_id, accepted_answer_id: r.accepted_answer_id,
      title: (r.title || "").slice(0, 4000),
      body_text_uri: null,
      body_text_sha256: r.body ? sha256(r.body) : null,
      body_byte_size: r.body ? Buffer.byteLength(r.body, "utf8") : null,
      score: r.score === null ? null : Number(r.score),
      view_count: r.view_count === null ? null : Number(r.view_count),
      answer_count: r.answer_count === null ? null : Number(r.answer_count),
      comment_count: r.comment_count === null ? null : Number(r.comment_count),
      favorite_count: r.favorite_count === null ? null : Number(r.favorite_count),
      tags: (r.tags || "").slice(0, 1024),
      owner_user_id: r.owner_user_id,
      posted_at: r.posted_at, last_activity_at: r.last_activity_at, last_edit_at: r.last_edit_at,
      language: null, license: "CC-BY-SA-4.0",
      props: null,
      actor_did: COLLECTOR_DID, org_did: COLLECTOR_DID, at_did: null,
      created_at: new Date().toISOString(),
    }));

    let maxDate = fromDate;
    for (const ins of inserts) if (ins.posted_at > maxDate) maxDate = ins.posted_at;

    if (!DRY_RUN) {
      const written = await rwBatchInsert({
        table: "vertex_qa_post",
        columns: ["vertex_id","sensitivity_ord","owner_did","source_dataset_id","community","post_type","post_id",
                  "parent_post_id","accepted_answer_id","title","body_text_uri","body_text_sha256","body_byte_size",
                  "score","view_count","answer_count","comment_count","favorite_count","tags","owner_user_id",
                  "posted_at","last_activity_at","last_edit_at","language","license","props",
                  "actor_did","org_did","at_did","created_at"],
        rows: inserts,
      });
      totalRows += written;
      console.log(`[so] ${bq} → vertex_qa_post n=${written}`);
      await recordExportArtifact({
        runId: RUN_ID, jobId, artifactKind: "bigquery.projection",
        datasetId: DATASET_ID, table: bq,
        exportUri: `rw://vertex_qa_post?run=${RUN_ID}&shard=${bq}`,
        format: "rw-inline", byteSize: null, rowCount: written,
        sha: sha256(`${RUN_ID}|${bq}|${written}`), license: "CC-BY-SA-4.0",
      });
      await saveCursor({
        ingestFamily: INGEST_FAMILY, sourceId: DATASET_ID, shardKey: bq,
        cursorValue: `creation_date=${maxDate.slice(0, 10)}`,
        highWatermark: `creation_date=${TO_DATE}`,
        runId: RUN_ID, status: rows.length === ROW_LIMIT ? "partial" : "complete",
        windowFrom: fromDate, windowTo: TO_DATE, lastRowCount: written,
      });
    }
  }

  if (!DRY_RUN) await rwFlush();
  await recordRunHeader({
    runId: RUN_ID, mode: "projection", project: PROJECT,
    providerFilter: "bigquery-public-data", datasetFilter: DATASET_ID,
    startedAt: runStartedAt, finishedAt: new Date().toISOString(),
    status: errorMessage ? "completed_with_errors" : "completed",
    datasetsSeen: 1, tablesSeen: TABLES.length, samplesTaken: totalRows,
    totalBytesBilled, maxBytesBilledPerQuery: Number(MAX_BYTES),
    monthlyScanBudgetTib: Number(binding.scan_budget_tib ?? 0.1),
    monthlyScanUsedTib: totalBytesBilled / 1024 ** 4,
    approvalNote: binding.approved_by ?? null, errorMessage,
  });
  console.log(`[so] === COMPLETE === total_rows=${totalRows} bytes_billed=${totalBytesBilled}`);
  await rwEnd();
}

main().catch(async (e) => {
  console.error(`[so] FATAL: ${e.stack ?? e.message ?? e}`);
  try { await rwEnd(); } catch { /* ignore */ }
  process.exit(1);
});
