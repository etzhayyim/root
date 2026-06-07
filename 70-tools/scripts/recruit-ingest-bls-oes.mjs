#!/usr/bin/env node
/**
 * Recruit — BLS OES May 2024 national occupation wage/employment ingest.
 *
 * Source: US Bureau of Labor Statistics, Occupational Employment and Wage Statistics
 *   https://www.bls.gov/oes/special.requests/oesm24nat.zip
 *   License: US Government public-domain (17 U.S.C. §105)
 *
 * Produces:
 *   - vertex_occupation_bls rows: 1 row per SOC code (occ_group=detailed or major)
 *   - vertex_talent_cohort rows: 1 row per ISCO major group (US aggregate employment)
 *
 * Download and prepare:
 *   curl -L -o /tmp/oesm24nat.zip https://www.bls.gov/oes/special.requests/oesm24nat.zip
 *   unzip /tmp/oesm24nat.zip -d /tmp/bls-oes/
 *   # The ZIP contains an Excel file. Convert to CSV:
 *   python3 -c "
 *     import openpyxl, csv, sys
 *     wb = openpyxl.load_workbook('/tmp/bls-oes/national_M2024_dl.xlsx', read_only=True, data_only=True)
 *     ws = wb.active
 *     w = csv.writer(sys.stdout)
 *     for row in ws.iter_rows(values_only=True): w.writerow(['' if v is None else v for v in row])
 *   " > /tmp/bls-oes/national_M2024_dl.csv
 *   node recruit-ingest-bls-oes.mjs --input /tmp/bls-oes/national_M2024_dl.csv
 *
 * Usage:
 *   node recruit-ingest-bls-oes.mjs --input <path-to-csv> [--dry-run] [--year 2024]
 */
import { readFile, writeFile } from "node:fs/promises";

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
const INPUT = getArg("input");
const YEAR = getArg("year", "2024");
const BATCH = parseInt(getArg("batch-size", "200"), 10);
const DRY_RUN = hasFlag("dry-run");
if (!INPUT) { console.error("error: --input required (pre-extracted CSV from oesm24nat.zip)"); process.exit(2); }

/**
 * SOC 2-digit major group → ISCO-08 major group (approximate crosswalk).
 * ILO crosswalk: https://www.ilo.org/public/english/bureau/stat/isco/docs/crosswalk08.xls
 */
const SOC_PREFIX_TO_ISCO = {
  "11": "1",  // Management → Managers
  "13": "2",  // Business/Financial Operations → Professionals
  "15": "2",  // Computer/Mathematical → Professionals
  "17": "2",  // Architecture/Engineering → Professionals
  "19": "2",  // Life/Physical/Social Science → Professionals
  "21": "3",  // Community/Social Service → Technicians and Associate Professionals
  "23": "2",  // Legal → Professionals
  "25": "2",  // Educational Instruction → Professionals
  "27": "3",  // Arts/Design/Entertainment → Technicians and Associate Professionals
  "29": "2",  // Healthcare Practitioners → Professionals
  "31": "3",  // Healthcare Support → Technicians and Associate Professionals
  "33": "3",  // Protective Service → Technicians and Associate Professionals
  "35": "5",  // Food Preparation → Service and Sales Workers
  "37": "9",  // Building/Grounds Cleaning → Elementary Occupations
  "39": "5",  // Personal Care → Service and Sales Workers
  "41": "5",  // Sales/Related → Service and Sales Workers
  "43": "4",  // Office/Administrative Support → Clerical Support Workers
  "45": "6",  // Farming/Fishing/Forestry → Skilled Agricultural Workers
  "47": "7",  // Construction → Craft and Related Trades Workers
  "49": "7",  // Installation/Maintenance/Repair → Craft and Related Trades Workers
  "51": "8",  // Production → Plant and Machine Operators
  "53": "8",  // Transportation/Moving → Plant and Machine Operators
  "55": "0",  // Military Specific → Armed Forces
};

