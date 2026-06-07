#!/usr/bin/env node
/**
 * Recruit / Talent — AT Protocol backfill script.
 *
 * Registers recruit.etzhayyim.com and talent.etzhayyim.com actors + profiles, then
 * backfills vertex_repo_record from the directly-ingested taxonomy tables:
 *
 *   vertex_occupation      → com.etzhayyim.apps.recruit.occupationTaxonomy  (5,172)
 *   vertex_skill           → com.etzhayyim.apps.recruit.skillTaxonomy       (13,896)
 *   vertex_talent_cohort   → com.etzhayyim.apps.talent.talentCohort         (~21K+)
 *   vertex_occupation_bls  → com.etzhayyim.apps.recruit.occupationBls       (23)
 *
 * Makes all taxonomy data AT-addressable via at://… URIs and queryable
 * through the PDS AppView pipeline.
 *
 * Usage:
 *   node recruit-talent-backfill-at-records.mjs [--dry-run] [--step actors|profiles|records|all]
 */
import { writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const BATCH   = parseInt(process.env.BATCH ?? "500");
const args    = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const getArg  = (k, d) => { const i = args.indexOf(k); return i === -1 ? d : args[i + 1] ?? d; };
const STEP    = getArg("--step", "all");
const NOW     = new Date().toISOString();
const TS_MS   = Date.now();

// ── Actor manifests ──────────────────────────────────────────────────────────
const ACTORS = [
  {
    did: "did:web:recruit.etzhayyim.com",
    handle: "recruit.etzhayyim.com",
    display_name: "Recruit",
    description: "Global 求人 intelligence — ISCO/ESCO/O*NET taxonomy, BLS OES wages. ADR-0027.",
    execution_tier: "T2",
    status: "active",
    performer_type: "service",
    runtime_type: "cf-worker",
    category: "talent",
  },
  {
    did: "did:web:talent.etzhayyim.com",
    handle: "talent.etzhayyim.com",
    display_name: "Talent",
    description: "Global 人材 intelligence — ISCO cohort-first per ADR-0018/0027. ILO+Eurostat+BLS+ORCID.",
    execution_tier: "T2",
    status: "active",
    performer_type: "service",
    runtime_type: "cf-worker",
    category: "talent",
  },
];

// ── pg pool ───────────────────────────────────────────────────────────────────
let _pool = null;
async function pool() {
  if (_pool) return _pool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 120_000 });
  return _pool;
}

async function query(sql, vals = []) {
  const db = await pool();
  return db.query(sql, vals);
}

