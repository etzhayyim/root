#!/usr/bin/env node
/**
 * BigQuery public-dataset partitioning review.
 *
 * For every approved table in `vertex_public_dataset_table`, parse the
 * `partitioning_json` and `clustering_json` fields and emit a delta
 * strategy recommendation. ADR-2605101000 §D2 / §D4 require P2 adapters
 * to use partition predicates where possible to keep BQ scan cost in
 * check; this script gives the operator a one-shot view of what kind of
 * delta predicate each table supports.
 *
 * No BigQuery API calls. Reads RW only.
 *
 * Output:
 *   - markdown report → stdout (or --out <path>)
 *   - csv → optional --csv <path>
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-partitioning-review.mjs \
 *     [--provider bigquery-public-data] \
 *     [--review-status approved|pending|all]   # default: approved
 *     [--out /tmp/bq-allowlist/partitioning.md] \
 *     [--csv /tmp/bq-allowlist/partitioning.csv]
 */

import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};

const PROVIDER = arg("provider", "bigquery-public-data");
const REVIEW = arg("review-status", "approved");
const OUT = arg("out");
const CSV = arg("csv");

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2 });
  return _pgPool;
}

function safeParseJson(s) {
  try { return JSON.parse(String(s)); } catch { return null; }
}

function classifyPartition(partitioning, clustering) {
  // The P0 catalog runner stores the BQ tables.get sub-objects directly:
  //   partitioning_json  = JSON.stringify(meta.timePartitioning) e.g.
  //                        { type: 'DAY'|'HOUR'|'MONTH'|'YEAR', field: '...', expirationMs: '...' }
  //                        (and uses meta.rangePartitioning if that's set instead;
  //                        the catalog currently only persists timePartitioning).
  //   clustering_json    = JSON.stringify(meta.clustering) e.g. { fields: ['col1',...] }
  // So `partitioning_json` parsed IS the timePartitioning object (not nested).
  if (!partitioning && !clustering) return { kind: "none", delta_strategy: "full_replace" };

  const p = partitioning ? safeParseJson(partitioning) : null;
  const c = clustering ? safeParseJson(clustering) : null;

  // Time partitioning shape: top-level `type` ∈ {DAY,HOUR,MONTH,YEAR}.
  if (p && typeof p === "object" && typeof p.type === "string"
      && ["DAY","HOUR","MONTH","YEAR"].includes(p.type)) {
    const field = p.field ?? "_PARTITIONTIME";
    return {
      kind: "time",
      partition_field: field,
      partition_type: p.type,
      expiration_ms: p.expirationMs ?? null,
      cluster_fields: c?.fields ?? null,
      delta_strategy: "partition_delta",
      where_template:
        `WHERE ${field} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @lookback_days DAY)`,
    };
  }
  // Range partitioning shape: top-level `range` + `field`.
  if (p && typeof p === "object" && p.field && p.range) {
    return {
      kind: "integer-range",
      partition_field: p.field,
      partition_range: p.range,
      cluster_fields: c?.fields ?? null,
      delta_strategy: "range_partition_delta",
      where_template: `WHERE ${p.field} BETWEEN @range_start AND @range_end`,
    };
  }
  if (c?.fields?.length) {
    return {
      kind: "clustered-only",
      cluster_fields: c.fields,
      delta_strategy: "clustered_filter",
      where_template:
        `WHERE ${c.fields[0]} = @key_value  -- exploit clustering on \`${c.fields[0]}\``,
    };
  }
  return { kind: "none", delta_strategy: "full_replace" };
}

