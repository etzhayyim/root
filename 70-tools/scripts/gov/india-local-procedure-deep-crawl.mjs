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

const LIMIT = Number(process.env.LIMIT || process.argv.find((a) => a.startsWith("--limit="))?.split("=")[1] || 250);
const CONCURRENCY = Number(process.env.CONCURRENCY || process.argv.find((a) => a.startsWith("--concurrency="))?.split("=")[1] || 4);
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS || process.argv.find((a) => a.startsWith("--timeout-ms="))?.split("=")[1] || 12000);
const DB_RETRIES = Number(process.env.DB_RETRIES || process.argv.find((a) => a.startsWith("--db-retries="))?.split("=")[1] || 8);
const MAX_EVIDENCE_PER_ROW = Number(process.env.MAX_EVIDENCE_PER_ROW || 4);
const SAFE_LIMIT = Math.max(1, Math.min(10000, Math.trunc(Number.isFinite(LIMIT) ? LIMIT : 250)));

const pool = new pg.Pool({ connectionString: DATABASE_URL, max: CONCURRENCY + 2 });

const DOCUMENT_RE = /\.(pdf|doc|docx|xls|xlsx|csv)(?:[?#].*)?$/i;
const ONLINE_RE = /\b(apply|online|portal|service|login|registration|payment|certificate|grievance|complaint|rti|tax|license|licence|permission|water)\b/i;
const NOISE_HOST_RE = /(^|\.)((facebook|x|twitter|linkedin|whatsapp|telegram|pinterest)\.com|t\.me)$/i;
const NOISE_URL_RE = /\b(sharer|share\?|intent\/tweet|wa\.me|mailto:|javascript:)/i;
const PROCEDURE_PATTERNS = new Map([
  ["birth_certificate", /\b(birth\s+certificate|birth registration|janam|जन्म)\b/i],
  ["death_certificate", /\b(death\s+certificate|death registration|मृत्यु)\b/i],
  ["property_tax", /\b(property\s+tax|house\s+tax|assessment|tax payment)\b/i],
  ["trade_license", /\b(trade\s+licen[cs]e|shop\s+licen[cs]e|establishment license)\b/i],
  ["building_permission", /\b(building\s+(permit|permission)|planning permission|layout approval)\b/i],
  ["water_connection", /\b(water\s+(connection|supply|tax)|जल)\b/i],
  ["grievance", /\b(grievance|complaint|public grievance|शिकायत)\b/i],
  ["rti", /\b(RTI|right to information|सूचना का अधिकार)\b/i],
  ["forms", /\b(forms?|downloads?|application form|आवेदन)\b/i],
  ["certificates", /\b(certificates?|e[- ]district|service plus|सेवा)\b/i],
]);

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function hash(s) {
  return crypto.createHash("sha256").update(String(s)).digest("hex").slice(0, 16);
}

function absUrl(base, href) {
  try {
    const url = new URL(href, base);
    if (!["http:", "https:"].includes(url.protocol)) return "";
    if (NOISE_HOST_RE.test(url.hostname) || NOISE_URL_RE.test(url.toString())) return "";
    url.hash = "";
    return url.toString();
  } catch {
    return "";
  }
}

function cleanText(s) {
  return String(s || "")
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 260);
}

function parseJson(s) {
  try {
    return JSON.parse(s || "{}");
  } catch {
    return {};
  }
}

function extractLinks(html, baseUrl) {
  const links = [];
  const seen = new Set();
  const re = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(html)) && links.length < 1500) {
    const href = absUrl(baseUrl, m[1]);
    if (!href || seen.has(href)) continue;
    seen.add(href);
    links.push({ href, text: cleanText(m[2]) });
  }
  return links;
}

function scoreLink(link, baseProcedureKey) {
  const hay = `${link.text} ${link.href}`.replace(/[-_/%?=&.]+/g, " ");
  let score = 0;
  const procedurePattern = PROCEDURE_PATTERNS.get(baseProcedureKey);
  if (procedurePattern?.test(hay)) score += 5;
  if (DOCUMENT_RE.test(link.href)) score += 4;
  if (ONLINE_RE.test(hay)) score += 2;
  if (/s3waas\.gov\.in|\.gov\.in|\.nic\.in/i.test(link.href)) score += 1;
  return score;
}

async function fetchEvidence(url) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      signal: ac.signal,
      redirect: "follow",
      headers: {
        "User-Agent": "etzhayyim/1.0 government local procedure evidence crawl (+https://etzhayyim.com)",
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.5",
      },
    });
    const contentType = resp.headers.get("content-type") || "";
    if (!resp.ok) return { ok: false, status: resp.status, contentType, finalUrl: resp.url, links: [] };
    if (!/html|text/i.test(contentType)) {
      return { ok: true, status: resp.status, contentType, finalUrl: resp.url, links: [] };
    }
    const html = await resp.text();
    return { ok: true, status: resp.status, contentType, finalUrl: resp.url, links: extractLinks(html, resp.url) };
  } finally {
    clearTimeout(t);
  }
}

function uniqueByHref(links, limit) {
  const out = [];
  const seen = new Set();
  for (const link of links) {
    if (!link.href || seen.has(link.href)) continue;
    try {
      const url = new URL(link.href);
      if (NOISE_HOST_RE.test(url.hostname) || NOISE_URL_RE.test(url.toString())) continue;
    } catch {
      continue;
    }
    seen.add(link.href);
    out.push(link);
    if (out.length >= limit) break;
  }
  return out;
}

