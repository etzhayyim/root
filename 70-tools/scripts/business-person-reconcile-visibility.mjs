#!/usr/bin/env node
import { createRequire } from "node:module";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/business-person-reconcile-visibility.mjs [--apply] [--json]

Dry-run is the default. Public corporate/news/profile sources become
sensitivity_ord=0. Potentially sensitive corporate/internal/security sources
become sensitivity_ord=2.
`);
  process.exit(code);
}

const opts = { apply: false, json: false };
for (const arg of process.argv.slice(2)) {
  if (arg === "--apply") opts.apply = true;
  else if (arg === "--json") opts.json = true;
  else if (arg === "-h" || arg === "--help") usage(0);
  else throw new Error(`Unknown argument: ${arg}`);
}

if (!DATABASE_URL) {
  console.error("Set DATABASE_URL, KOTOBA_URL, or KOTOBA_URL.");
  process.exit(1);
}

const pool = new pg.Pool({
  connectionString: DATABASE_URL,
  max: 2,
  statement_timeout: 120_000,
});

async function flushBestEffort() {
  try {
    await pool.query("FLUSH");
    return null;
  } catch (error) {
    return String(error?.message ?? error);
  }
}

async function queryWithRecoveryRetry(text, params = []) {
  const maxAttempts = 6;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await pool.query(text, params);
    } catch (error) {
      const message = String(error?.message ?? error);
      const recoverable = message.includes("cluster recovery") || message.includes("failed to recover");
      if (!recoverable || attempt === maxAttempts) throw error;
      await new Promise((resolve) => setTimeout(resolve, attempt * 10_000));
    }
  }
  throw new Error("unreachable retry state");
}

const sensitiveTerms = [
  "internal communication",
  "engineering roadmap",
  "strategic planning",
  "security report",
  "security incident",
  "technical documentation",
  "compliance document",
  "data privacy policy",
];

const publicTerms = [
  "linkedin",
  "press release",
  "blog",
  "official website",
  "website",
  "investor relations",
  "annual report",
  "earnings report",
  "reuters",
  "tech news",
  "industry publication",
  "industry report",
  "qualys inc. report",
  "security forum",
  "news",
];

function likeAnySql(alias, terms, offset) {
  const expr = terms.map((_, i) => `LOWER(${alias}) LIKE $${offset + i}`).join(" OR ");
  return `(${expr})`;
}

function likeParams(terms) {
  return terms.map((term) => `%${term}%`);
}

async function countPlan() {
  const sensitiveSql = likeAnySql("source", sensitiveTerms, 1);
  const publicSql = likeAnySql("source", publicTerms, sensitiveTerms.length + 1);
  const params = [...likeParams(sensitiveTerms), ...likeParams(publicTerms)];
  const result = await pool.query(
    `
      SELECT
        COUNT(*) FILTER (
          WHERE sensitivity_ord IS NULL
            AND ${sensitiveSql}
        )::bigint AS planned_confidential,
        COUNT(*) FILTER (
          WHERE sensitivity_ord IS NULL
            AND NOT ${sensitiveSql}
            AND ${publicSql}
        )::bigint AS planned_public,
        COUNT(*) FILTER (
          WHERE sensitivity_ord IS NULL
            AND NOT ${sensitiveSql}
            AND NOT ${publicSql}
        )::bigint AS planned_remaining
        FROM vertex_business_person
    `,
    params,
  );
  return result.rows[0] ?? {};
}

async function breakdown() {
  const result = await pool.query(`
    SELECT source, country, sensitivity_ord, COUNT(*)::bigint AS count
      FROM vertex_business_person
     GROUP BY source, country, sensitivity_ord
     ORDER BY sensitivity_ord NULLS FIRST, count DESC, source NULLS FIRST, country NULLS FIRST
  `);
  return result.rows;
}

async function main() {
  const before = await countPlan();
  let updatedConfidential = 0;
  let updatedPublic = 0;
  let flushWarning = null;

  if (opts.apply) {
    const sensitiveSql = likeAnySql("source", sensitiveTerms, 1);
    const conf = await queryWithRecoveryRetry(
      `UPDATE vertex_business_person SET sensitivity_ord = 2 WHERE sensitivity_ord IS NULL AND ${sensitiveSql}`,
      likeParams(sensitiveTerms),
    );
    updatedConfidential = conf.rowCount ?? 0;

    const publicSql = likeAnySql("source", publicTerms, 1);
    const pub = await queryWithRecoveryRetry(
      `UPDATE vertex_business_person SET sensitivity_ord = 0 WHERE sensitivity_ord IS NULL AND ${publicSql}`,
      likeParams(publicTerms),
    );
    updatedPublic = pub.rowCount ?? 0;
    flushWarning = await flushBestEffort();
  }

  const after = await countPlan();
  const report = {
    evaluatedAt: new Date().toISOString(),
    apply: opts.apply,
    plannedPublic: Number(before.planned_public ?? 0),
    plannedConfidential: Number(before.planned_confidential ?? 0),
    plannedRemaining: Number(before.planned_remaining ?? 0),
    updatedPublic,
    updatedConfidential,
    flushWarning,
    afterRemaining: Number(after.planned_remaining ?? 0),
    breakdown: opts.json ? await breakdown() : undefined,
  };

  if (opts.json) console.log(JSON.stringify(report, null, 2));
  else {
    console.log(`evaluatedAt: ${report.evaluatedAt}`);
    console.log(`apply: ${report.apply}`);
    console.log(`plannedPublic: ${report.plannedPublic}`);
    console.log(`plannedConfidential: ${report.plannedConfidential}`);
    console.log(`plannedRemaining: ${report.plannedRemaining}`);
    console.log(`updatedPublic: ${report.updatedPublic}`);
    console.log(`updatedConfidential: ${report.updatedConfidential}`);
    console.log(`afterRemaining: ${report.afterRemaining}`);
  }
}

try {
  await main();
} finally {
  await pool.end();
}
