#!/usr/bin/env node
import { createRequire } from "node:module";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/natural-person-latent-entity-audit.mjs [--json]

Audits natural-person/business-person public-hidden classification, cohort paths,
and latent entity backend activation state.
`);
  process.exit(code);
}

const opts = {
  json: false,
};

for (const arg of process.argv.slice(2)) {
  if (arg === "--json") opts.json = true;
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
  statement_timeout: 60_000,
});

async function q(text, params = []) {
  const result = await pool.query(text, params);
  return result.rows;
}

async function scalar(text, params = []) {
  const rows = await q(text, params);
  return Number(rows[0]?.value ?? 0);
}

async function relationExists(name) {
  const rows = await q(
    `SELECT 1
       FROM information_schema.tables
      WHERE table_schema = 'public'
        AND table_name = $1
      LIMIT 1`,
    [name],
  );
  return rows.length > 0;
}

async function countIfExists(name) {
  if (!(await relationExists(name))) return null;
  return scalar(`SELECT COUNT(*)::bigint AS value FROM ${name}`);
}

function visibilityClass(row) {
  const ord = row.sensitivity_ord === null || row.sensitivity_ord === undefined ? null : Number(row.sensitivity_ord);
  if (ord === null || Number.isNaN(ord)) return "unclassified";
  if (ord === 0) return "public_searchable";
  if (ord === 1) return "internal_aggregate";
  if (ord === 2) return "confidential";
  if (ord === 3) return "restricted_individual";
  if (ord >= 100) return "non_federating_pii";
  return "unknown";
}

function printTable(title, rows, columns) {
  console.log(`\n${title}`);
  if (rows.length === 0) {
    console.log("  (none)");
    return;
  }
  const widths = columns.map((c) => Math.max(c.length, ...rows.map((r) => String(r[c] ?? "").length)));
  console.log(columns.map((c, i) => c.padEnd(widths[i])).join("  "));
  console.log(columns.map((_, i) => "-".repeat(widths[i])).join("  "));
  for (const row of rows) {
    console.log(columns.map((c, i) => String(row[c] ?? "").padEnd(widths[i])).join("  "));
  }
}

try {
  const evaluatedAt = new Date().toISOString();

  const [
    businessSensitivity,
    naturalSensitivity,
    cohortSensitivity,
    identifiedSensitivity,
    naturalSources,
    businessSources,
    cohortSamples,
    latentCounts,
    bpmnBindings,
    activityEvents,
    ocelEvents,
  ] = await Promise.all([
    q(`SELECT sensitivity_ord, status, COUNT(*)::bigint AS count
         FROM vertex_business_person
        GROUP BY sensitivity_ord, status
        ORDER BY sensitivity_ord NULLS FIRST, status NULLS FIRST`),
    q(`SELECT sensitivity_ord, data_classification, COUNT(*)::bigint AS count
         FROM vertex_natural_person
        GROUP BY sensitivity_ord, data_classification
        ORDER BY sensitivity_ord NULLS FIRST, data_classification NULLS FIRST`),
    q(`SELECT sensitivity_ord, data_classification, vital_status, era, COUNT(*)::bigint AS count,
              COALESCE(SUM(COALESCE(intel_estimated_count, 0)), 0)::bigint AS estimated_count
         FROM vertex_natural_person_cohort_person
        GROUP BY sensitivity_ord, data_classification, vital_status, era
        ORDER BY sensitivity_ord NULLS FIRST, data_classification NULLS FIRST, vital_status NULLS FIRST, era NULLS FIRST`),
    q(`SELECT sensitivity_ord, COUNT(*)::bigint AS count
         FROM vertex_natural_person_identified_person
        GROUP BY sensitivity_ord
        ORDER BY sensitivity_ord NULLS FIRST`),
    q(`SELECT source_app, data_classification, sensitivity_ord, COUNT(*)::bigint AS count
         FROM vertex_natural_person
        GROUP BY source_app, data_classification, sensitivity_ord
        ORDER BY count DESC
        LIMIT 20`),
    q(`SELECT source, country, sensitivity_ord, COUNT(*)::bigint AS count
         FROM vertex_business_person
        GROUP BY source, country, sensitivity_ord
        ORDER BY count DESC
        LIMIT 20`),
    q(`SELECT cohort_hash, COUNT(*)::bigint AS count,
              MIN(cohort_did) AS sample_cohort_did,
              MIN(vertex_id) AS sample_vertex_id
         FROM vertex_natural_person_cohort_person
        WHERE cohort_hash IS NOT NULL AND cohort_hash <> ''
        GROUP BY cohort_hash
        HAVING COUNT(*) > 1
        ORDER BY count DESC, cohort_hash
        LIMIT 20`),
    Promise.all([
      "vertex_lda_viewpoint",
      "vertex_lda_signal",
      "vertex_lda_model",
      "vertex_lda_topic",
      "vertex_latent_entity",
      "vertex_natural_person_latent_materialization_cursor",
      "edge_entity_cohort_link",
      "edge_entity_evidence",
    ].map(async (name) => ({ relation: name, count: await countIfExists(name) }))),
    q(`SELECT nsid, bpmn_process_id, status, sensitivity_ord
         FROM vertex_bpmn_lexicon_binding
        WHERE nsid IN (
          'com.etzhayyim.apps.naturalPerson.generateCohortBatch',
          'com.etzhayyim.apps.coverage.inferCensusStats',
          'com.etzhayyim.apps.coverage.inferLdaSignals',
          'com.etzhayyim.apps.coverage.inferLdaTopics',
          'com.etzhayyim.apps.coverage.inferLdaEntities',
          'com.etzhayyim.apps.coverage.inferFission',
          'com.etzhayyim.apps.naturalPerson.reconcileVisibility',
          'com.etzhayyim.apps.naturalPerson.seedLatentEntities',
          'com.etzhayyim.apps.naturalPerson.materializeAllLatentEntities'
        )
        ORDER BY nsid`),
    q(`SELECT COUNT(*)::bigint AS count
         FROM vertex_bpmn_activity_event
        WHERE event_type ILIKE '%infer%'
           OR event_type ILIKE '%naturalPerson%'
           OR event_type ILIKE '%cohort%'
           OR activity_id ILIKE '%infer%'
           OR activity_id ILIKE '%cohort%'`),
    q(`SELECT COUNT(*)::bigint AS count
         FROM vertex_ocel_event
        WHERE activity ILIKE '%infer%'
           OR activity ILIKE '%naturalPerson%'
           OR activity ILIKE '%cohort%'`),
  ]);

  const businessByVisibility = new Map();
  for (const row of businessSensitivity) {
    const key = visibilityClass(row);
    businessByVisibility.set(key, (businessByVisibility.get(key) ?? 0) + Number(row.count));
  }
  const naturalByVisibility = new Map();
  for (const row of naturalSensitivity) {
    const key = visibilityClass(row);
    naturalByVisibility.set(key, (naturalByVisibility.get(key) ?? 0) + Number(row.count));
  }
  for (const row of cohortSensitivity) {
    const key = visibilityClass(row);
    naturalByVisibility.set(key, (naturalByVisibility.get(key) ?? 0) + Number(row.count));
  }
  for (const row of identifiedSensitivity) {
    const key = visibilityClass(row);
    naturalByVisibility.set(key, (naturalByVisibility.get(key) ?? 0) + Number(row.count));
  }

  const report = {
    evaluatedAt,
    visibility: {
      businessPerson: Object.fromEntries([...businessByVisibility.entries()].sort()),
      naturalPerson: Object.fromEntries([...naturalByVisibility.entries()].sort()),
    },
    raw: {
      businessSensitivity,
      naturalSensitivity,
      cohortSensitivity,
      identifiedSensitivity,
      naturalSources,
      businessSources,
    },
    cohortHashCollisions: cohortSamples,
    latentBackend: {
      relationCounts: latentCounts,
      bpmnBindings,
      bpmnActivityEventMatches: Number(activityEvents[0]?.count ?? 0),
      ocelEventMatches: Number(ocelEvents[0]?.count ?? 0),
    },
  };

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`Natural Person Latent Entity Audit`);
    console.log(`EvaluatedAt: ${evaluatedAt}`);
    printTable("Business Person Visibility", Object.entries(report.visibility.businessPerson).map(([visibility, count]) => ({ visibility, count })), ["visibility", "count"]);
    printTable("Natural Person Visibility", Object.entries(report.visibility.naturalPerson).map(([visibility, count]) => ({ visibility, count })), ["visibility", "count"]);
    printTable("Natural Person Sources", naturalSources, ["source_app", "data_classification", "sensitivity_ord", "count"]);
    printTable("Business Person Sources", businessSources, ["source", "country", "sensitivity_ord", "count"]);
    printTable("Cohort Hash Collisions", cohortSamples, ["cohort_hash", "count", "sample_cohort_did"]);
    printTable("Latent Backend Relations", latentCounts, ["relation", "count"]);
    printTable("BPMN Bindings", bpmnBindings, ["nsid", "bpmn_process_id", "status", "sensitivity_ord"]);
    console.log(`\nBPMN activity matches: ${report.latentBackend.bpmnActivityEventMatches}`);
    console.log(`OCEL event matches: ${report.latentBackend.ocelEventMatches}`);
  }
} finally {
  await pool.end();
}
