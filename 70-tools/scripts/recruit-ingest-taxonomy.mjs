#!/usr/bin/env node
/**
 * Recruit — Occupation taxonomy ingest (ISCO-08 / ESCO / O*NET).
 *
 * Compliance-safe: writes only public-CC-licensed taxonomy data to PDS
 * (recruit.etzhayyim.com DID scope) as `com.etzhayyim.apps.recruit.occupation` records.
 * Each record carries `sourceLicense` for lineage audit.
 *
 * Sources (verified 2026-04-14):
 *   - ISCO-08 (ILO, CC-BY-3.0 IGO)
 *     https://www.ilo.org/ilostat-files/ISCO/newdocs-08-2021/ISCO-08/ISCO-08%20EN.csv
 *     Wide CSV: ISCO_version,major,major_label,sub_major,sub_major_label,minor,minor_label,unit,description
 *   - ESCO v1.1.1 (CC-BY-4.0, via tabiya-tech mirror)
 *     https://raw.githubusercontent.com/tabiya-tech/tabiya-open-dataset/main/tabiya-esco-v1.1.1/csv/occupations.csv
 *     CSV: ORIGINURI,ID,UUIDHISTORY,ISCOGROUPCODE,CODE,PREFERREDLABEL,ALTLABELS,DESCRIPTION,...
 *   - O*NET (US DOL, public domain)
 *     https://www.onetcenter.org/dl_files/database/db_29_0_text.zip → "Occupation Data.txt" (TSV)
 *
 * Usage:
 *   node 70-tools/scripts/recruit-ingest-taxonomy.mjs --source isco --input /tmp/isco08.csv [--dry-run]
 *   node 70-tools/scripts/recruit-ingest-taxonomy.mjs --source esco --input /tmp/esco-occupations.csv [--dry-run]
 *   node 70-tools/scripts/recruit-ingest-taxonomy.mjs --source onet --input "/tmp/.../Occupation Data.txt" [--dry-run]
 *
 * Auth (non-dry-run):
 *   export BEARER_TOKEN=$(etzhayyim agent-token --did did:web:recruit.etzhayyim.com --lxm com.atproto.repo.applyWrites)
 */

import { readFile } from "node:fs/promises";
import { writeFile } from "node:fs/promises";

const PDS_URL = "https://atproto.etzhayyim.com";
const COLLECTOR_DID = "did:web:recruit.etzhayyim.com";
const COLLECTION = "com.etzhayyim.apps.recruit.occupation";
const PROGRESS_FILE = "/tmp/recruit-taxonomy-progress.json";
const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";

const LICENSES = {
  isco: "CC-BY-3.0-IGO",
  esco: "CC-BY-4.0",
  onet: "public-domain",
};
const SOURCE_HOMEPAGE = {
  isco: "https://www.ilo.org/public/english/bureau/stat/isco/isco08/",
  esco: "https://esco.ec.europa.eu/",
  onet: "https://www.onetcenter.org/",
};

const args = process.argv.slice(2);
const getArg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1] ?? d;
};
const hasFlag = (k) => args.includes(`--${k}`);

const SOURCE = getArg("source");
const INPUT = getArg("input");
const MODE = getArg("mode", "pds"); // pds | sql
const BATCH_SIZE = parseInt(getArg("batch-size", "100"), 10);
const LIMIT = getArg("limit") ? parseInt(getArg("limit"), 10) : Infinity;
const DRY_RUN = hasFlag("dry-run");

if (!SOURCE || !LICENSES[SOURCE]) {
  console.error("error: --source must be one of: isco, esco, onet");
  process.exit(2);
}
if (!INPUT) {
  console.error("error: --input PATH required");
  process.exit(2);
}
const TOKEN = process.env.BEARER_TOKEN;
if (MODE === "pds" && !TOKEN && !DRY_RUN) {
  console.error("error: BEARER_TOKEN env var required for --mode pds (or use --dry-run)");
  process.exit(2);
}

// ── Robust CSV/TSV parser (handles quoted fields with embedded newlines) ──
function* parseDelimited(text, delim) {
  let row = [];
  let cur = "";
  let inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { cur += '"'; i += 1; }
        else { inQ = false; }
      } else {
        cur += c;
      }
    } else {
      if (c === '"') { inQ = true; }
      else if (c === delim) { row.push(cur); cur = ""; }
      else if (c === "\n") {
        row.push(cur); cur = "";
        if (row.length > 1 || row[0] !== "") yield row;
        row = [];
      } else if (c === "\r") {
        // ignore (handled at \n)
      } else {
        cur += c;
      }
    }
  }
  if (cur.length > 0 || row.length > 0) {
    row.push(cur);
    if (row.length > 1 || row[0] !== "") yield row;
  }
}

function codeLevel(code) {
  const n = String(code).replace(/[^0-9]/g, "").length;
  if (n === 1) return "major";
  if (n === 2) return "submajor";
  if (n === 3) return "minor";
  if (n === 4) return "unit";
  return "detail";
}

function rkeyFor(source, code) {
  const safe = String(code).replace(/[^a-zA-Z0-9]/g, "-").slice(0, 63);
  return `${source}-${safe}`;
}

function baseRecord(source, extra) {
  return {
    source,
    sourceLicense: LICENSES[source],
    sourceHomepage: SOURCE_HOMEPAGE[source],
    ingestedAt: new Date().toISOString(),
    ...extra,
  };
}

