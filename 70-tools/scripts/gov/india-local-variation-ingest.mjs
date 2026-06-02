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

const LIMIT = Number(process.env.LIMIT || process.argv.find((a) => a.startsWith("--limit="))?.split("=")[1] || 190);
const CONCURRENCY = Number(process.env.CONCURRENCY || process.argv.find((a) => a.startsWith("--concurrency="))?.split("=")[1] || 6);
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS || process.argv.find((a) => a.startsWith("--timeout-ms="))?.split("=")[1] || 8000);
const SAFE_LIMIT = Math.max(1, Math.min(10000, Math.trunc(Number.isFinite(LIMIT) ? LIMIT : 190)));
const DB_RETRIES = Number(process.env.DB_RETRIES || process.argv.find((a) => a.startsWith("--db-retries="))?.split("=")[1] || 8);

const PROCEDURE_PATTERNS = [
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
];

const LANGUAGE_PATTERNS = [
  ["en-IN", "English", "Latn", /\b(en|english)\b/i],
  ["hi-IN", "Hindi", "Deva", /\b(hi|hindi|हिन्दी|हिंदी)\b/i],
  ["bn-IN", "Bengali", "Beng", /\b(bn|bengali|bangla|বাংলা)\b/i],
  ["gu-IN", "Gujarati", "Gujr", /\b(gu|gujarati|ગુજરાતી)\b/i],
  ["kn-IN", "Kannada", "Knda", /\b(kn|kannada|ಕನ್ನಡ)\b/i],
  ["ml-IN", "Malayalam", "Mlym", /\b(ml|malayalam|മലയാളം)\b/i],
  ["mr-IN", "Marathi", "Deva", /\b(mr|marathi|मराठी)\b/i],
  ["or-IN", "Odia", "Orya", /\b(or|odia|oriya|ଓଡ଼ିଆ)\b/i],
  ["pa-IN", "Punjabi", "Guru", /\b(pa|punjabi|ਪੰਜਾਬੀ)\b/i],
  ["ta-IN", "Tamil", "Taml", /\b(ta|tamil|தமிழ்)\b/i],
  ["te-IN", "Telugu", "Telu", /\b(te|telugu|తెలుగు)\b/i],
  ["ur-IN", "Urdu", "Arab", /\b(ur|urdu|اردو)\b/i],
];

const LOCALE_ALIASES = new Map([
  ["en", "en-IN"],
  ["en-us", "en-IN"],
  ["en-gb", "en-IN"],
  ["hi", "hi-IN"],
  ["bn", "bn-IN"],
  ["gu", "gu-IN"],
  ["kn", "kn-IN"],
  ["ml", "ml-IN"],
  ["mr", "mr-IN"],
  ["or", "or-IN"],
  ["pa", "pa-IN"],
  ["ta", "ta-IN"],
  ["te", "te-IN"],
  ["ur", "ur-IN"],
]);

const LANGUAGE_BY_LOCALE = new Map(LANGUAGE_PATTERNS.map(([locale, language, script]) => [locale, { locale, language, script }]));

function normalizeLocale(raw) {
  const tag = String(raw || "").trim().replace("_", "-");
  if (!/^[a-z]{2,3}(-[a-z]{2})?$/i.test(tag)) return null;
  const lower = tag.toLowerCase();
  const mapped = LOCALE_ALIASES.get(lower) || `${lower.slice(0, 2)}-${lower.slice(-2).toUpperCase()}`;
  if (!LANGUAGE_BY_LOCALE.has(mapped)) return null;
  return LANGUAGE_BY_LOCALE.get(mapped);
}

const pool = new pg.Pool({ connectionString: DATABASE_URL, max: CONCURRENCY + 2 });

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function slug(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "unknown";
}

function hash(s) {
  return crypto.createHash("sha256").update(s).digest("hex").slice(0, 24);
}

function absUrl(base, href) {
  try {
    return new URL(href, base).toString();
  } catch {
    return "";
  }
}

function extractLinks(html, baseUrl) {
  const links = [];
  const re = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(html)) && links.length < 1000) {
    const href = absUrl(baseUrl, m[1]);
    if (!href || !href.startsWith("http")) continue;
    const text = m[2].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 200);
    links.push({ href, text });
  }
  return links;
}

