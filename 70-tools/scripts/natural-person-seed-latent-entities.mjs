#!/usr/bin/env node
import { createRequire } from "node:module";
import process from "node:process";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;
const OWNER_DID = "did:web:coverage.etzhayyim.com";

function usage(code = 0) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/natural-person-seed-latent-entities.mjs [--apply] [--json]

Dry-run is the default. Seeds one latent entity per natural-person cohort and
links it back to the cohort with edge_entity_cohort_link + edge_entity_evidence.
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

function entityId(cohortHash) {
  return `at://did:web:coverage.etzhayyim.com/com.etzhayyim.apps.coverage.latentEntity/natural-person-cohort-${cohortHash}`;
}

function edgeId(prefix, cohortHash) {
  return `at://did:web:coverage.etzhayyim.com/com.etzhayyim.apps.coverage.${prefix}/natural-person-cohort-${cohortHash}`;
}

function label(row) {
  const parts = [
    row.vital_status,
    row.era,
    row.country,
    row.gender,
    row.death_cause_icd10,
  ].filter(Boolean);
  return `natural person cohort: ${parts.join(" / ") || row.cohort_hash}`;
}

async function exists(table, idColumn, id) {
  const result = await pool.query(`SELECT 1 FROM ${table} WHERE ${idColumn} = $1 LIMIT 1`, [id]);
  return result.rows.length > 0;
}

async function main() {
  const result = await pool.query(`
    SELECT vertex_id, cohort_hash, cohort_did, vital_status, era, country, gender,
           death_cause_icd10, sensitivity_ord, intel_estimated_count
      FROM vertex_natural_person_cohort_person
     WHERE cohort_hash IS NOT NULL AND cohort_hash <> ''
     ORDER BY vertex_id
  `);

  let plannedEntities = 0;
  let plannedCohortLinks = 0;
  let plannedEvidenceLinks = 0;
  let insertedEntities = 0;
  let insertedCohortLinks = 0;
  let insertedEvidenceLinks = 0;
  let flushWarning = null;

  const samples = [];
  for (const row of result.rows) {
    const entityVid = entityId(row.cohort_hash);
    const cohortLinkId = edgeId("entityCohortLink", row.cohort_hash);
    const evidenceEdgeId = edgeId("entityEvidence", row.cohort_hash);

    const entityMissing = !(await exists("vertex_latent_entity", "vertex_id", entityVid));
    const cohortLinkMissing = !(await exists("edge_entity_cohort_link", "edge_id", cohortLinkId));
    const evidenceMissing = !(await exists("edge_entity_evidence", "edge_id", evidenceEdgeId));

    if (entityMissing) plannedEntities++;
    if (cohortLinkMissing) plannedCohortLinks++;
    if (evidenceMissing) plannedEvidenceLinks++;
    if (samples.length < 10 && (entityMissing || cohortLinkMissing || evidenceMissing)) {
      samples.push({ cohortHash: row.cohort_hash, entityVid, cohortVid: row.vertex_id });
    }

    if (!opts.apply) continue;

    const sensitivity = 300;
    if (entityMissing) {
      const insert = await queryWithRecoveryRetry(
        `INSERT INTO vertex_latent_entity (
           vertex_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at,
           entity_kind, canonical_label, existence_probability, k_evidence_count,
           viewpoint_consensus, fission_eligible, status, primary_topic_vid, individual_did
         ) VALUES ($1, $2, $3, $4, $4, $4, NOW(), $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
        [
          entityVid,
          1,
          sensitivity,
          OWNER_DID,
          "natural_person_cohort",
          label(row),
          0.99,
          Number(row.intel_estimated_count ?? 0) > 0 ? 1 : 0,
          1,
          row.vital_status === "alive",
          "active",
          row.vertex_id,
          `did:web:natural-person.etzhayyim.com:latent:${row.cohort_hash}`,
        ],
      );
      insertedEntities += insert.rowCount ?? 0;
    }

    if (cohortLinkMissing) {
      const insert = await queryWithRecoveryRetry(
        `INSERT INTO edge_entity_cohort_link (
           edge_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at,
           src_vid, dst_vid, link_confidence
         ) VALUES ($1, 1, $2, $3, $3, $3, NOW(), $4, $5, $6)`,
        [cohortLinkId, sensitivity, OWNER_DID, entityVid, row.vertex_id, 0.99],
      );
      insertedCohortLinks += insert.rowCount ?? 0;
    }

    if (evidenceMissing) {
      const insert = await queryWithRecoveryRetry(
        `INSERT INTO edge_entity_evidence (
           edge_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at,
           src_vid, dst_vid, evidence_weight
         ) VALUES ($1, 1, $2, $3, $3, $3, NOW(), $4, $5, $6)`,
        [evidenceEdgeId, sensitivity, OWNER_DID, row.vertex_id, entityVid, 1.0],
      );
      insertedEvidenceLinks += insert.rowCount ?? 0;
    }
  }

  if (opts.apply) flushWarning = await flushBestEffort();

  const counts = await Promise.all([
    pool.query("SELECT COUNT(*)::bigint AS count FROM vertex_latent_entity"),
    pool.query("SELECT COUNT(*)::bigint AS count FROM edge_entity_cohort_link"),
    pool.query("SELECT COUNT(*)::bigint AS count FROM edge_entity_evidence"),
  ]);

  const report = {
    evaluatedAt: new Date().toISOString(),
    apply: opts.apply,
    sourceCohorts: result.rows.length,
    plannedEntities,
    plannedCohortLinks,
    plannedEvidenceLinks,
    insertedEntities,
    insertedCohortLinks,
    insertedEvidenceLinks,
    flushWarning,
    totals: {
      vertexLatentEntity: Number(counts[0].rows[0]?.count ?? 0),
      edgeEntityCohortLink: Number(counts[1].rows[0]?.count ?? 0),
      edgeEntityEvidence: Number(counts[2].rows[0]?.count ?? 0),
    },
    samples,
  };

  if (opts.json) console.log(JSON.stringify(report, null, 2));
  else {
    console.log(`evaluatedAt: ${report.evaluatedAt}`);
    console.log(`apply: ${report.apply}`);
    console.log(`sourceCohorts: ${report.sourceCohorts}`);
    console.log(`plannedEntities: ${report.plannedEntities}`);
    console.log(`plannedCohortLinks: ${report.plannedCohortLinks}`);
    console.log(`plannedEvidenceLinks: ${report.plannedEvidenceLinks}`);
    console.log(`insertedEntities: ${report.insertedEntities}`);
    console.log(`insertedCohortLinks: ${report.insertedCohortLinks}`);
    console.log(`insertedEvidenceLinks: ${report.insertedEvidenceLinks}`);
  }
}

try {
  await main();
} finally {
  await pool.end();
}