async function main() {
  const pool = await getRwPool();

  const reviewClause = REVIEW === "all"
    ? "1=1"
    : `c.review_status = $${2}`;
  const params = [PROVIDER];
  if (REVIEW !== "all") params.push(REVIEW);

  const sql = `
    SELECT t.dataset_id, t.bq_project, t.bq_dataset, t.bq_table,
           t.row_count_estimate, t.size_bytes_estimate,
           t.partitioning_json, t.clustering_json,
           c.license, c.recommended_ingest_mode, c.review_status
    FROM vertex_public_dataset_table t
    JOIN vertex_public_dataset_catalog c
      ON c.dataset_id = t.dataset_id
    WHERE c.provider = $1 AND ${reviewClause}
    ORDER BY t.dataset_id, t.size_bytes_estimate DESC NULLS LAST
  `;
  const { rows } = await pool.query(sql, params);

  const records = rows.map((r) => {
    const cls = classifyPartition(r.partitioning_json, r.clustering_json);
    return {
      dataset_id: r.dataset_id,
      bq_dataset: r.bq_dataset,
      bq_table: r.bq_table,
      review_status: r.review_status,
      license: r.license,
      ingest_mode: r.recommended_ingest_mode,
      size_gib: r.size_bytes_estimate
        ? Number((Number(r.size_bytes_estimate) / 1024 / 1024 / 1024).toFixed(2))
        : null,
      row_count: r.row_count_estimate ? Number(r.row_count_estimate) : null,
      kind: cls.kind,
      delta_strategy: cls.delta_strategy,
      partition_field: cls.partition_field ?? null,
      partition_type: cls.partition_type ?? null,
      partition_range: cls.partition_range ?? null,
      cluster_fields: cls.cluster_fields ?? null,
      where_template: cls.where_template ?? null,
    };
  });

  const summary = {
    by_kind: groupCount(records, "kind"),
    by_delta_strategy: groupCount(records, "delta_strategy"),
    by_dataset: tableCountByDataset(records),
  };

  const md = renderMarkdown({ provider: PROVIDER, review: REVIEW, records, summary });
  if (OUT) {
    await mkdir(dirname(OUT), { recursive: true });
    await writeFile(OUT, md, "utf8");
    console.log(`[bq-partitioning] wrote ${OUT}`);
  } else {
    process.stdout.write(md);
  }
  if (CSV) {
    await mkdir(dirname(CSV), { recursive: true });
    const header = [
      "dataset_id","bq_table","review_status","license","ingest_mode",
      "size_gib","row_count","kind","delta_strategy","partition_field",
      "partition_type","cluster_fields","where_template",
    ].join(",");
    const lines = records.map((r) => [
      r.dataset_id, r.bq_table, r.review_status, r.license, r.ingest_mode,
      r.size_gib ?? "", r.row_count ?? "", r.kind, r.delta_strategy,
      r.partition_field ?? "", r.partition_type ?? "",
      (r.cluster_fields ?? []).join("|"),
      JSON.stringify(r.where_template ?? "").replace(/\n/g, " "),
    ].map(csvCell).join(","));
    await writeFile(CSV, [header, ...lines].join("\n") + "\n", "utf8");
    console.log(`[bq-partitioning] wrote ${CSV}`);
  }
  console.log(`[bq-partitioning] tables=${records.length}`
    + ` by_kind=${JSON.stringify(summary.by_kind)}`);
  console.log(`[bq-partitioning] by_delta_strategy=${JSON.stringify(summary.by_delta_strategy)}`);

  await pool.end();
}

function csvCell(v) {
  const s = String(v ?? "");
  if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function groupCount(rows, key) {
  const out = {};
  for (const r of rows) {
    const v = r[key] ?? "(null)";
    out[v] = (out[v] ?? 0) + 1;
  }
  return out;
}

function tableCountByDataset(rows) {
  const out = {};
  for (const r of rows) {
    out[r.dataset_id] = (out[r.dataset_id] ?? 0) + 1;
  }
  return out;
}

function renderMarkdown({ provider, review, records, summary }) {
  const lines = [];
  lines.push(`# Partitioning review — ${provider} (review_status=${review})`);
  lines.push("");
  lines.push(`Generated ${new Date().toISOString()} by`
    + ` \`70-tools/scripts/bigquery-public-dataset-partitioning-review.mjs\`.`);
  lines.push("");
  lines.push(`## Summary`);
  lines.push("");
  lines.push(`- tables: ${records.length}`);
  lines.push(`- by_kind: ${JSON.stringify(summary.by_kind)}`);
  lines.push(`- by_delta_strategy: ${JSON.stringify(summary.by_delta_strategy)}`);
  lines.push("");
  lines.push(`## Per-table delta strategy recommendations`);
  lines.push("");
  lines.push(`| dataset | table | size_gib | kind | delta_strategy | partition / cluster |`);
  lines.push(`|---|---|---:|---|---|---|`);
  for (const r of records) {
    const ext = r.partition_field
      ? `partition: ${r.partition_field}` + (r.partition_type ? ` (${r.partition_type})` : "")
      : (r.cluster_fields ? `cluster: ${r.cluster_fields.join(", ")}` : "—");
    lines.push(`| ${r.bq_dataset} | ${r.bq_table} | ${r.size_gib ?? "?"} | ${r.kind} | ${r.delta_strategy} | ${ext} |`);
  }
  lines.push("");
  lines.push(`## WHERE-clause templates by kind`);
  lines.push("");
  const seenKind = new Set();
  for (const r of records) {
    if (seenKind.has(r.kind) || !r.where_template) continue;
    seenKind.add(r.kind);
    lines.push(`### ${r.kind}`);
    lines.push("```sql");
    lines.push(r.where_template);
    lines.push("```");
    lines.push("");
  }
  return lines.join("\n");
}

main().catch(async (e) => {
  console.error(`[bq-partitioning] FATAL: ${e.stack ?? e.message ?? e}`);
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});
