#!/usr/bin/env node
/**
 * Talent — Eurostat cohort ingest (lfsa_egais: employment by ISCO major, EU).
 *
 * Source: Eurostat SDMX REST, dataflow lfsa_egais
 *   https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/lfsa_egais?format=SDMX-CSV
 *   License: CC-BY-4.0 (reuse policy: https://ec.europa.eu/eurostat/about/policies/copyright)
 *
 * Filtered subset (apply with awk before ingest):
 *   awk -F, 'NR==1 || ($5=="T" && $7=="EMP" && ($6=="Y15-64" || $6=="Y15-74") && $8 ~ /^OC[0-9]$/ && $10>="2020")' > filtered.csv
 *
 * ISCO mapping: OC0→0, OC1→1, ..., OC9→9 (ISCO major code).
 */
import { readFile, writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const TALENT_DID = "did:web:talent.etzhayyim.com";
const SOURCE = "eurostat";
const LICENSE = "CC-BY-4.0";
const HOMEPAGE = "https://ec.europa.eu/eurostat/";
const COLLECTION = "com.etzhayyim.apps.talent.talentCohort";

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const INPUT = getArg("input");
const DRY_RUN = args.includes("--dry-run");
if (!INPUT) { console.error("error: --input required"); process.exit(2); }

function parseCsv(text) {
  const out = [];
  let row = [], cur = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) { if (c === '"') { if (text[i+1] === '"') { cur += '"'; i++; } else inQ = false; } else cur += c; }
    else {
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

async function main() {
  const text = await readFile(INPUT, "utf8");
  const rows = parseCsv(text);
  const header = rows.shift();
  const idx = (k) => header.indexOf(k);
  const records = [];
  for (const r of rows) {
    const sex = r[idx("sex")];
    const isco08 = r[idx("isco08")];
    const geo = r[idx("geo")];
    const period = r[idx("TIME_PERIOD")];
    const value = parseFloat(r[idx("OBS_VALUE")]);
    if (!/^OC[0-9]$/.test(isco08) || !geo || !period || isNaN(value)) continue;
    records.push({
      isco: isco08.slice(2),
      country: geo,
      sex,
      period,
      value,
    });
  }
  console.log(`[eurostat] parsed=${records.length} dry-run=${DRY_RUN}`);

  const cols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "isco_code","country","sex","time_period","size_thousands","unit","ingested_at"];
  const now = new Date().toISOString();
  const BATCH = 500;
  let written = 0;
  for (let i = 0; i < records.length; i += BATCH) {
    const chunk = records.slice(i, i + BATCH);
    const ph = []; const vals = []; let p = 1;
    for (const rec of chunk) {
      const vid = `cohort:eurostat:${rec.isco}:${rec.country}:${rec.sex}:${rec.period}`;
      const rkey = `eurostat-${rec.isco}-${rec.country}-${rec.sex}-${rec.period}`;
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
    console.log(`[eurostat] progress written=${written}/${records.length}`);
  }
  await writeFile("/tmp/talent-eurostat-progress.json", JSON.stringify({ written, total: records.length }, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[eurostat] done written=${written}`);
}

main().catch(e => { console.error(e); process.exit(1); });
