#!/usr/bin/env node
import { createRequire } from "node:module";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/natural-person-repair-cohort-hashes.mjs [--apply] [--json]

Dry-run is the default. Recomputes vertex_natural_person_cohort_person.cohort_hash
from the same 26 canonical cohort dimensions used by the natural-person app.
`);
  process.exit(code);
}

const opts = {
  apply: false,
  json: false,
};

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

const cohortColumns = [
  "country", "region", "municipality", "age", "gender",
  "income_decile", "education_isced", "occupation_isco", "employment_status",
  "marital_status", "household_size", "housing_tenure", "urban_rural",
  "health_icd10", "disability_type", "migration_status",
  "ethnicity", "religion", "language_primary",
  "entity_did", "community_id",
  "vital_status", "birth_year", "death_year",
  "death_cause_icd10", "era",
];

function canonical(row) {
  return cohortColumns.map((column) => String(row[column] ?? "")).join("|");
}

function cohortHashV1(input) {
  let h = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  const mask = 0xffffffffffffffffn;
  for (let i = 0; i < input.length; i++) {
    h ^= BigInt(input.charCodeAt(i));
    h = (h * prime) & mask;
  }
  return `npch1_${h.toString(16).padStart(16, "0")}`;
}

const pool = new pg.Pool({
  connectionString: DATABASE_URL,
  max: 2,
  statement_timeout: 120_000,
});

async function countCollisions() {
  const result = await pool.query(`
    SELECT COUNT(*)::bigint AS collision_groups
      FROM (
        SELECT cohort_hash
          FROM vertex_natural_person_cohort_person
         WHERE cohort_hash IS NOT NULL AND cohort_hash <> ''
         GROUP BY cohort_hash
        HAVING COUNT(*) > 1
      ) x
  `);
  return Number(result.rows[0]?.collision_groups ?? 0);
}

async function main() {
  const beforeCollisionGroups = await countCollisions();
  const result = await pool.query(`
    SELECT vertex_id, cohort_hash, ${cohortColumns.join(", ")}
      FROM vertex_natural_person_cohort_person
     ORDER BY vertex_id
  `);

  const changes = result.rows
    .map((row) => ({
      vertexId: row.vertex_id,
      oldHash: row.cohort_hash,
      newHash: cohortHashV1(canonical(row)),
    }))
    .filter((row) => row.oldHash !== row.newHash);

  let updated = 0;
  if (opts.apply) {
    for (const change of changes) {
      const update = await pool.query(
        "UPDATE vertex_natural_person_cohort_person SET cohort_hash = $1 WHERE vertex_id = $2",
        [change.newHash, change.vertexId],
      );
      updated += update.rowCount ?? 0;
    }
    await pool.query("FLUSH");
  }

  const afterCollisionGroups = await countCollisions();
  const report = {
    evaluatedAt: new Date().toISOString(),
    apply: opts.apply,
    totalRows: result.rows.length,
    plannedUpdates: changes.length,
    updated,
    beforeCollisionGroups,
    afterCollisionGroups,
    sampleChanges: changes.slice(0, 10),
  };

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`evaluatedAt: ${report.evaluatedAt}`);
    console.log(`apply: ${report.apply}`);
    console.log(`totalRows: ${report.totalRows}`);
    console.log(`plannedUpdates: ${report.plannedUpdates}`);
    console.log(`updated: ${report.updated}`);
    console.log(`beforeCollisionGroups: ${report.beforeCollisionGroups}`);
    console.log(`afterCollisionGroups: ${report.afterCollisionGroups}`);
  }
}

try {
  await main();
} finally {
  await pool.end();
}