// ── helpers ───────────────────────────────────────────────────────────────────
function batchInsert(table, cols, rows) {
  const ph = []; const vals = []; let p = 1;
  for (const row of rows) {
    ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
    vals.push(...row);
  }
  return query(`INSERT INTO ${table} (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
}

function makeUri(repo, collection, rkey) {
  return `at://${repo}/${collection}/${rkey}`;
}

// ── Step 1: actors ────────────────────────────────────────────────────────────
async function stepActors() {
  console.log("[backfill] step=actors");
  const existing = await query(
    `SELECT did FROM vertex_actor WHERE did = ANY($1)`,
    [ACTORS.map(a => a.did)]
  );
  const existingSet = new Set(existing.rows.map(r => r.did));

  const cols = ["vertex_id","did","handle","display_name","execution_tier","status",
                "performer_type","runtime_type","category","created_at"];
  const rows = ACTORS
    .filter(a => !existingSet.has(a.did))
    .map(a => [a.did, a.did, a.handle, a.display_name, a.execution_tier,
               a.status, a.performer_type, a.runtime_type, a.category, NOW]);

  if (rows.length === 0) {
    console.log("[backfill] actors already registered — skip");
    return;
  }
  if (!DRY_RUN) await batchInsert("vertex_actor", cols, rows);
  console.log(`[backfill] actors written=${rows.length}`);
}

// ── Step 2: profiles ──────────────────────────────────────────────────────────
async function stepProfiles() {
  console.log("[backfill] step=profiles");
  const existing = await query(
    `SELECT repo FROM vertex_profile WHERE repo = ANY($1)`,
    [ACTORS.map(a => a.did)]
  );
  const existingSet = new Set(existing.rows.map(r => r.repo));

  const cols = ["repo","display_name","description","created_at"];
  const rows = ACTORS
    .filter(a => !existingSet.has(a.did))
    .map(a => [a.did, a.display_name, a.description, NOW]);

  if (rows.length === 0) {
    console.log("[backfill] profiles already registered — skip");
    return;
  }
  if (!DRY_RUN) await batchInsert("vertex_profile", cols, rows);
  console.log(`[backfill] profiles written=${rows.length}`);
}

// ── Step 3: records ───────────────────────────────────────────────────────────
const REC_COLS = ["uri","repo","collection","rkey","value_json","indexed_at","ts_ms"];

function makeRecRows(sourceRows, collection, toJson) {
  return sourceRows.map(r => {
    const rkey = r.rkey;
    const repo = r.repo;
    const uri  = makeUri(repo, collection, rkey);
    const vj   = JSON.stringify(toJson(r));
    return [uri, repo, collection, rkey, vj, NOW, TS_MS];
  });
}

async function insertRecBatch(rows, label) {
  let written = 0;
  for (let i = 0; i < rows.length; i += BATCH) {
    if (!DRY_RUN) await batchInsert("vertex_repo_record", REC_COLS, rows.slice(i, i + BATCH));
    written += Math.min(BATCH, rows.length - i);
    if (i % (BATCH * 10) === 0 || i + BATCH >= rows.length)
      console.log(`[backfill] ${label} ${written}/${rows.length}`);
  }
}

async function stepRecords() {
  console.log("[backfill] step=records");

  // ── occupation taxonomy ──────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT rkey, repo, source, source_license, source_homepage,
              code, isco_code, esco_code, onet_soc_code, level, name, description
       FROM vertex_occupation`
    );
    const coll = "com.etzhayyim.apps.recruit.occupationTaxonomy";
    const recRows = makeRecRows(rows, coll, r => ({
      $type: coll,
      code: r.code, iscoCode: r.isco_code, escoCode: r.esco_code,
      onetSocCode: r.onet_soc_code, level: r.level,
      name: r.name, description: r.description,
      source: r.source, sourceLicense: r.source_license, sourceHomepage: r.source_homepage,
    }));
    await insertRecBatch(recRows, "occupation");
  }

  // ── skill taxonomy ───────────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT rkey, repo, source, source_license, source_homepage,
              code, esco_id, skill_type, reuse_level, name, description
       FROM vertex_skill`
    );
    const coll = "com.etzhayyim.apps.recruit.skillTaxonomy";
    const recRows = makeRecRows(rows, coll, r => ({
      $type: coll,
      code: r.code, escoId: r.esco_id,
      skillType: r.skill_type, reuseLevel: r.reuse_level,
      name: r.name, description: r.description,
      source: r.source, sourceLicense: r.source_license, sourceHomepage: r.source_homepage,
    }));
    await insertRecBatch(recRows, "skill");
  }

  // ── talent cohort ────────────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT rkey, repo, source, source_license, source_homepage,
              isco_code, country, sex, time_period, size_thousands, unit
       FROM vertex_talent_cohort`
    );
    const coll = "com.etzhayyim.apps.talent.talentCohort";
    const recRows = makeRecRows(rows, coll, r => ({
      $type: coll,
      iscoCode: r.isco_code, country: r.country, sex: r.sex,
      timePeriod: r.time_period, sizeThousands: r.size_thousands, unit: r.unit,
      source: r.source, sourceLicense: r.source_license, sourceHomepage: r.source_homepage,
    }));
    await insertRecBatch(recRows, "talentCohort");
  }

  // ── BLS OES occupation ───────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT rkey, repo, source, source_license, source_homepage,
              soc_code, isco_code, occ_title, occ_group, reference_year,
              tot_emp, h_mean, a_mean, h_pct50, a_pct50
       FROM vertex_occupation_bls`
    );
    const coll = "com.etzhayyim.apps.recruit.occupationBls";
    const recRows = makeRecRows(rows, coll, r => ({
      $type: coll,
      socCode: r.soc_code, iscoCode: r.isco_code,
      occTitle: r.occ_title, occGroup: r.occ_group, referenceYear: r.reference_year,
      totEmp: r.tot_emp, hMean: r.h_mean, aMean: r.a_mean,
      hPct50: r.h_pct50, aPct50: r.a_pct50,
      source: r.source, sourceLicense: r.source_license, sourceHomepage: r.source_homepage,
    }));
    await insertRecBatch(recRows, "occupationBls");
  }

  // ── job postings (ATS direct + future sources) ───────────────────────────
  {
    const { rows } = await query(
      `SELECT vertex_id AS rkey, repo, source, source_license, source_url,
              title, employer_name, isco_code, country, location,
              remote_allowed, employment_type,
              salary_min, salary_max, salary_currency,
              posted_at, expires_at
       FROM vertex_job_posting
       WHERE rkey IS NOT NULL`
    );
    const coll = "com.etzhayyim.apps.recruit.jobPosting";
    // Use vertex_id as rkey (already set in ingest scripts)
    const recRows = rows.map(r => {
      const rk   = r.rkey.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 128);
      const repo  = r.repo ?? "did:web:recruit.etzhayyim.com";
      const uri   = makeUri(repo, coll, rk);
      const vj    = JSON.stringify({
        $type: coll,
        title: r.title, employerName: r.employer_name,
        iscoCode: r.isco_code, country: r.country, location: r.location,
        remoteAllowed: r.remote_allowed, employmentType: r.employment_type,
        salaryMin: r.salary_min, salaryMax: r.salary_max, salaryCurrency: r.salary_currency,
        postedAt: r.posted_at, expiresAt: r.expires_at,
        source: r.source, sourceLicense: r.source_license, sourceUrl: r.source_url,
      });
      return [uri, repo, coll, rk, vj, NOW, TS_MS];
    });
    await insertRecBatch(recRows, "jobPosting");
  }

  // ── press signals ─────────────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT vertex_id AS rkey, source, source_url, source_license,
              company_name, headline, trigger_type, trigger_score,
              isco_codes, country, published_at
       FROM vertex_press_signal`
    );
    const coll = "com.etzhayyim.apps.recruit.pressSignal";
    const repo  = "did:web:recruit.etzhayyim.com";
    const recRows = rows.map(r => {
      const rk  = r.rkey.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 128);
      const uri = makeUri(repo, coll, rk);
      const vj  = JSON.stringify({
        $type: coll,
        companyName: r.company_name, headline: r.headline,
        triggerType: r.trigger_type, triggerScore: r.trigger_score,
        iscoCodes: (() => { try { return JSON.parse(r.isco_codes ?? "[]"); } catch { return []; } })(),
        country: r.country, publishedAt: r.published_at,
        source: r.source, sourceLicense: r.source_license, sourceUrl: r.source_url,
      });
      return [uri, repo, coll, rk, vj, NOW, TS_MS];
    });
    await insertRecBatch(recRows, "pressSignal");
  }

  // ── demand forecasts ──────────────────────────────────────────────────────
  {
    const { rows } = await query(
      `SELECT vertex_id AS rkey, isco_code, country, period,
              demand_score, supply_size_k, typical_salary, salary_currency,
              engagement_types, top_skills, press_signal_count, posting_count
       FROM vertex_demand_forecast`
    );
    const coll = "com.etzhayyim.apps.recruit.demandForecast";
    const repo  = "did:web:recruit.etzhayyim.com";
    const recRows = rows.map(r => {
      const rk  = r.rkey.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 128);
      const uri = makeUri(repo, coll, rk);
      const parseJson = v => { try { return JSON.parse(v ?? "[]"); } catch { return []; } };
      const vj  = JSON.stringify({
        $type: coll,
        iscoCode: r.isco_code, country: r.country, period: r.period,
        demandScore: r.demand_score, supplySizeK: r.supply_size_k,
        typicalSalary: r.typical_salary, salaryCurrency: r.salary_currency,
        engagementTypes: parseJson(r.engagement_types),
        topSkills: parseJson(r.top_skills),
        pressSignalCount: Number(r.press_signal_count),
        postingCount: Number(r.posting_count),
      });
      return [uri, repo, coll, rk, vj, NOW, TS_MS];
    });
    await insertRecBatch(recRows, "demandForecast");
  }
}

// ── main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`[backfill] start  step=${STEP}  dry-run=${DRY_RUN}`);
  const t0 = Date.now();

  if (STEP === "all" || STEP === "actors")   await stepActors();
  if (STEP === "all" || STEP === "profiles") await stepProfiles();
  if (STEP === "all" || STEP === "records")  await stepRecords();

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`[backfill] done  elapsed=${elapsed}s`);

  // summary counts
  if (!DRY_RUN) {
    const { rows } = await query(`
      SELECT collection, COUNT(*) AS cnt
      FROM vertex_repo_record
      WHERE collection IN (
        'com.etzhayyim.apps.recruit.occupationTaxonomy',
        'com.etzhayyim.apps.recruit.skillTaxonomy',
        'com.etzhayyim.apps.talent.talentCohort',
        'com.etzhayyim.apps.recruit.occupationBls',
        'com.etzhayyim.apps.recruit.jobPosting',
        'com.etzhayyim.apps.recruit.pressSignal',
        'com.etzhayyim.apps.recruit.demandForecast'
      )
      GROUP BY collection ORDER BY collection
    `);
    console.log("[backfill] vertex_repo_record counts:");
    rows.forEach(r => console.log(`  ${r.collection}: ${r.cnt}`));
    await writeFile("/tmp/backfill-summary.json", JSON.stringify({rows, elapsed}, null, 2));
  }

  if (_pool) await _pool.end();
}

main().catch(e => { console.error(e); process.exit(1); });