async function loadRows() {
  const { rows } = await pool.query(
    `SELECT vertex_id, municipality_code, municipality_name, admin1_name,
            procedure_key, base_procedure_key, portal_url, source_url,
            descriptor_json, language_tags, script_tags
     FROM vertex_gov_procedure_variant
     WHERE country_iso3 = 'IND'
       AND locality_scope = 'municipality'
       AND variant_status IN ('candidate_detected', 'candidate_deepened')
     ORDER BY admin1_name, municipality_name, base_procedure_key
     LIMIT ${SAFE_LIMIT}`,
  );
  return rows;
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
      const result = await fn(client);
      return result;
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

async function updateRow(row, descriptor, deepEvidenceLinks, documentLinks, onlineServiceLinks, crawledUrls, errors) {
  const allEvidence = uniqueByHref([
    ...(descriptor.evidenceLinks || []),
    ...deepEvidenceLinks,
    ...documentLinks,
    ...onlineServiceLinks,
  ], 20);
  const enriched = {
    ...descriptor,
    evidenceDepth: 2,
    evidenceCrawledAt: nowIso(),
    crawledUrls,
    deepEvidenceLinks: uniqueByHref(deepEvidenceLinks, 12),
    documentLinks: uniqueByHref(documentLinks, 10),
    onlineServiceLinks: uniqueByHref(onlineServiceLinks, 10),
    evidenceLinks: allEvidence,
    crawlErrors: errors.slice(0, 6),
  };
  const bestPortal = onlineServiceLinks[0]?.href || documentLinks[0]?.href || row.portal_url || row.source_url;
  const formKey = documentLinks.length ? `ind.local.${row.base_procedure_key}.form` : (row.form_key || "");
  const formatKey = documentLinks.length ? "document-link" : "";
  const status = deepEvidenceLinks.length || documentLinks.length || onlineServiceLinks.length
    ? "candidate_deepened"
    : "candidate_detected";
  await withDbRetry(`deep-update:${row.vertex_id}`, (client) =>
    client.query(
      `UPDATE vertex_gov_procedure_variant
       SET variant_status = $1,
           portal_url = $2,
           form_key = $3,
           format_key = $4,
           source_kind = $5,
           descriptor_json = $6,
           last_verified_at = $7
       WHERE vertex_id = $8`,
      [
        status,
        bestPortal,
        formKey,
        formatKey,
        status === "candidate_deepened" ? "municipal_site_deep_detected" : "municipal_site_detected",
        JSON.stringify(enriched),
        "2026-04-27",
        row.vertex_id,
      ],
    ),
  );
  return status;
}

async function processOne(row) {
  const descriptor = parseJson(row.descriptor_json);
  const seedLinks = uniqueByHref([
    ...(descriptor.evidenceLinks || []),
    { href: row.portal_url, text: "portal_url" },
  ].filter((link) => link.href), MAX_EVIDENCE_PER_ROW);
  const deepEvidenceLinks = [];
  const documentLinks = [];
  const onlineServiceLinks = [];
  const crawledUrls = [];
  const errors = [];

  for (const seed of seedLinks) {
    try {
      const fetched = await fetchEvidence(seed.href);
      crawledUrls.push({ href: seed.href, status: fetched.status, contentType: fetched.contentType, finalUrl: fetched.finalUrl });
      if (!fetched.ok) continue;
      if (DOCUMENT_RE.test(fetched.finalUrl || seed.href) || /pdf|word|excel|spreadsheet|csv/i.test(fetched.contentType)) {
        documentLinks.push({ href: fetched.finalUrl || seed.href, text: seed.text || "document" });
        continue;
      }
      const scored = fetched.links
        .map((link) => ({ ...link, score: scoreLink(link, row.base_procedure_key) }))
        .filter((link) => link.score >= 3)
        .sort((a, b) => b.score - a.score);
      for (const link of scored.slice(0, 8)) {
        deepEvidenceLinks.push({ href: link.href, text: link.text, score: link.score });
        if (DOCUMENT_RE.test(link.href)) documentLinks.push({ href: link.href, text: link.text });
        else if (ONLINE_RE.test(`${link.text} ${link.href}`)) onlineServiceLinks.push({ href: link.href, text: link.text });
      }
    } catch (err) {
      errors.push({ href: seed.href, error: String(err).slice(0, 180) });
    }
  }

  const status = await updateRow(
    row,
    descriptor,
    uniqueByHref(deepEvidenceLinks, 12),
    uniqueByHref(documentLinks, 10),
    uniqueByHref(onlineServiceLinks, 10),
    crawledUrls,
    errors,
  );
  return {
    vertex: hash(row.vertex_id),
    municipality: row.municipality_code,
    procedure: row.base_procedure_key,
    status,
    deep: uniqueByHref(deepEvidenceLinks, 12).length,
    docs: uniqueByHref(documentLinks, 10).length,
    online: uniqueByHref(onlineServiceLinks, 10).length,
    errors: errors.length,
  };
}

async function main() {
  const rows = await loadRows();
  let index = 0;
  const results = [];
  async function worker() {
    while (index < rows.length) {
      const row = rows[index++];
      const result = await processOne(row);
      results.push(result);
      console.log(JSON.stringify(result));
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, rows.length) }, () => worker()));
  console.error(JSON.stringify({
    processed: results.length,
    deepened: results.filter((r) => r.status === "candidate_deepened").length,
    docs: results.reduce((sum, r) => sum + r.docs, 0),
    online: results.reduce((sum, r) => sum + r.online, 0),
    errors: results.reduce((sum, r) => sum + r.errors, 0),
  }));
}

main().finally(async () => pool.end());