function socToIsco(socCode) {
  const prefix = String(socCode).replace(/-/g, "").slice(0, 2);
  return SOC_PREFIX_TO_ISCO[prefix] ?? null;
}

function parseCsv(text) {
  const out = [];
  let row = [], cur = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i+1] === '"') { cur += '"'; i++; } else inQ = false; }
      else cur += c;
    } else {
      if (c === '"') inQ = true;
      else if (c === ",") { row.push(cur); cur = ""; }
      else if (c === "\n") { row.push(cur); cur = ""; if (row.length > 1 || row[0] !== "") out.push(row); row = []; }
      else if (c !== "\r") cur += c;
    }
  }
  if (cur || row.length) { row.push(cur); if (row.length > 1 || row[0] !== "") out.push(row); }
  return out;
}

function parseNum(v) {
  if (!v || v === "**" || v === "*" || v === "#") return null;
  const n = parseFloat(String(v).replace(/,/g, ""));
  return isNaN(n) ? null : n;
}

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function insertBatch(table, cols, rows) {
  if (rows.length === 0) return;
  const pg = await pool();
  const ph = []; const vals = []; let p = 1;
  for (const row of rows) {
    ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
    vals.push(...row);
  }
  await pg.query(`INSERT INTO ${table} (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
}

async function main() {
  const text = await readFile(INPUT, "utf8");
  const rows = parseCsv(text);
  const header = rows.shift().map(h => String(h).trim().toUpperCase());
  const idx = (k) => { const i = header.indexOf(k); if (i === -1) throw new Error(`column ${k} not found in: ${header.join(",")}`); return i; };

  const OCC_CODE_COL = header.includes("OCC_CODE") ? idx("OCC_CODE") : idx("NAICS");
  const socIdx = idx("OCC_CODE");
  const titleIdx = idx("OCC_TITLE");
  const groupIdx = idx("OCC_GROUP");
  const empIdx = idx("TOT_EMP");
  const empPrseIdx = header.includes("EMP_PRSE") ? idx("EMP_PRSE") : -1;
  const hMeanIdx = header.includes("H_MEAN") ? idx("H_MEAN") : -1;
  const aMeanIdx = header.includes("A_MEAN") ? idx("A_MEAN") : -1;
  const hPct10Idx = header.includes("H_PCT10") ? idx("H_PCT10") : -1;
  const hPct25Idx = header.includes("H_PCT25") ? idx("H_PCT25") : -1;
  const hPct50Idx = header.includes("H_PCT50") ? idx("H_PCT50") : -1;
  const hPct75Idx = header.includes("H_PCT75") ? idx("H_PCT75") : -1;
  const hPct90Idx = header.includes("H_PCT90") ? idx("H_PCT90") : -1;
  const aPct10Idx = header.includes("A_PCT10") ? idx("A_PCT10") : -1;
  const aPct25Idx = header.includes("A_PCT25") ? idx("A_PCT25") : -1;
  const aPct50Idx = header.includes("A_PCT50") ? idx("A_PCT50") : -1;
  const aPct75Idx = header.includes("A_PCT75") ? idx("A_PCT75") : -1;
  const aPct90Idx = header.includes("A_PCT90") ? idx("A_PCT90") : -1;

  const getCol = (row, colIdx) => colIdx === -1 ? null : row[colIdx];

  const blsRows = [];
  const cohortMap = {}; // ISCO major → { tot_emp, count }

  for (const r of rows) {
    const socCode = String(r[socIdx] ?? "").trim();
    const occGroup = String(r[groupIdx] ?? "").trim().toLowerCase();
    const occTitle = String(r[titleIdx] ?? "").trim();
    const totEmp = parseNum(getCol(r, empIdx));
    if (!socCode || !occTitle) continue;

    const isco = socToIsco(socCode);
    const now = new Date().toISOString();

    blsRows.push([
      `bls-oes:${YEAR}:${socCode}`,
      `${YEAR}-${socCode}`,
      RECRUIT_DID,
      BLS_COLLECTION,
      SOURCE,
      LICENSE,
      HOMEPAGE,
      socCode,
      isco,
      occTitle,
      occGroup,
      YEAR,
      totEmp,
      parseNum(getCol(r, empPrseIdx)),
      parseNum(getCol(r, hMeanIdx)),
      parseNum(getCol(r, aMeanIdx)),
      parseNum(getCol(r, hPct10Idx)),
      parseNum(getCol(r, hPct25Idx)),
      parseNum(getCol(r, hPct50Idx)),
      parseNum(getCol(r, hPct75Idx)),
      parseNum(getCol(r, hPct90Idx)),
      parseNum(getCol(r, aPct10Idx)),
      parseNum(getCol(r, aPct25Idx)),
      parseNum(getCol(r, aPct50Idx)),
      parseNum(getCol(r, aPct75Idx)),
      parseNum(getCol(r, aPct90Idx)),
      now,
    ]);

    // Aggregate employment per ISCO major for vertex_talent_cohort
    if (occGroup === "detailed" && isco && totEmp !== null) {
      if (!cohortMap[isco]) cohortMap[isco] = { tot_emp: 0, count: 0 };
      cohortMap[isco].tot_emp += totEmp;
      cohortMap[isco].count += 1;
    }
  }

  console.log(`[bls-oes] parsed vertex_occupation_bls=${blsRows.length} dry-run=${DRY_RUN}`);

  const blsCols = [
    "vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "soc_code","isco_code","occ_title","occ_group","reference_year",
    "tot_emp","emp_prse","h_mean","a_mean",
    "h_pct10","h_pct25","h_pct50","h_pct75","h_pct90",
    "a_pct10","a_pct25","a_pct50","a_pct75","a_pct90",
    "ingested_at",
  ];

  if (!DRY_RUN) {
    for (let i = 0; i < blsRows.length; i += BATCH) {
      await insertBatch("vertex_occupation_bls", blsCols, blsRows.slice(i, i + BATCH));
      if ((i / BATCH) % 5 === 0 || i + BATCH >= blsRows.length) {
        console.log(`[bls-oes] bls progress ${Math.min(i + BATCH, blsRows.length)}/${blsRows.length}`);
      }
    }
  }

  // Build vertex_talent_cohort rows from ISCO aggregates
  const now = new Date().toISOString();
  const cohortCols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "isco_code","country","sex","time_period","size_thousands","unit","ingested_at"];
  const cohortRows = [];
  for (const [isco, agg] of Object.entries(cohortMap)) {
    const vid = `cohort:bls-oes:${YEAR}:isco-${isco}:US:SEX_T:${YEAR}`;
    const rkey = `bls-oes-${YEAR}-${isco}-US-SEX_T-${YEAR}`;
    cohortRows.push([
      vid, rkey, TALENT_DID, COHORT_COLLECTION, SOURCE, LICENSE, HOMEPAGE,
      isco, "US", "SEX_T", YEAR, agg.tot_emp / 1000, "thousands", now,
    ]);
  }

  console.log(`[bls-oes] cohort aggregates isco_major=${cohortRows.length} (one row per ISCO major)`);

  if (!DRY_RUN && cohortRows.length > 0) {
    const pg = await pool();
    const ph = []; const vals = []; let p = 1;
    for (const row of cohortRows) {
      ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
      vals.push(...row);
    }
    await pg.query(
      `INSERT INTO vertex_talent_cohort (${cohortCols.join(",")}) VALUES ${ph.join(",")}`,
      vals
    );
    console.log(`[bls-oes] cohort written=${cohortRows.length}`);
  }

  const summary = {
    source: SOURCE, year: YEAR, bls_rows: blsRows.length, cohort_rows: cohortRows.length,
    cohort_by_isco: Object.fromEntries(Object.entries(cohortMap).map(([k, v]) => [k, v.tot_emp])),
    dry_run: DRY_RUN,
  };
  await writeFile("/tmp/bls-oes-progress.json", JSON.stringify(summary, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[bls-oes] done bls=${blsRows.length} cohort=${cohortRows.length}`);
}

main().catch(e => { console.error(e); process.exit(1); });
