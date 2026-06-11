#!/usr/bin/env node
/**
 * Recruit — ESCO skills + relations ingest (CC-BY-4.0).
 *
 * Sources (tabiya-tech mirror, ESCO v1.1.1):
 *   - skills.csv                       ~13,500 skills
 *   - occupation_skill_relations.csv   ~123,000 pairs
 *   - skill_skill_relations.csv        ~5,800 pairs
 *
 * Usage:
 *   node recruit-ingest-skills.mjs --kind skill        --input /tmp/recruit-taxonomy/esco-skills.csv
 *   node recruit-ingest-skills.mjs --kind occ-skill    --input /tmp/recruit-taxonomy/esco-occ-skill-rel.csv
 *   node recruit-ingest-skills.mjs --kind skill-skill  --input /tmp/recruit-taxonomy/esco-skill-skill-rel.csv
 */
import { readFile, writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const COLLECTOR_DID = "did:web:recruit.etzhayyim.com";
const SOURCE = "esco";
const LICENSE = "CC-BY-4.0";
const HOMEPAGE = "https://esco.ec.europa.eu/";
const PROGRESS_FILE = "/tmp/recruit-skills-progress.json";

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = (k) => args.includes(`--${k}`);
const KIND = getArg("kind"); // skill | occ-skill | skill-skill
const INPUT = getArg("input");
const BATCH_SIZE = parseInt(getArg("batch-size", "200"), 10);
const LIMIT = getArg("limit") ? parseInt(getArg("limit"), 10) : Infinity;
const DRY_RUN = hasFlag("dry-run");
if (!["skill", "occ-skill", "skill-skill"].includes(KIND)) {
  console.error("error: --kind must be skill | occ-skill | skill-skill");
  process.exit(2);
}
if (!INPUT) { console.error("error: --input required"); process.exit(2); }

function* parseCsv(text) {
  let row = [], cur = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i += 1; } else inQ = false; }
      else cur += c;
    } else {
      if (c === '"') inQ = true;
      else if (c === ",") { row.push(cur); cur = ""; }
      else if (c === "\n") { row.push(cur); cur = ""; if (row.length > 1 || row[0] !== "") yield row; row = []; }
      else if (c !== "\r") cur += c;
    }
  }
  if (cur || row.length) { row.push(cur); if (row.length > 1 || row[0] !== "") yield row; }
}

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function writeSkills(rows, header) {
  const idx = (k) => header.indexOf(k);
  const cols = ["vertex_id","rkey","repo","label","source","source_license","source_homepage","code","esco_id","skill_type","reuse_level","name","description","alt_labels","ingested_at"];
  const now = new Date().toISOString();
  const ph = []; const vals = []; let p = 1;
  for (const r of rows) {
    const uri = r[idx("ORIGINURI")] ?? r[0];
    const id = r[idx("ID")];
    const skillType = r[idx("SKILLTYPE")] ?? "";
    const reuse = r[idx("REUSELEVEL")] ?? "";
    const label = r[idx("PREFERREDLABEL")];
    const desc = r[idx("DESCRIPTION")] ?? "";
    const alts = r[idx("ALTLABELS")] ?? "";
    if (!uri || !label) continue;
    const vid = `skill:esco:${id || uri.split("/").pop()}`;
    const rkey = `esco-${(id || uri.split("/").pop()).replace(/[^a-zA-Z0-9]/g, "-").slice(0, 63)}`;
    const altJson = alts ? JSON.stringify(alts.split("\n").map(s => s.trim()).filter(Boolean).slice(0, 50)) : null;
    const row = [vid, rkey, COLLECTOR_DID, "com.etzhayyim.apps.recruit.skill", SOURCE, LICENSE, HOMEPAGE,
      uri, id || null, skillType, reuse, label, desc.slice(0, 4000), altJson, now];
    ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
    vals.push(...row);
  }
  if (!ph.length) return 0;
  const pg = await pool();
  await pg.query(`INSERT INTO vertex_skill (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
  return ph.length;
}

async function writeOccSkill(rows, header) {
  const idx = (k) => header.indexOf(k);
  const cols = ["edge_id","occupation_id","skill_id","relation_type","source","source_license","ingested_at"];
  const now = new Date().toISOString();
  const ph = []; const vals = []; let p = 1;
  for (const r of rows) {
    const occId = r[idx("OCCUPATIONID")];
    const skillId = r[idx("SKILLID")];
    const rel = r[idx("RELATIONTYPE")] ?? "essential";
    if (!occId || !skillId) continue;
    const eid = `occ-skill:${occId}:${skillId}:${rel}`;
    ph.push(`($${p++},$${p++},$${p++},$${p++},$${p++},$${p++},$${p++})`);
    vals.push(eid, occId, skillId, rel, SOURCE, LICENSE, now);
  }
  if (!ph.length) return 0;
  const pg = await pool();
  await pg.query(`INSERT INTO edge_occupation_skill (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
  return ph.length;
}

async function writeSkillSkill(rows, header) {
  const idx = (k) => header.indexOf(k);
  const cols = ["edge_id","requiring_id","required_id","relation_type","source","source_license","ingested_at"];
  const now = new Date().toISOString();
  const ph = []; const vals = []; let p = 1;
  for (const r of rows) {
    const reqing = r[idx("REQUIRINGID")];
    const reqd = r[idx("REQUIREDID")];
    const rel = r[idx("RELATIONTYPE")] ?? "optional";
    if (!reqing || !reqd) continue;
    const eid = `skill-skill:${reqing}:${reqd}:${rel}`;
    ph.push(`($${p++},$${p++},$${p++},$${p++},$${p++},$${p++},$${p++})`);
    vals.push(eid, reqing, reqd, rel, SOURCE, LICENSE, now);
  }
  if (!ph.length) return 0;
  const pg = await pool();
  await pg.query(`INSERT INTO edge_skill_skill (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
  return ph.length;
}

async function main() {
  const text = await readFile(INPUT, "utf8");
  let header = null;
  const rows = [];
  for (const r of parseCsv(text)) {
    if (!header) { header = r; continue; }
    rows.push(r);
    if (rows.length >= LIMIT) break;
  }
  console.log(`[skills:${KIND}] rows=${rows.length} license=${LICENSE} dry-run=${DRY_RUN}`);
  let written = 0;
  const writer = KIND === "skill" ? writeSkills : KIND === "occ-skill" ? writeOccSkill : writeSkillSkill;
  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const chunk = rows.slice(i, i + BATCH_SIZE);
    const n = DRY_RUN ? chunk.length : await writer(chunk, header);
    written += n;
    if (i % (BATCH_SIZE * 10) === 0 || i + BATCH_SIZE >= rows.length) {
      console.log(`[skills:${KIND}] progress written=${written}/${rows.length}`);
      await writeFile(PROGRESS_FILE, JSON.stringify({ kind: KIND, written, total: rows.length }, null, 2));
    }
  }
  if (_pgPool) await _pgPool.end();
  console.log(`[skills:${KIND}] done written=${written}`);
}

main().catch(e => { console.error(e); process.exit(1); });
