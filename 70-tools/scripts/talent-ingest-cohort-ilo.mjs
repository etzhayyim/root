#!/usr/bin/env node
/**
 * Talent — ILOSTAT cohort ingest (ADR-0018 Tier 3 compliant: aggregate only).
 *
 * Source: ILO Modelled Estimates, dataflow DF_EMP_2EMP_SEX_OCU_NB
 *   https://sdmx.ilo.org/rest/data/ILO,DF_EMP_2EMP_SEX_OCU_NB,1.0/all?format=csv&startPeriod=YYYY
 *   License: CC-BY-4.0
 *
 * Produces vertex_talent_cohort rows: 1 row per (ISCO code, country, sex, year).
 * NO individual PII — only cohort sizes (thousands).
 *
 * Usage:
 *   node talent-ingest-cohort-ilo.mjs --input /tmp/recruit-taxonomy/ilo-emp-occ.csv [--dry-run]
 */
import { readFile, writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const TALENT_DID = "did:web:talent.etzhayyim.com";
const SOURCE = "ilostat";
const LICENSE = "CC-BY-4.0";
const HOMEPAGE = "https://ilostat.ilo.org/";
const COLLECTION = "com.etzhayyim.apps.talent.talentCohort";

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = (k) => args.includes(`--${k}`);
const INPUT = getArg("input");
const BATCH = parseInt(getArg("batch-size", "500"), 10);
const DRY_RUN = hasFlag("dry-run");
if (!INPUT) { console.error("error: --input required"); process.exit(2); }

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

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

// Parse OCU code: "OCU_ISCO08_1" → "1", "OCU_ISCO08_TOTAL" → null (skip)
function parseIscoFromOcu(ocu) {
  if (!ocu || !ocu.startsWith("OCU_ISCO08_")) return null;
  const tail = ocu.slice("OCU_ISCO08_".length);
  if (tail === "TOTAL" || tail === "X") return null;
  if (!/^[0-9]+$/.test(tail)) return null;
  return tail;
}

async function main() {
  const text = await readFile(INPUT, "utf8");
  const rows = parseCsv(text);
  const header = rows.shift();
  const idx = (k) => header.indexOf(k);
  const records = [];
  for (const r of rows) {
    const country = r[idx("REF_AREA")];
    const sex = r[idx("SEX")] ?? "SEX_T";
    const ocu = r[idx("OCU")];
    const period = r[idx("TIME_PERIOD")];
    const value = parseFloat(r[idx("OBS_VALUE")]);
    const isco = parseIscoFromOcu(ocu);
    if (!isco || !country || !period || isNaN(value)) continue;
    records.push({ isco, country, sex, period, value });
  }
  console.log(`[ilo-cohort] parsed=${records.length} (rows=${rows.length}) license=${LICENSE} dry-run=${DRY_RUN}`);

  const cols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "isco_code","country","sex","time_period","size_thousands","unit","ingested_at"];
  const now = new Date().toISOString();
  let written = 0;
  for (let i = 0; i < records.length; i += BATCH) {
    const chunk = records.slice(i, i + BATCH);
    const ph = []; const vals = []; let p = 1;
    for (const rec of chunk) {
      const vid = `cohort:isco:${rec.isco}:${rec.country}:${rec.sex}:${rec.period}`;
      const rkey = `${rec.isco}-${rec.country}-${rec.sex}-${rec.period}`;
      const row = [vid, rkey, TALENT_DID, COLLECTION, SOURCE, LICENSE, HOMEPAGE,
        rec.isco, rec.country, rec.sex, rec.period, rec.value, "thousands", now];
      ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
      vals.push(...row);
    }
    if (!DRY_RUN) {
      const pg = await pool();
      await pg.query(`INSERT INTO vertex_talent_cohort (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
    }
    written += chunk.length;
    if (i % (BATCH * 5) === 0 || i + BATCH >= records.length) {
      console.log(`[ilo-cohort] progress written=${written}/${records.length}`);
    }
  }
  await writeFile("/tmp/talent-cohort-progress.json", JSON.stringify({ written, total: records.length }, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[ilo-cohort] done written=${written}`);
}

main().catch(e => { console.error(e); process.exit(1); });