function detectLanguages(html, links) {
  const evidence = new Map();
  const htmlLang = html.match(/<html[^>]*\blang\s*=\s*["']([^"']+)["']/i)?.[1];
  const normalizedHtmlLang = normalizeLocale(htmlLang);
  if (normalizedHtmlLang) evidence.set(normalizedHtmlLang.locale, { ...normalizedHtmlLang, evidence: "html.lang" });
  for (const m of html.matchAll(/\bhreflang\s*=\s*["']([^"']+)["']/gi)) {
    const normalized = normalizeLocale(m[1]);
    if (normalized) evidence.set(normalized.locale, { ...normalized, evidence: "hreflang" });
  }
  const text = `${html.slice(0, 50000)} ${links.map((l) => l.text).join(" ")}`;
  for (const [locale, language, script, pattern] of LANGUAGE_PATTERNS) {
    if (pattern.test(text)) {
      evidence.set(locale, { locale, language, script, evidence: "keyword" });
    }
  }
  if (evidence.size === 0) evidence.set("en-IN", { locale: "en-IN", language: "English", script: "Latn", evidence: "default" });
  return [...evidence.values()].slice(0, 8);
}

function detectProcedures(links) {
  const byKind = new Map();
  for (const link of links) {
    const hay = `${link.text} ${link.href}`.replace(/[-_/%?=&.]+/g, " ");
    for (const [kind, pattern] of PROCEDURE_PATTERNS) {
      if (!pattern.test(hay)) continue;
      const arr = byKind.get(kind) || [];
      if (arr.length < 5) arr.push(link);
      byKind.set(kind, arr);
    }
  }
  return [...byKind.entries()].map(([kind, evidenceLinks]) => ({ kind, evidenceLinks })).slice(0, 12);
}

async function fetchSite(url) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      signal: ac.signal,
      headers: {
        "User-Agent": "etzhayyim/1.0 government local variation audit (+https://etzhayyim.com)",
        "Accept": "text/html,application/xhtml+xml",
      },
      redirect: "follow",
    });
    const contentType = resp.headers.get("content-type") || "";
    const text = await resp.text();
    return { ok: resp.ok, status: resp.status, contentType, finalUrl: resp.url, text };
  } finally {
    clearTimeout(t);
  }
}

async function loadMunicipalities() {
  const { rows } = await pool.query(
    `SELECT municipality_code, prefecture, city, site_url, "actorDid" AS actor_did
     FROM vertex_gov_municipality
     WHERE site_url IS NOT NULL AND municipality_code IS NOT NULL
     ORDER BY prefecture, city
     LIMIT ${SAFE_LIMIT}`,
  );
  return rows;
}

async function insertLanguage(client, m, lang, sourceUrl) {
  const formKey = "local-site";
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.formLanguageVariant/ind-${m.municipality_code}-${slug(lang.locale)}`;
  await client.query(`DELETE FROM vertex_gov_form_language_variant WHERE vertex_id = $1`, [vertexId]);
  await client.query(
    `INSERT INTO vertex_gov_form_language_variant (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      form_key, format_key, country_iso3, admin1_name, municipality_code,
      locale, language_name, script_tag, translation_status, source_url,
      descriptor_json, last_verified_at, created_at, org_id, user_id, actor_id
    ) VALUES ($1,$2,$3::date,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)`,
    [
      vertexId,
      Date.now(),
      "2026-04-27",
      1,
      m.actor_did || "did:web:gov.etzhayyim.com",
      formKey,
      "",
      "IND",
      m.prefecture || "",
      m.municipality_code,
      lang.locale,
      lang.language,
      lang.script || "",
      lang.evidence === "default" ? "inferred_default" : "source_detected",
      sourceUrl,
      JSON.stringify({ evidence: lang.evidence, municipalityName: m.city }),
      "2026-04-27",
      nowIso(),
      "ind",
      "system",
      "sys.gov.local.variation.ingest",
    ],
  );
}

async function insertProcedure(client, m, p, sourceUrl, languages) {
  const procedureKey = `ind.local.${slug(p.kind)}`;
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.procedureVariant/ind-${m.municipality_code}-${slug(p.kind)}-${hash(sourceUrl)}`;
  const evidenceUrls = p.evidenceLinks.map((l) => l.href);
  await client.query(`DELETE FROM vertex_gov_procedure_variant WHERE vertex_id = $1`, [vertexId]);
  await client.query(
    `INSERT INTO vertex_gov_procedure_variant (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      procedure_key, base_procedure_key, country_iso3, admin1_name,
      municipality_code, municipality_name, locality_scope, actor_did,
      gov_org_key, form_key, format_key, language_tags, script_tags,
      portal_url, source_url, source_kind, variant_status, descriptor_json,
      last_verified_at, created_at, org_id, user_id, actor_id
    ) VALUES ($1,$2,$3::date,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28)`,
    [
      vertexId,
      Date.now(),
      "2026-04-27",
      1,
      m.actor_did || "did:web:gov.etzhayyim.com",
      procedureKey,
      p.kind,
      "IND",
      m.prefecture || "",
      m.municipality_code,
      m.city || "",
      "municipality",
      m.actor_did || "",
      m.municipality_code,
      "",
      "",
      languages.map((l) => l.locale).join(","),
      [...new Set(languages.map((l) => l.script).filter(Boolean))].join(","),
      p.evidenceLinks[0]?.href || sourceUrl,
      sourceUrl,
      "municipal_site_detected",
      "candidate_detected",
      JSON.stringify({ evidenceLinks: p.evidenceLinks, municipalityName: m.city }),
      "2026-04-27",
      nowIso(),
      "ind",
      "system",
      "sys.gov.local.variation.ingest",
    ],
  );
}