// ── Source-specific extractors ────────────────────────────────────────────
function extractIsco(rows, header) {
  const idx = (k) => header.indexOf(k);
  const seen = new Set();
  const out = [];
  for (const row of rows) {
    const major = row[idx("major")];
    const majorLabel = row[idx("major_label")];
    const subMajor = row[idx("sub_major")];
    const subLabel = row[idx("sub_major_label")];
    const minor = row[idx("minor")];
    const minorLabel = row[idx("minor_label")];
    const unit = row[idx("unit")];
    const unitLabel = row[idx("description")];
    const emit = (code, name) => {
      if (!code || !name) return;
      const key = `isco-${code}`;
      if (seen.has(key)) return;
      seen.add(key);
      out.push(baseRecord("isco", {
        code: String(code),
        iscoCode: String(code),
        name,
        level: codeLevel(code),
      }));
    };
    emit(major, majorLabel);
    emit(subMajor, subLabel);
    emit(minor, minorLabel);
    emit(unit, unitLabel);
  }
  return out;
}

function extractEsco(rows, header) {
  const idx = (k) => header.indexOf(k);
  const out = [];
  for (const row of rows) {
    const conceptUri = row[idx("ORIGINURI")] ?? row[0];
    const label = row[idx("PREFERREDLABEL")];
    const code = row[idx("CODE")];
    const isco = row[idx("ISCOGROUPCODE")];
    const description = row[idx("DESCRIPTION")] ?? "";
    const altLabels = row[idx("ALTLABELS")] ?? "";
    if (!conceptUri || !label) continue;
    out.push(baseRecord("esco", {
      code: conceptUri,
      iscoCode: isco ? String(isco) : undefined,
      escoCode: code || undefined,
      name: label,
      description: description.slice(0, 4000),
      altLabels: altLabels ? altLabels.split("\n").map((s) => s.trim()).filter(Boolean).slice(0, 50) : undefined,
    }));
  }
  return out;
}

function extractOnet(rows, header) {
  const out = [];
  for (const row of rows) {
    const socCode = row[0];
    const title = row[1];
    const description = row[2] ?? "";
    if (!socCode || !title || socCode === header[0]) continue;
    out.push(baseRecord("onet", {
      code: socCode,
      onetSocCode: socCode,
      name: title,
      description: description.slice(0, 4000),
    }));
  }
  return out;
}

// ── RisingWave SQL writer ─────────────────────────────────────────────────
let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 30000 });
  return _pgPool;
}

async function writeBatchSQL(records) {
  const pool = await getRwPool();
  const cols = [
    "vertex_id", "rkey", "repo", "label",
    "source", "source_license", "source_homepage",
    "code", "isco_code", "esco_code", "onet_soc_code",
    "level", "name", "description", "alt_labels", "ingested_at",
  ];
  const placeholders = [];
  const values = [];
  let p = 1;
  for (const rec of records) {
    const vertexId = `occupation:${rec.source}:${rec.code}`;
    const row = [
      vertexId, rkeyFor(rec.source, rec.code), COLLECTOR_DID, COLLECTION,
      rec.source, rec.sourceLicense, rec.sourceHomepage,
      rec.code, rec.iscoCode ?? null, rec.escoCode ?? null, rec.onetSocCode ?? null,
      rec.level ?? null, rec.name, rec.description ?? null,
      rec.altLabels ? JSON.stringify(rec.altLabels) : null,
      rec.ingestedAt,
    ];
    placeholders.push(`(${row.map(() => `$${p++}`).join(",")})`);
    values.push(...row);
  }
  const sql = `INSERT INTO vertex_occupation (${cols.join(",")}) VALUES ${placeholders.join(",")}`;
  await pool.query(sql, values);
}

// ── PDS writer ────────────────────────────────────────────────────────────
async function applyWrites(writes) {
  const res = await fetch(`${PDS_URL}/xrpc/com.atproto.repo.applyWrites`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({ repo: COLLECTOR_DID, validate: false, writes }),
  });
  if (!res.ok) {
    throw new Error(`applyWrites HTTP ${res.status}: ${(await res.text()).slice(0, 500)}`);
  }
  return res.json();
}

// ── Main ──────────────────────────────────────────────────────────────────
async function run() {
  const text = await readFile(INPUT, "utf8");
  const delim = SOURCE === "onet" ? "\t" : ",";
  const rowIter = parseDelimited(text, delim);
  let header = null;
  const rows = [];
  for (const r of rowIter) {
    if (!header) { header = r; continue; }
    rows.push(r);
    if (rows.length >= LIMIT) break;
  }

  const extractor = SOURCE === "isco" ? extractIsco : SOURCE === "esco" ? extractEsco : extractOnet;
  const records = extractor(rows, header);

  console.log(`[${SOURCE}] parsed=${records.length} (rows=${rows.length}) license=${LICENSES[SOURCE]} dry-run=${DRY_RUN}`);

  let written = 0;
  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    const chunk = records.slice(i, i + BATCH_SIZE);
    if (!DRY_RUN) {
      if (MODE === "sql") {
        await writeBatchSQL(chunk);
      } else {
        const writes = chunk.map((rec) => ({
          $type: "com.atproto.repo.applyWrites#create",
          collection: COLLECTION,
          rkey: rkeyFor(SOURCE, rec.code),
          value: { $type: COLLECTION, ...rec },
        }));
        await applyWrites(writes);
      }
    }
    written += chunk.length;
    if (i % (BATCH_SIZE * 10) === 0 || i + BATCH_SIZE >= records.length) {
      console.log(`[${SOURCE}] progress written=${written}/${records.length} (mode=${MODE})`);
      await writeFile(PROGRESS_FILE, JSON.stringify({ source: SOURCE, mode: MODE, written, total: records.length }, null, 2));
    }
  }
  if (_pgPool) await _pgPool.end();
  console.log(`[${SOURCE}] done  written=${written}`);
}

run().catch((err) => { console.error(err); process.exit(1); });
