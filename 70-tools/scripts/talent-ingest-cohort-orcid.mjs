#!/usr/bin/env node
/**
 * Talent — ORCID researcher count ingest (ADR-0018 Tier 3 cohort-first).
 *
 * Source: ORCID Public API v3.0
 *   https://pub.orcid.org/v3.0/search
 *   License: CC0 1.0 Universal (public domain)
 *   No API key required.
 *
 * Produces vertex_talent_cohort rows:
 *   - 1 row: total registered ORCID profiles (country=WORLD, isco=2)
 *   - 1 row: profiles with recorded institution affiliation (country=WORLD_AFF, isco=2)
 *
 * Note: ORCID Solr does not expose a country-level search field in the public
 * API. Country breakdown requires the 185 GB bulk data file (CC0, figshare).
 * For country-level researcher stats see talent-ingest-cohort-ilo.mjs (ILOSTAT
 * ISCO major 2 covers professional/researcher occupations per country).
 *
 * ADR-0018 compliance: aggregate counts ONLY — no iDs, names, or affiliations stored.
 *
 * Usage:
 *   node talent-ingest-cohort-orcid.mjs [--dry-run] [--year 2024]
 */
import { writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const TALENT_DID = "did:web:talent.etzhayyim.com";
const SOURCE = "orcid";
const LICENSE = "CC0";
const HOMEPAGE = "https://orcid.org/";
const COLLECTION = "com.etzhayyim.apps.talent.talentCohort";
const ISCO_CODE = "2";  // ISCO major 2 = Professionals (includes researchers/academics)

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = (k) => args.includes(`--${k}`);
const DRY_RUN = hasFlag("dry-run");
const YEAR = getArg("year", "2024");

async function fetchCount(query) {
  const url = `https://pub.orcid.org/v3.0/search?q=${encodeURIComponent(query)}&rows=0`;
  const res = await fetch(url, {
    headers: { "Accept": "application/json" },
    signal: AbortSignal.timeout(20000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for query=${query}`);
  const data = await res.json();
  if (data["response-code"]) throw new Error(data["developer-message"] ?? `ORCID error ${data["response-code"]}`);
  return data["num-found"] ?? 0;
}

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function main() {
  console.log(`[orcid] fetching global researcher cohort counts (dry-run=${DRY_RUN})`);

  // Total ORCID registered profiles
  const totalCount = await fetchCount("*:*");
  console.log(`[orcid] total registered ORCID profiles: ${totalCount.toLocaleString()}`);

  // Profiles with recorded institutional affiliation
  const affiliatedCount = await fetchCount("current-institution-affiliation-name:*");
  console.log(`[orcid] profiles with institution affiliation: ${affiliatedCount.toLocaleString()}`);

  // Employment in research/science fields (free-text proxy — not a strict field filter)
  const researchCount = await fetchCount(`current-institution-affiliation-name:universit*`);
  console.log(`[orcid] profiles with university affiliation (proxy): ${researchCount.toLocaleString()}`);

  const now = new Date().toISOString();
  const cols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "isco_code","country","sex","time_period","size_thousands","unit","ingested_at"];

  const cohortRows = [
    [
      `cohort:orcid:${YEAR}:${ISCO_CODE}:WORLD:SEX_T:${YEAR}`,
      `orcid-${YEAR}-${ISCO_CODE}-WORLD-SEX_T-${YEAR}`,
      TALENT_DID, COLLECTION, SOURCE, LICENSE, HOMEPAGE,
      ISCO_CODE, "WORLD", "SEX_T", YEAR,
      totalCount / 1000, "thousands", now,
    ],
    [
      `cohort:orcid:${YEAR}:${ISCO_CODE}:WORLD_AFF:SEX_T:${YEAR}`,
      `orcid-${YEAR}-${ISCO_CODE}-WORLD_AFF-SEX_T-${YEAR}`,
      TALENT_DID, COLLECTION, SOURCE, LICENSE, HOMEPAGE,
      ISCO_CODE, "WORLD_AFF", "SEX_T", YEAR,
      affiliatedCount / 1000, "thousands", now,
    ],
    [
      `cohort:orcid:${YEAR}:${ISCO_CODE}:WORLD_UNI:SEX_T:${YEAR}`,
      `orcid-${YEAR}-${ISCO_CODE}-WORLD_UNI-SEX_T-${YEAR}`,
      TALENT_DID, COLLECTION, SOURCE, LICENSE, HOMEPAGE,
      ISCO_CODE, "WORLD_UNI", "SEX_T", YEAR,
      researchCount / 1000, "thousands", now,
    ],
  ];

  if (!DRY_RUN) {
    const pg = await pool();
    const ph = []; const vals = []; let p = 1;
    for (const row of cohortRows) {
      ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
      vals.push(...row);
    }
    await pg.query(
      `INSERT INTO vertex_talent_cohort (${cols.join(",")}) VALUES ${ph.join(",")}`,
      vals
    );
    console.log(`[orcid] written=${cohortRows.length} rows`);
  }

  const summary = {
    source: SOURCE, year: YEAR,
    total_orcid: totalCount,
    affiliated: affiliatedCount,
    university_affiliated: researchCount,
    rows_written: DRY_RUN ? 0 : cohortRows.length,
    dry_run: DRY_RUN,
    note: "Country breakdown requires 185 GB bulk data file (figshare CC0). Use ILOSTAT data for per-country ISCO-2 employment stats.",
  };
  await writeFile("/tmp/orcid-cohort-progress.json", JSON.stringify(summary, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[orcid] done total=${totalCount.toLocaleString()} affiliated=${affiliatedCount.toLocaleString()}`);
}

main().catch(e => { console.error(e); process.exit(1); });
