#!/usr/bin/env node
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
const DB_RETRIES = Number(process.env.DB_RETRIES || process.argv.find((a) => a.startsWith("--db-retries="))?.split("=")[1] || 8);
const SAFE_LIMIT = Math.max(1, Math.min(10000, Math.trunc(Number.isFinite(LIMIT) ? LIMIT : 10000)));

const pool = new pg.Pool({ connectionString: DATABASE_URL, max: 4 });

const LANG = {
  "as-IN": ["Assamese", "Beng"],
  "bn-IN": ["Bengali", "Beng"],
  "en-IN": ["English", "Latn"],
  "gu-IN": ["Gujarati", "Gujr"],
  "hi-IN": ["Hindi", "Deva"],
  "kn-IN": ["Kannada", "Knda"],
  "kok-IN": ["Konkani", "Deva"],
  "ml-IN": ["Malayalam", "Mlym"],
  "mr-IN": ["Marathi", "Deva"],
  "mni-IN": ["Meitei", "Mtei"],
  "ne-IN": ["Nepali", "Deva"],
  "or-IN": ["Odia", "Orya"],
  "pa-IN": ["Punjabi", "Guru"],
  "ta-IN": ["Tamil", "Taml"],
  "te-IN": ["Telugu", "Telu"],
  "ur-IN": ["Urdu", "Arab"],
};

const ADMIN1_MAJOR_LANGUAGES = new Map([
  ["A&N Islands", ["en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN"]],
  ["Andhra Pradesh", ["te-IN", "en-IN", "ur-IN"]],
  ["Arunachal Pradesh", ["en-IN", "hi-IN"]],
  ["Assam", ["as-IN", "bn-IN", "en-IN", "hi-IN"]],
  ["Bihar", ["hi-IN", "ur-IN", "bn-IN"]],
  ["Chandigarh", ["en-IN", "hi-IN", "pa-IN"]],
  ["Chhattisgarh", ["hi-IN", "en-IN"]],
  ["DNH & DD", ["gu-IN", "hi-IN", "en-IN"]],
  ["Delhi", ["hi-IN", "en-IN", "pa-IN", "ur-IN"]],
  ["Goa", ["kok-IN", "en-IN", "mr-IN", "hi-IN"]],
  ["Gujarat", ["gu-IN", "en-IN", "hi-IN"]],
  ["Haryana", ["hi-IN", "en-IN", "pa-IN"]],
  ["Himachal Pradesh", ["hi-IN", "en-IN"]],
  ["Jammu & Kashmir", ["ur-IN", "hi-IN", "en-IN"]],
  ["Jharkhand", ["hi-IN", "en-IN", "bn-IN"]],
  ["Karnataka", ["kn-IN", "en-IN", "hi-IN"]],
  ["Kerala", ["ml-IN", "en-IN", "ta-IN"]],
  ["Ladakh", ["en-IN", "hi-IN", "ur-IN"]],
  ["Lakshadweep", ["ml-IN", "en-IN"]],
  ["Madhya Pradesh", ["hi-IN", "en-IN"]],
  ["Maharashtra", ["mr-IN", "en-IN", "hi-IN"]],
  ["Manipur", ["mni-IN", "en-IN", "hi-IN"]],
  ["Meghalaya", ["en-IN", "hi-IN", "bn-IN"]],
  ["Mizoram", ["en-IN", "hi-IN"]],
  ["Nagaland", ["en-IN", "hi-IN"]],
  ["Odisha", ["or-IN", "en-IN", "hi-IN"]],
  ["Puducherry", ["ta-IN", "en-IN", "te-IN", "ml-IN"]],
  ["Punjab", ["pa-IN", "en-IN", "hi-IN"]],
  ["Rajasthan", ["hi-IN", "en-IN"]],
  ["Sikkim", ["en-IN", "ne-IN", "hi-IN"]],
  ["Tamil Nadu", ["ta-IN", "en-IN"]],
  ["Telangana", ["te-IN", "ur-IN", "en-IN", "hi-IN"]],
  ["Tripura", ["bn-IN", "en-IN", "hi-IN"]],
  ["Uttar Pradesh", ["hi-IN", "ur-IN", "en-IN"]],
  ["Uttarakhand", ["hi-IN", "en-IN"]],
  ["West Bengal", ["bn-IN", "en-IN", "hi-IN", "ur-IN"]],
]);

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function slug(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
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

async function loadMunicipalities() {
  const { rows } = await pool.query(
    `SELECT municipality_code, prefecture, city, site_url, "actorDid" AS actor_did
     FROM vertex_gov_municipality
     WHERE municipality_code IS NOT NULL
     ORDER BY prefecture, city
     LIMIT ${SAFE_LIMIT}`,
  );
  return rows;
}

function sqlString(s) {
  return `'${String(s ?? "").replace(/'/g, "''")}'`;
}

function mappingValuesSql() {
  const rows = [];
  let ord = 0;
  for (const [admin1, locales] of ADMIN1_MAJOR_LANGUAGES.entries()) {
    for (const locale of locales) {
      const [languageName, scriptTag] = LANG[locale] || [locale, ""];
      rows.push(`(${sqlString(admin1)}, ${sqlString(locale)}, ${sqlString(languageName)}, ${sqlString(scriptTag)}, ${ord++})`);
    }
  }
  return rows.join(",\n      ");
}

async function bulkInsertTargets() {
  const values = mappingValuesSql();
  return await withDbRetry("major-language:bulk", async (client) => {
    const result = await client.query(
      `INSERT INTO vertex_gov_form_language_variant (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        form_key, format_key, country_iso3, admin1_name, municipality_code,
        locale, language_name, script_tag, translation_status, source_url,
        descriptor_json, last_verified_at, created_at, org_id, user_id, actor_id
      )
      SELECT
        CONCAT('at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.formLanguageVariant/ind-', m.municipality_code, '-major-', REPLACE(l.locale, '-', '-')),
        20260427004000 + ROW_NUMBER() OVER (ORDER BY m.prefecture, m.city, l.ordinal),
        DATE '2026-04-27',
        1,
        COALESCE(m."actorDid", 'did:web:gov.etzhayyim.com'),
        'local-site',
        '',
        'IND',
        m.prefecture,
        m.municipality_code,
        l.locale,
        l.language_name,
        l.script_tag,
        'target_required',
        COALESCE(m.site_url, ''),
        CONCAT('{"source":"admin1_major_language_policy","evidence":"coverage_target","municipalityName":"', COALESCE(m.city, ''), '","admin1Name":"', COALESCE(m.prefecture, ''), '"}'),
        '2026-04-27',
        $1,
        'ind',
        'system',
        'sys.gov.local.major.language.seed'
      FROM vertex_gov_municipality m
      JOIN (
        VALUES
        ${values}
      ) AS l(admin1_name, locale, language_name, script_tag, ordinal)
        ON l.admin1_name = m.prefecture
      WHERE m.municipality_code IS NOT NULL
        AND NOT EXISTS (
          SELECT 1
          FROM vertex_gov_form_language_variant existing
          WHERE existing.country_iso3 = 'IND'
            AND existing.municipality_code = m.municipality_code
            AND existing.locale = l.locale
        )
      LIMIT ${SAFE_LIMIT}`,
      [nowIso()],
    );
    return { inserted: result.rowCount };
  });
}

async function main() {
  const municipalities = await loadMunicipalities();
  const result = await bulkInsertTargets();
  console.log(JSON.stringify(result));
  console.error(JSON.stringify({
    municipalities: municipalities.length,
    inserted: result.inserted,
  }));
}

main().finally(async () => pool.end());
