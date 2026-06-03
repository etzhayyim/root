#!/usr/bin/env node
/**
 * Recruit — Wikidata occupation enrichment (P8283 = ISCO-08 class).
 *
 * Pulls all Wikidata items with an ISCO-08 code + 10-language labels.
 * License: CC0. Extends vertex_occupation with cross-lingual discovery.
 *
 * Usage:
 *   node recruit-ingest-wikidata.mjs [--dry-run]
 */
import { writeFile } from "node:fs/promises";

const RW_CONN = process.env.RW_CONN ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const COLLECTOR_DID = "did:web:recruit.etzhayyim.com";
const SPARQL_URL = "https://query.wikidata.org/sparql";
const UA = "etzhayyim-recruit-taxonomy/0.1 (https://recruit.etzhayyim.com; research)";
const LANGS = ["en", "ja", "fr", "de", "es", "zh", "ar", "ru", "pt", "it"];

const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");

function buildQuery() {
  const labelOpts = LANGS.map((l) => `OPTIONAL { ?item rdfs:label ?label_${l} FILTER(LANG(?label_${l})="${l}") }`).join("\n  ");
  const labelSel = LANGS.map((l) => `?label_${l}`).join(" ");
  return `SELECT ?item ?isco ${labelSel} WHERE {
  ?item wdt:P8283 ?isco .
  ${labelOpts}
}`;
}

async function sparql(query) {
  const res = await fetch(SPARQL_URL, {
    method: "POST",
    headers: {
      "User-Agent": UA,
      "Accept": "application/sparql-results+json",
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `query=${encodeURIComponent(query)}`,
  });
  if (!res.ok) throw new Error(`SPARQL HTTP ${res.status}: ${(await res.text()).slice(0, 400)}`);
  return res.json();
}

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: RW_CONN, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function main() {
  console.log(`[wikidata] SPARQL P8283 query start (${LANGS.length} languages)`);
  const j = await sparql(buildQuery());
  const bindings = j.results.bindings;
  console.log(`[wikidata] fetched=${bindings.length} license=CC0 dry-run=${DRY_RUN}`);

  const records = [];
  for (const b of bindings) {
    const qid = b.item?.value?.split("/").pop();
    const isco = b.isco?.value;
    if (!qid || !isco) continue;
    const rec = { qid, isco };
    for (const l of LANGS) rec[`label_${l}`] = b[`label_${l}`]?.value ?? null;
    records.push(rec);
  }

  const cols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage",
    "wikidata_qid","isco_code",
    ...LANGS.map((l) => `label_${l}`),
    "ingested_at"];
  const now = new Date().toISOString();
  let written = 0;
  const BATCH = 200;
  for (let i = 0; i < records.length; i += BATCH) {
    const chunk = records.slice(i, i + BATCH);
    const ph = []; const vals = []; let p = 1;
    for (const r of chunk) {
      const vid = `occ-wikidata:${r.qid}:${r.isco}`;
      const rkey = `${r.qid}-${r.isco}`;
      const row = [vid, rkey, COLLECTOR_DID, "com.etzhayyim.apps.recruit.occupationWikidata",
        "wikidata", "CC0", "https://www.wikidata.org/",
        r.qid, r.isco,
        ...LANGS.map((l) => r[`label_${l}`]),
        now];
      ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
      vals.push(...row);
    }
    if (!DRY_RUN) {
      const pg = await pool();
      await pg.query(`INSERT INTO vertex_occupation_wikidata (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
    }
    written += chunk.length;
    console.log(`[wikidata] progress written=${written}/${records.length}`);
  }
  await writeFile("/tmp/recruit-wikidata-progress.json", JSON.stringify({ written, total: records.length }, null, 2));
  if (_pgPool) await _pgPool.end();
  console.log(`[wikidata] done written=${written}`);
}

main().catch((e) => { console.error(e.message); process.exit(1); });
