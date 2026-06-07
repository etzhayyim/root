#!/usr/bin/env node
import { createRequire } from "node:module";
import fs from "node:fs";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;
const ALLOWLIST = new Set(["app.bsky.feed.post"]);

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/audit/repo-record-allowlist.mjs [--json] [--strict] [--limit 50] [--sample-rows 10000] [--with-counts] [--out report.json]

Audits legacy rows in vertex_repo_record by collection.

Policy:
  - app.bsky.feed.post is allowed in vertex_repo_record.
  - all other collections are legacy/grandfathered audit findings.
  - default exit is 0 after reporting; --strict exits 2 when findings exist.

Default mode samples non-post rows to avoid expensive full-table group-by on
large RisingWave deployments. Use --with-counts for exact collection counts.
`);
  process.exit(code);
}

const opts = {
  json: false,
  strict: false,
  limit: 50,
  sampleRows: 10_000,
  withCounts: false,
  out: "",
};

for (let i = 2; i < process.argv.length; i += 1) {
  const arg = process.argv[i];
  const next = process.argv[i + 1];
  if (arg === "--json") opts.json = true;
  else if (arg === "--strict") opts.strict = true;
  else if (arg === "--limit" && next) {
    opts.limit = Math.max(1, Number.parseInt(next, 10) || opts.limit);
    i += 1;
  } else if (arg === "--sample-rows" && next) {
    opts.sampleRows = Math.max(1, Number.parseInt(next, 10) || opts.sampleRows);
    i += 1;
  } else if (arg === "--with-counts") {
    opts.withCounts = true;
  } else if (arg === "--out" && next) {
    opts.out = next;
    i += 1;
  } else if (arg === "-h" || arg === "--help") usage(0);
  else throw new Error(`Unknown argument: ${arg}`);
}

if (!DATABASE_URL) {
  console.error("Set DATABASE_URL, KOTOBA_URL, or KOTOBA_URL.");
  process.exit(1);
}

const pool = new pg.Pool({
  connectionString: DATABASE_URL,
  max: 2,
  statement_timeout: 60_000,
});

async function q(text, params = []) {
  const result = await pool.query(text, params);
  return result.rows;
}

function toCount(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? n : 0;
}

function printTable(title, rows, columns) {
  console.log(`\n${title}`);
  if (rows.length === 0) {
    console.log("  (none)");
    return;
  }
  const widths = columns.map((column) => Math.max(column.length, ...rows.map((row) => String(row[column] ?? "").length)));
  console.log(columns.map((column, i) => column.padEnd(widths[i])).join("  "));
  console.log(columns.map((_, i) => "-".repeat(widths[i])).join("  "));
  for (const row of rows) {
    console.log(columns.map((column, i) => String(row[column] ?? "").padEnd(widths[i])).join("  "));
  }
}

try {
  const evaluatedAt = new Date().toISOString();
  const sampleRowsLimit = Math.max(1, Number.parseInt(String(opts.sampleRows), 10) || 10_000);
  const rows = opts.withCounts
    ? await q(
      `SELECT
          collection,
          COUNT(*)::bigint AS row_count,
          COUNT(DISTINCT repo)::bigint AS repo_count,
          MIN(created_at) AS first_created_at,
          MAX(created_at) AS last_created_at,
          MIN(uri) AS sample_uri
         FROM vertex_repo_record
        GROUP BY collection
        ORDER BY COUNT(*) DESC, collection ASC`,
    )
    : await q(
      `SELECT
          collection,
          COUNT(*)::bigint AS sampled_row_count,
          COUNT(DISTINCT repo)::bigint AS sampled_repo_count,
          MIN(created_at) AS first_sample_created_at,
          MAX(created_at) AS last_sample_created_at,
          MIN(uri) AS sample_uri
         FROM (
           SELECT collection, repo, created_at, uri
             FROM vertex_repo_record
            WHERE collection <> $1
            LIMIT ${sampleRowsLimit}
         ) sampled
        GROUP BY collection
        ORDER BY COUNT(*) DESC, collection ASC`,
      [Array.from(ALLOWLIST)[0]],
    );

  const collections = rows.map((row) => {
    const collection = String(row.collection ?? "");
    const allowed = ALLOWLIST.has(collection);
    return {
      collection,
      allowed,
      status: allowed ? "allowed" : "legacy_grandfathered",
      row_count: opts.withCounts ? toCount(row.row_count) : null,
      repo_count: opts.withCounts ? toCount(row.repo_count) : null,
      sampled_row_count: opts.withCounts ? null : toCount(row.sampled_row_count),
      sampled_repo_count: opts.withCounts ? null : toCount(row.sampled_repo_count),
      first_created_at: row.first_created_at ?? row.first_sample_created_at ?? null,
      last_created_at: row.last_created_at ?? row.last_sample_created_at ?? null,
      sample_uri: row.sample_uri ?? null,
    };
  });

  const findings = collections.filter((row) => !row.allowed);
  const topFindings = findings.slice(0, opts.limit);
  const totalRows = opts.withCounts ? collections.reduce((sum, row) => sum + row.row_count, 0) : null;
  const allowedRows = opts.withCounts ? collections.filter((row) => row.allowed).reduce((sum, row) => sum + row.row_count, 0) : null;
  const findingRows = opts.withCounts ? findings.reduce((sum, row) => sum + row.row_count, 0) : null;
  const sampledFindingRows = opts.withCounts ? null : findings.reduce((sum, row) => sum + row.sampled_row_count, 0);

  const report = {
    evaluated_at: evaluatedAt,
    table: "vertex_repo_record",
    mode: opts.withCounts ? "exact_counts" : "sample",
    allowlist: Array.from(ALLOWLIST).sort(),
    summary: {
      collections: collections.length,
      allowed_collections: collections.length - findings.length,
      finding_collections: findings.length,
      sample_rows: opts.withCounts ? null : opts.sampleRows,
      total_rows: totalRows,
      allowed_rows: allowedRows,
      finding_rows: findingRows,
      sampled_finding_rows: sampledFindingRows,
    },
    findings: topFindings,
    collections,
  };

  if (opts.out) fs.writeFileSync(opts.out, `${JSON.stringify(report, null, 2)}\n`);

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`repo-record-allowlist audit @ ${evaluatedAt}`);
    console.log(`table: vertex_repo_record`);
    console.log(`mode: ${report.mode}`);
    console.log(`allowlist: ${report.allowlist.join(", ")}`);
    if (opts.withCounts) {
      console.log(`collections=${report.summary.collections} findings=${report.summary.finding_collections} total_rows=${totalRows} finding_rows=${findingRows}`);
    } else {
      console.log(`collections=${report.summary.collections} findings=${report.summary.finding_collections} sampled_rows_limit=${opts.sampleRows} sampled_finding_rows=${sampledFindingRows}`);
    }
    printTable("Top legacy/grandfathered findings", topFindings, [
      "collection",
      "row_count",
      "repo_count",
      "sampled_row_count",
      "sampled_repo_count",
      "first_created_at",
      "last_created_at",
      "sample_uri",
    ]);
    if (findings.length > topFindings.length) {
      console.log(`\n...and ${findings.length - topFindings.length} more collection(s). Re-run with --limit ${findings.length} or --json.`);
    }
    if (opts.out) console.log(`\nwrote ${opts.out}`);
  }

  await pool.end();
  if (opts.strict && findings.length > 0) process.exit(2);
} catch (error) {
  await pool.end().catch(() => {});
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
