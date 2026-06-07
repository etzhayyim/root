#!/usr/bin/env node
/**
 * Recruit real job ingest runner.
 *
 * Wraps the public ATS ingest with operational checks:
 *   - dry-run can verify live public APIs without a database
 *   - real runs require RisingWave/Postgres connectivity
 *   - migrations run before insert unless --skip-migrate is set
 *   - post-run counts are written to /tmp for monitoring/debugging
 */
import { readFile, writeFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { createRequire } from "node:module";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const args = process.argv.slice(2);
const hasFlag = (key) => args.includes(`--${key}`);
const getArg = (key, fallback) => {
  const index = args.lastIndexOf(`--${key}`);
  return index === -1 ? fallback : args[index + 1] ?? fallback;
};

const platform = getArg("platform", "lever");
const limit = getArg("limit", "100");
const batchSize = getArg("batch-size", getArg("batchSize", "50"));
const dryRun = hasFlag("dry-run");
const skipMigrate = hasFlag("skip-migrate");
const allowUnanchored = hasFlag("allow-unanchored") || hasFlag("allowUnanchored");
const ignoreCheckpoint = hasFlag("ignore-checkpoint") || hasFlag("ignoreCheckpoint");
const startedAt = new Date().toISOString();
const runId = `recruit-job-ingest:${platform}:${startedAt}`;
const graphRequire = createRequire(new URL("../../30-graph/graph-schema/package.json", import.meta.url));

function run(command, commandArgs, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, commandArgs, { stdio: "inherit", ...options });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${commandArgs.join(" ")} exited with ${code}`));
    });
  });
}

async function pgClient() {
  const pg = graphRequire("pg");
  const client = new pg.Client({ connectionString: KOTOBA_URL, statement_timeout: 30_000 });
  await client.connect();
  return client;
}

async function assertDbReady() {
  const client = await pgClient();
  try {
    await client.query("SELECT 1");
  } finally {
    await client.end();
  }
}

async function readSummary() {
  try {
    return JSON.parse(await readFile("/tmp/ats-direct-summary.json", "utf8"));
  } catch {
    return {};
  }
}

async function queryCounts() {
  const client = await pgClient();
  try {
    const { rows } = await client.query(`
      SELECT source, count(*)::bigint AS count, max(ingested_at) AS latest_ingested_at
      FROM vertex_job_posting
      WHERE source IN ('greenhouse', 'lever', 'ashby')
      GROUP BY source
      ORDER BY source
    `);
    return rows;
  } finally {
    await client.end();
  }
}

async function persistRun(report) {
  if (dryRun) return;
  const client = await pgClient();
  const vertexId = `at://did:web:recruit.etzhayyim.com/com.etzhayyim.apps.recruit.jobIngestRun/${runId.replace(/[^a-zA-Z0-9._:-]/g, "_")}`;
  const createdDate = startedAt.slice(0, 10);
  try {
    await client.query(
      `
      INSERT INTO vertex_recruit_job_ingest_run (
        vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo,
        run_id, platform, status, fetched, inserted, skipped, limit_count,
        batch_size, started_at, finished_at, duration_ms, error, props
      )
      VALUES (
        $1, $17, 1, $2, $3, $2,
        $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16
      )
      `,
      [
        vertexId,
        "did:web:recruit.etzhayyim.com",
        runId,
        runId,
        platform,
        report.status,
        report.fetched ?? 0,
        report.inserted ?? report.total ?? 0,
        report.skipped ?? 0,
        Number(limit),
        Number(batchSize),
        startedAt,
        report.finishedAt,
        report.durationMs,
        report.error ?? null,
        JSON.stringify(report),
        createdDate,
      ],
    );
  } finally {
    await client.end();
  }
}

async function main() {
  console.log(`[recruit] ingest platform=${platform} limit=${limit} batchSize=${batchSize} dryRun=${dryRun}`);

  if (!dryRun) {
    await assertDbReady();
    if (!skipMigrate) {
      await run("pnpm", ["--filter", "@etzhayyim/graph-schema", "run", "db:migrate"], {
        env: { ...process.env, DATABASE_URL: process.env.DATABASE_URL ?? KOTOBA_URL },
      });
    }
  }

  await run("node", [
    "70-tools/scripts/recruit-ingest-ats-direct.mjs",
    "--platform", platform,
    "--limit", limit,
    "--batch-size", batchSize,
    ...(dryRun ? ["--dry-run"] : []),
    ...(allowUnanchored ? ["--allow-unanchored"] : []),
    ...(ignoreCheckpoint ? ["--ignore-checkpoint"] : []),
  ]);

  const summary = await readSummary();
  const counts = dryRun ? [] : await queryCounts();
  const finishedAt = new Date().toISOString();
  const report = {
    ...summary,
    runId,
    platform,
    status: "succeeded",
    limit: Number(limit),
    batchSize: Number(batchSize),
    dryRun,
    allowUnanchored,
    ignoreCheckpoint,
    counts,
    startedAt,
    finishedAt,
    durationMs: Date.parse(finishedAt) - Date.parse(startedAt),
    generatedAt: finishedAt,
  };
  await persistRun(report);
  await writeFile("/tmp/recruit-real-job-ingest-run.json", JSON.stringify(report, null, 2));
  console.log(`[recruit] report=/tmp/recruit-real-job-ingest-run.json inserted=${report.inserted ?? report.total ?? 0}`);
}

main().catch(async (error) => {
  console.error(`[recruit] ingest failed: ${error.message}`);
  const finishedAt = new Date().toISOString();
  const report = {
    runId,
    platform,
    status: "failed",
    fetched: 0,
    inserted: 0,
    skipped: 0,
    limit: Number(limit),
    batchSize: Number(batchSize),
    dryRun,
    allowUnanchored,
    ignoreCheckpoint,
    counts: [],
    startedAt,
    finishedAt,
    durationMs: Date.parse(finishedAt) - Date.parse(startedAt),
    error: error.message,
    generatedAt: finishedAt,
  };
  try {
    await persistRun(report);
    await writeFile("/tmp/recruit-real-job-ingest-run.json", JSON.stringify(report, null, 2));
  } catch (persistError) {
    console.error(`[recruit] failed to persist run report: ${persistError.message}`);
  }
  process.exit(1);
});
