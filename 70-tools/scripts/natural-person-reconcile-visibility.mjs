#!/usr/bin/env node
import { createRequire } from "node:module";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/natural-person-reconcile-visibility.mjs [--apply-openalex-public] [--json]

Dry-run is the default. --apply-openalex-public only updates OpenAlex rows that
are data_classification='open' and sensitivity_ord IS NULL.
`);
  process.exit(code);
}

const opts = {
  applyOpenalexPublic: false,
  json: false,
};

for (const arg of process.argv.slice(2)) {
  if (arg === "--apply-openalex-public") opts.applyOpenalexPublic = true;
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

async function one(text, params = []) {
  const result = await pool.query(text, params);
  return result.rows[0] ?? {};
}

async function many(text, params = []) {
  const result = await pool.query(text, params);
  return result.rows;
}

async function main() {
  const evaluatedAt = new Date().toISOString();
  const plan = await one(`
    SELECT
      (SELECT COUNT(*)::bigint
         FROM vertex_natural_person
        WHERE sensitivity_ord IS NULL
          AND data_classification = 'open'
          AND source_app = 'openalex') AS planned_openalex_public,
      (SELECT COUNT(*)::bigint
         FROM vertex_business_person
        WHERE sensitivity_ord IS NULL) AS business_unclassified,
      (SELECT COUNT(*)::bigint
         FROM (
           SELECT cohort_hash
             FROM vertex_natural_person_cohort_person
            WHERE cohort_hash IS NOT NULL AND cohort_hash <> ''
            GROUP BY cohort_hash
           HAVING COUNT(*) > 1
         ) x) AS cohort_hash_collision_groups
  `);

  const before = await many(`
    SELECT source_app, data_classification, sensitivity_ord, COUNT(*)::bigint AS count
      FROM vertex_natural_person
     GROUP BY source_app, data_classification, sensitivity_ord
     ORDER BY count DESC
     LIMIT 20
  `);

  let updatedOpenalexPublic = 0;
  if (opts.applyOpenalexPublic) {
    const result = await pool.query(`
      UPDATE vertex_natural_person
         SET sensitivity_ord = 0
       WHERE sensitivity_ord IS NULL
         AND data_classification = 'open'
         AND source_app = 'openalex'
    `);
    updatedOpenalexPublic = result.rowCount ?? 0;
    await pool.query("FLUSH");
  }

  const report = {
    evaluatedAt,
    applyOpenalexPublic: opts.applyOpenalexPublic,
    plannedOpenalexPublic: Number(plan.planned_openalex_public ?? 0),
    updatedOpenalexPublic,
    businessUnclassified: Number(plan.business_unclassified ?? 0),
    cohortHashCollisionGroups: Number(plan.cohort_hash_collision_groups ?? 0),
    naturalPersonSourceBreakdown: before,
  };

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`evaluatedAt: ${report.evaluatedAt}`);
    console.log(`applyOpenalexPublic: ${report.applyOpenalexPublic}`);
    console.log(`plannedOpenalexPublic: ${report.plannedOpenalexPublic}`);
    console.log(`updatedOpenalexPublic: ${report.updatedOpenalexPublic}`);
    console.log(`businessUnclassified: ${report.businessUnclassified}`);
    console.log(`cohortHashCollisionGroups: ${report.cohortHashCollisionGroups}`);
  }
}

try {
  await main();
} finally {
  await pool.end();
}
