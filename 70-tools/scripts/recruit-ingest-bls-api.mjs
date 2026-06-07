#!/usr/bin/env node
/**
 * Recruit — BLS OES May 2024 major occupation employment ingest via BLS API v2.
 *
 * Source: US Bureau of Labor Statistics, Occupational Employment and Wage Statistics
 *   https://api.bls.gov/publicAPI/v2/timeseries/data/
 *   License: US Government public-domain (17 U.S.C. §105)
 *   No API key required (anonymous: 500 req/day).
 *
 * Produces vertex_talent_cohort rows: 1 per SOC major group, country=US, year=2024.
 * Also produces vertex_occupation_bls rows with annual mean wage per major group.
 *
 * Note: for detailed SOC-level data with all wage percentiles, download the
 *   national ZIP manually (may require browser) and use recruit-ingest-bls-oes.mjs.
 *   ZIP URL: https://www.bls.gov/oes/special.requests/oesm24nat.zip
 *
 * BLS OES series ID format (25 chars):
 *   OE + U + N + XXXXXXXXX (NAICS, 9) + XXXX (state, 4) + XXXXXX (SOC, 6) + XX (type, 2)
 *   type 01 = employment, 04 = annual mean wage
 *
 * Usage:
 *   node recruit-ingest-bls-api.mjs [--dry-run] [--year 2024]
 */
import { writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const RECRUIT_DID = "did:web:recruit.etzhayyim.com";
const TALENT_DID = "did:web:talent.etzhayyim.com";
const SOURCE = "bls-oes";
const LICENSE = "public-domain";
const HOMEPAGE = "https://www.bls.gov/oes/";
const BLS_COLLECTION = "com.etzhayyim.apps.recruit.occupationBls";
const COHORT_COLLECTION = "com.etzhayyim.apps.talent.talentCohort";

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = (k) => args.includes(`--${k}`);
const DRY_RUN = hasFlag("dry-run");
const YEAR = getArg("year", "2024");

/**
 * SOC major occupation groups (2018 SOC) with ISCO-08 crosswalk and titles.
 * Ordered by 2-digit SOC prefix.
 */
const SOC_MAJOR_GROUPS = [
  { soc: "000000", title: "All Occupations",                                    isco: null },
  { soc: "110000", title: "Management",                                          isco: "1" },
  { soc: "130000", title: "Business and Financial Operations",                   isco: "2" },
  { soc: "150000", title: "Computer and Mathematical",                           isco: "2" },
  { soc: "170000", title: "Architecture and Engineering",                        isco: "2" },
  { soc: "190000", title: "Life, Physical, and Social Science",                  isco: "2" },
  { soc: "210000", title: "Community and Social Service",                        isco: "3" },
  { soc: "230000", title: "Legal",                                               isco: "2" },
  { soc: "250000", title: "Educational Instruction and Library",                 isco: "2" },
  { soc: "270000", title: "Arts, Design, Entertainment, Sports, and Media",      isco: "3" },
  { soc: "290000", title: "Healthcare Practitioners and Technical",              isco: "2" },
  { soc: "310000", title: "Healthcare Support",                                  isco: "3" },
  { soc: "330000", title: "Protective Service",                                  isco: "3" },
  { soc: "350000", title: "Food Preparation and Serving Related",                isco: "5" },
  { soc: "370000", title: "Building and Grounds Cleaning and Maintenance",       isco: "9" },
  { soc: "390000", title: "Personal Care and Service",                           isco: "5" },
  { soc: "410000", title: "Sales and Related",                                   isco: "5" },
  { soc: "430000", title: "Office and Administrative Support",                   isco: "4" },
  { soc: "450000", title: "Farming, Fishing, and Forestry",                      isco: "6" },
  { soc: "470000", title: "Construction and Extraction",                         isco: "7" },
  { soc: "490000", title: "Installation, Maintenance, and Repair",               isco: "7" },
  { soc: "510000", title: "Production",                                          isco: "8" },
  { soc: "530000", title: "Transportation and Material Moving",                  isco: "8" },
];

function makeSeriesId(soc, dataType) {
  // OE(2)+U(1)+N(1) + NAICS(9 zeros)+state(4 zeros) + SOC(6) + type(2) = 25 chars
  const type = String(dataType).slice(-2).padStart(2, "0");
  return `OEUN0000000000000${soc}${type}`;
}

/**
 * Yorishiro-aligned BLS fetch (ADR-2605211900).
 *
 * Contract : ai.etzhayyim.yorishiro.bls.fetchTimeseries
 * Lexicon  : 00-contracts/lexicons/ai/etzhayyim/yorishiro/bls/fetchTimeseries.json
 * MCP equiv: @etzhayyim/yorishiro-bls-mcp
 * Charter  : grant (read-only public-domain US Government data, 17 USC §105)
 *
 * Direct fetch is retained here because this is a standalone ingest script
 * (no Node workspace context to resolve the yorishiro MCP package from);
 * the request shape mirrors the lexicon's input schema exactly. The
 * in-cluster equivalent (yorishiro_bls cell + cell-runner xrpc trigger)
 * is the canonical path — this script will be retired once that lands.
 */
async function fetchBlsTimeseries(seriesIds, startYear, endYear) {
  const body = {
    seriesid: seriesIds,
    startyear: String(startYear),
    endyear: String(endYear),
  };
  const res = await fetch("https://api.bls.gov/publicAPI/v2/timeseries/data/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) throw new Error(`BLS API HTTP ${res.status}`);
  const data = await res.json();
  if (data.status !== "REQUEST_SUCCEEDED") {
    throw new Error(`BLS API error: ${JSON.stringify(data.message)}`);
  }
  return data.Results?.series ?? [];
}

// Backward-compat alias for existing callers within this script.
const fetchBls = fetchBlsTimeseries;

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function main() {
  console.log(`[bls-api] fetching OES May ${YEAR} major occupation groups (dry-run=${DRY_RUN})`);

  // Build series IDs: employment (01) and annual mean wage (04) for each major group
  const empSeriesIds = SOC_MAJOR_GROUPS.map(g => makeSeriesId(g.soc, "0001"));
  const wageSeriesIds = SOC_MAJOR_GROUPS.map(g => makeSeriesId(g.soc, "0004"));

  // BLS API v2 allows 50 series per request
  console.log(`[bls-api] requesting ${empSeriesIds.length} employment series...`);
  const empResults = await fetchBls(empSeriesIds, YEAR, YEAR);
  console.log(`[bls-api] got ${empResults.length} employment series`);

  console.log(`[bls-api] requesting ${wageSeriesIds.length} wage series...`);
  const wageResults = await fetchBls(wageSeriesIds, YEAR, YEAR);
  console.log(`[bls-api] got ${wageResults.length} wage series`);

  // Build lookup maps: seriesId → latest value
  const empMap = {};
  for (const s of empResults) {
    const latest = s.data?.find(d => d.latest === "true") ?? s.data?.[0];
    if (latest) empMap[s.seriesID] = parseFloat(latest.value.replace(/,/g, "")) || null;
  }
  const wageMap = {};
  for (const s of wageResults) {
    const latest = s.data?.find(d => d.latest === "true") ?? s.data?.[0];
    if (latest) wageMap[s.seriesID] = parseFloat(latest.value.replace(/,/g, "")) || null;
  }

  const now = new Date().toISOString();

  // Build vertex_occupation_bls rows
  const blsCols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "soc_code","isco_code","occ_title","occ_group","reference_year","tot_emp","a_mean","ingested_at"];
  const blsRows = [];

  // Build vertex_talent_cohort rows (ISCO-aggregated employment, skip "all occupations")
  const cohortCols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "isco_code","country","sex","time_period","size_thousands","unit","ingested_at"];
  const cohortRows = [];

  for (const grp of SOC_MAJOR_GROUPS) {
    const empSeries = makeSeriesId(grp.soc, "0001");
    const wageSeries = makeSeriesId(grp.soc, "0004");
    const emp = empMap[empSeries] ?? null;
    const wage = wageMap[wageSeries] ?? null;
    const group = grp.soc === "000000" ? "total" : "major";

    blsRows.push([
      `bls-oes:${YEAR}:${grp.soc}`,
      `${YEAR}-${grp.soc}`,
      RECRUIT_DID, BLS_COLLECTION, SOURCE, LICENSE, HOMEPAGE,
      grp.soc.replace(/(\d{2})(\d{4})/, "$1-$2"),  // format as XX-XXXX
      grp.isco,
      grp.title, group, YEAR, emp, wage, now,
    ]);

    if (grp.isco !== null && emp !== null) {
      cohortRows.push([
        `cohort:bls-oes:${YEAR}:isco-${grp.isco}:US:SEX_T:${YEAR}:soc-${grp.soc}`,
        `bls-${YEAR}-isco${grp.isco}-${grp.soc}-US`,
        TALENT_DID, COHORT_COLLECTION, SOURCE, LICENSE, HOMEPAGE,
        grp.isco, "US", "SEX_T", YEAR,
        emp / 1000, "thousands", now,
      ]);
    }
  }

  console.log(`[bls-api] vertex_occupation_bls=${blsRows.length} vertex_talent_cohort=${cohortRows.length}`);
  blsRows.forEach(r => console.log(`  soc=${r[7]} isco=${r[8]} emp=${r[12]?.toLocaleString() ?? "n/a"} wage=${r[13]?.toLocaleString() ?? "n/a"}`));

  if (!DRY_RUN) {
    const pg = await pool();

    // Insert vertex_occupation_bls
    {
      const ph = []; const vals = []; let p = 1;
      for (const row of blsRows) {
        ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
        vals.push(...row);
      }
      await pg.query(
        `INSERT INTO vertex_occupation_bls (${blsCols.join(",")}) VALUES ${ph.join(",")}`,
        vals
      );
      console.log(`[bls-api] written vertex_occupation_bls=${blsRows.length}`);
    }

    // Insert vertex_talent_cohort
    if (cohortRows.length > 0) {
      const ph = []; const vals = []; let p = 1;
      for (const row of cohortRows) {
        ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
        vals.push(...row);
      }
      await pg.query(
        `INSERT INTO vertex_talent_cohort (${cohortCols.join(",")}) VALUES ${ph.join(",")}`,
        vals
      );
      console.log(`[bls-api] written vertex_talent_cohort=${cohortRows.length}`);
    }
  }

  const summary = {
    source: SOURCE, year: YEAR, dry_run: DRY_RUN,
    vertex_occupation_bls: blsRows.length,
    vertex_talent_cohort: cohortRows.length,
    groups: SOC_MAJOR_GROUPS.map(g => ({
      soc: g.soc, title: g.title, isco: g.isco,
      emp: empMap[makeSeriesId(g.soc, "0001")],
      a_mean: wageMap[makeSeriesId(g.soc, "0004")],
    })),
  };
  await writeFile("/tmp/bls-api-progress.json", JSON.stringify(summary, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[bls-api] done`);
}

main().catch(e => { console.error(e); process.exit(1); });
