#!/usr/bin/env node
import crypto from "node:crypto";
import { createRequire } from "node:module";
import process from "node:process";
import { setTimeout as sleep } from "node:timers/promises";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error("DATABASE_URL required");
  process.exit(1);
}

const LIMIT = Number(process.env.LIMIT || process.argv.find((a) => a.startsWith("--limit="))?.split("=")[1] || 10000);
const MAX_LINKS_PER_PROCEDURE = Number(process.env.MAX_LINKS_PER_PROCEDURE || 6);
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 400);
const DB_RETRIES = Number(process.env.DB_RETRIES || process.argv.find((a) => a.startsWith("--db-retries="))?.split("=")[1] || 8);
const SAFE_LIMIT = Math.max(1, Math.min(10000, Math.trunc(Number.isFinite(LIMIT) ? LIMIT : 10000)));

const pool = new pg.Pool({ connectionString: DATABASE_URL, max: 6 });

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function hash(s) {
  return crypto.createHash("sha256").update(String(s)).digest("hex").slice(0, 24);
}

function parseJson(s) {
  try {
    return JSON.parse(s || "{}");
  } catch {
    return {};
  }
}

function isTransientDbError(err) {
  const msg = String(err?.message || err);
  return /cluster recovery|table reader|batch service|Scheduler error|streaming executors|Internal error/i.test(msg);
}

async function withDbRetry(label, fn) {
  let lastErr;
  for (let attempt = 1; attempt <= DB_RETRIES; attempt++) {
    const client = await pool.connect();
    try {
      await client.query("SET RW_IMPLICIT_FLUSH = true");
      return await fn(client);
    } catch (err) {
      lastErr = err;
      if (!isTransientDbError(err) || attempt === DB_RETRIES) throw err;
      const waitMs = Math.min(30000, 2000 * attempt);
      console.error(JSON.stringify({ label, attempt, retryInMs: waitMs, error: String(err).slice(0, 180) }));
      await sleep(waitMs);
    } finally {
      client.release();
    }
  }
  throw lastErr;
}