async function markGap(client, m, status, reason) {
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.localVariationGap/ind-${m.municipality_code}`;
  await client.query(
    `DELETE FROM vertex_gov_local_variation_gap WHERE vertex_id = $1`,
    [vertexId],
  );
  await client.query(
    `INSERT INTO vertex_gov_local_variation_gap (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      country_iso3, admin1_name, municipality_code, municipality_name, site_url,
      gap_kind, gap_status, reason, created_at, org_id, user_id, actor_id
    ) VALUES ($1,$2,$3::date,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)`,
    [
      vertexId,
      Date.now(),
      "2026-04-27",
      1,
      m.actor_did || "did:web:gov.etzhayyim.com",
      "IND",
      m.prefecture || "",
      m.municipality_code,
      m.city || "",
      m.site_url || "",
      "procedure_form_language",
      status,
      reason,
      nowIso(),
      "ind",
      "system",
      "sys.gov.local.variation.ingest",
    ],
  );
}

async function clearMunicipalityCandidates(client, m) {
  await client.query(
    `DELETE FROM vertex_gov_form_language_variant
     WHERE country_iso3 = 'IND'
       AND municipality_code = $1
       AND form_key = 'local-site'`,
    [m.municipality_code],
  );
  await client.query(
    `DELETE FROM vertex_gov_procedure_variant
     WHERE country_iso3 = 'IND'
       AND locality_scope = 'municipality'
       AND municipality_code = $1
       AND source_kind = 'municipal_site_detected'`,
    [m.municipality_code],
  );
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
      await client.query("BEGIN");
      const result = await fn(client);
      await client.query("COMMIT");
      return result;
    } catch (err) {
      lastErr = err;
      try {
        await client.query("ROLLBACK");
      } catch {}
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

async function processOne(m) {
  try {
    const fetched = await fetchSite(m.site_url);
    if (!fetched.ok || !/html/i.test(fetched.contentType)) {
      await withDbRetry(`mark-fetch-failed:${m.municipality_code}`, (client) =>
        markGap(client, m, "fetch_failed", `HTTP ${fetched.status} ${fetched.contentType}`),
      );
      return { code: m.municipality_code, ok: false, status: "fetch_failed" };
    }
    const links = extractLinks(fetched.text, fetched.finalUrl || m.site_url);
    const languages = detectLanguages(fetched.text, links);
    const procedures = detectProcedures(links);
    const gapStatus = procedures.length ? "candidate_detected" : "language_only";
    await withDbRetry(`write-candidates:${m.municipality_code}`, async (client) => {
      await clearMunicipalityCandidates(client, m);
      for (const lang of languages) await insertLanguage(client, m, lang, fetched.finalUrl);
      for (const p of procedures) await insertProcedure(client, m, p, fetched.finalUrl, languages);
      await markGap(client, m, gapStatus, `${procedures.length} procedure candidates, ${languages.length} language candidates`);
    });
    return { code: m.municipality_code, ok: true, procedures: procedures.length, languages: languages.length };
  } catch (err) {
    try {
      await withDbRetry(`mark-fetch-error:${m.municipality_code}`, (client) =>
        markGap(client, m, "fetch_error", String(err).slice(0, 240)),
      );
    } catch {}
    return { code: m.municipality_code, ok: false, status: "fetch_error", error: String(err).slice(0, 160) };
  }
}

async function main() {
  const municipalities = await loadMunicipalities();
  let index = 0;
  const results = [];
  async function worker() {
    while (index < municipalities.length) {
      const m = municipalities[index++];
      const r = await processOne(m);
      results.push(r);
      console.log(JSON.stringify(r));
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, municipalities.length) }, () => worker()));
  const ok = results.filter((r) => r.ok).length;
  const procedures = results.reduce((sum, r) => sum + (r.procedures || 0), 0);
  const languages = results.reduce((sum, r) => sum + (r.languages || 0), 0);
  console.error(JSON.stringify({ processed: results.length, ok, procedures, languages }));
}

main().finally(async () => pool.end());