function classifySource(href) {
  if (/\.(pdf)(?:[?#].*)?$/i.test(href)) return { sourceKind: "pdf", taskKind: "document_form_extract" };
  if (/\.(doc|docx)(?:[?#].*)?$/i.test(href)) return { sourceKind: "word", taskKind: "document_form_extract" };
  if (/\.(xls|xlsx|csv)(?:[?#].*)?$/i.test(href)) return { sourceKind: "spreadsheet", taskKind: "document_form_extract" };
  return { sourceKind: "online_service", taskKind: "online_service_extract" };
}

const PROCEDURE_RELEVANCE = new Map([
  ["birth_certificate", /\b(birth|janam|जन्म)\b/i],
  ["death_certificate", /\b(death|मृत्यु)\b/i],
  ["property_tax", /\b(property|house|tax|assessment|payment|receipt)\b/i],
  ["trade_license", /\b(trade|licen[cs]e|shop|establishment|d&o|health\s*branch)\b/i],
  ["building_permission", /\b(building|permission|permit|planning|layout|development|construction)\b/i],
  ["water_connection", /\b(water|connection|supply|plumber|hydraulic)\b/i],
  ["grievance", /\b(grievance|complaint|redress|jan\s*sunwai|pgrs|register\s+a\s+grievance)\b/i],
  ["rti", /\b(rti|right\s+to\s+information|information\s+act|सूचना)\b/i],
  ["forms", /\b(form|forms|download|application|manual|apply|onlineforms|document)\b/i],
  ["certificates", /\b(certificate|certificates|service|apply|birth|death|income|caste|residence|domicile)\b/i],
]);

function isRelevantToProcedure(link, baseProcedureKey) {
  const hay = `${link.text || ""} ${link.href || ""}`.replace(/[-_/%?=&.]+/g, " ");
  const pattern = PROCEDURE_RELEVANCE.get(baseProcedureKey);
  if (!pattern) return true;
  if (pattern.test(hay)) return true;
  if (baseProcedureKey === "forms" && /\.(pdf|doc|docx|xls|xlsx|csv)(?:[?#].*)?$/i.test(link.href || "")) return true;
  return false;
}

function priorityFor({ taskKind, languageStatus, locale, baseProcedureKey }) {
  let p = taskKind === "document_form_extract" ? 40 : 30;
  if (languageStatus === "source_detected") p += 20;
  if (locale === "en-IN") p += 10;
  if (["birth_certificate", "death_certificate", "property_tax", "trade_license", "water_connection"].includes(baseProcedureKey)) p += 10;
  if (baseProcedureKey === "forms") p += 5;
  return p;
}

async function loadProcedureRows() {
  const { rows } = await pool.query(
    `SELECT vertex_id, owner_did, admin1_name, municipality_code, municipality_name,
            procedure_key, base_procedure_key, source_url, descriptor_json
     FROM vertex_gov_procedure_variant
     WHERE country_iso3 = 'IND'
       AND locality_scope = 'municipality'
       AND variant_status = 'candidate_deepened'
     ORDER BY admin1_name, municipality_name, base_procedure_key
     LIMIT ${SAFE_LIMIT}`,
  );
  return rows;
}

async function loadLanguages() {
  const { rows } = await pool.query(
    `SELECT municipality_code, locale, language_name, script_tag, translation_status
     FROM vertex_gov_form_language_variant
     WHERE country_iso3 = 'IND'
       AND municipality_code IS NOT NULL
       AND form_key = 'local-site'`,
  );
  const byMunicipality = new Map();
  for (const row of rows) {
    const arr = byMunicipality.get(row.municipality_code) || [];
    arr.push(row);
    byMunicipality.set(row.municipality_code, arr);
  }
  for (const arr of byMunicipality.values()) {
    arr.sort((a, b) => {
      const rank = (x) => x.translation_status === "source_detected" ? 0 : x.locale === "en-IN" ? 1 : x.locale === "hi-IN" ? 2 : 3;
      return rank(a) - rank(b) || a.locale.localeCompare(b.locale);
    });
  }
  return byMunicipality;
}

function linksForProcedure(row) {
  const d = parseJson(row.descriptor_json);
  const docs = (d.documentLinks || [])
    .filter((link) => isRelevantToProcedure(link, row.base_procedure_key))
    .map((link) => ({ ...link, ...classifySource(link.href) }));
  const online = (d.onlineServiceLinks || [])
    .filter((link) => isRelevantToProcedure(link, row.base_procedure_key))
    .map((link) => ({ ...link, ...classifySource(link.href) }));
  const seen = new Set();
  const out = [];
  for (const link of [...docs, ...online]) {
    if (!link.href || seen.has(link.href)) continue;
    seen.add(link.href);
    out.push(link);
    if (out.length >= MAX_LINKS_PER_PROCEDURE) break;
  }
  return out;
}

function buildTaskValues(row, lang, link, ordinal) {
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.formExtractionTask/ind-${hash(`${row.vertex_id}|${lang.locale}|${link.href}`)}`;
  const priority = priorityFor({
    taskKind: link.taskKind,
    languageStatus: lang.translation_status,
    locale: lang.locale,
    baseProcedureKey: row.base_procedure_key,
  });
  return [
    vertexId,
    20260427005100 + ordinal,
    "2026-04-27",
    1,
    row.owner_did || "did:web:gov.etzhayyim.com",
    "IND",
    row.admin1_name || "",
    row.municipality_code || "",
    row.municipality_name || "",
    row.vertex_id,
    row.procedure_key || "",
    row.base_procedure_key || "",
    link.href,
    link.sourceKind,
    String(link.text || "").slice(0, 500),
    lang.locale,
    lang.language_name || "",
    lang.script_tag || "",
    lang.translation_status || "",
    link.taskKind,
    "queued",
    priority,
    JSON.stringify({
      evidence: "deepened_procedure_link",
      procedureSourceUrl: row.source_url,
      sourceText: link.text || "",
      priorityReason: {
        taskKind: link.taskKind,
        languageStatus: lang.translation_status,
        baseProcedureKey: row.base_procedure_key,
      },
    }),
    "2026-04-27",
    nowIso(),
    "ind",
    "system",
    "sys.gov.local.form.extraction.queue.seed",
  ];
}

async function insertTaskBatch(client, tasks) {
  if (!tasks.length) return;
  const cols = 28;
  const placeholders = [];
  const params = [];
  for (let i = 0; i < tasks.length; i++) {
    const offset = i * cols;
    placeholders.push(`(${Array.from({ length: cols }, (_, j) => `$${offset + j + 1}${j === 2 ? "::date" : ""}`).join(",")})`);
    params.push(...tasks[i]);
  }
  await client.query(
    `INSERT INTO vertex_gov_form_extraction_task (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      country_iso3, admin1_name, municipality_code, municipality_name,
      procedure_variant_id, procedure_key, base_procedure_key,
      source_url, source_kind, source_text,
      locale, language_name, script_tag, language_status,
      task_kind, task_status, priority, descriptor_json,
      last_verified_at, created_at, org_id, user_id, actor_id
    ) VALUES ${placeholders.join(",")}`,
    params,
  );
}

async function main() {
  const [procedureRows, languagesByMunicipality] = await Promise.all([loadProcedureRows(), loadLanguages()]);
  const tasks = [];
  let procedureWithTasks = 0;
  await withDbRetry("clear-india-form-extraction-queue", (client) =>
    client.query(`DELETE FROM vertex_gov_form_extraction_task WHERE country_iso3 = 'IND'`),
  );
  for (const row of procedureRows) {
    const links = linksForProcedure(row);
    const languages = languagesByMunicipality.get(row.municipality_code) || [];
    if (!links.length || !languages.length) continue;
    procedureWithTasks++;
    for (const link of links) {
      for (const lang of languages) {
        tasks.push(buildTaskValues(row, lang, link, tasks.length));
      }
    }
    console.log(JSON.stringify({ municipality: row.municipality_code, procedure: row.base_procedure_key, links: links.length, languages: languages.length }));
  }
  for (let i = 0; i < tasks.length; i += BATCH_SIZE) {
    const batch = tasks.slice(i, i + BATCH_SIZE);
    await withDbRetry(`seed-task-batch:${i}`, (client) => insertTaskBatch(client, batch));
    console.error(JSON.stringify({ inserted: Math.min(i + batch.length, tasks.length), total: tasks.length }));
  }
  console.error(JSON.stringify({ procedures: procedureRows.length, procedureWithTasks, tasks: tasks.length }));
}

main().finally(async () => pool.end());
