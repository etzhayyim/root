#!/usr/bin/env node
/**
 * Recruit — Common Crawl job posting ingest.
 *
 * Queries the CC CDX Index API for ATS platform domains that serve
 * schema.org/JobPosting JSON-LD, fetches WARC records, extracts job
 * data, maps titles → ISCO codes, and inserts into vertex_job_posting.
 *
 * Targets known ATS platforms (no prohibited host fragments):
 *   boards.greenhouse.io  — Greenhouse (JSON-LD standard)
 *   jobs.lever.co          — Lever
 *   jobs.ashbyhq.com       — Ashby
 *   jobs.smartrecruiters.com — SmartRecruiters
 *   apply.workable.com     — Workable
 *   jobs.breezy.hr         — Breezy HR
 *   jobs.recruitee.com     — Recruitee
 *
 * Compliance:
 *   - PROHIBITED_HOST_FRAGMENTS enforced (no LinkedIn/Indeed/Glassdoor etc.)
 *   - source_license="crawl-public" (CC ToS, facts not creative)
 *   - employer_did left null (no vertex_legal_entity anchoring yet — resolved in Phase 2)
 *
 * Usage:
 *   node recruit-ingest-commoncrawl.mjs [--dry-run] [--crawl CC-MAIN-2024-51] [--limit 5000]
 */
import { writeFile, readFile } from "node:fs/promises";
import { createGunzip } from "node:zlib";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";

const KOTOBA_URL   = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const RECRUIT_DID = "did:web:recruit.etzhayyim.com";
const COLLECTION  = "com.etzhayyim.apps.recruit.jobPosting";

const args    = process.argv.slice(2);
const getArg  = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = k => args.includes(`--${k}`);

const DRY_RUN   = hasFlag("dry-run");
const CRAWL     = getArg("crawl", "CC-MAIN-2024-51");
const LIMIT     = parseInt(getArg("limit", "2000"), 10);
const BATCH     = parseInt(getArg("batch-size", "100"), 10);
const CHECKPOINT = "/tmp/cc-job-checkpoint.json";
const CC_BASE   = "https://data.commoncrawl.org";
const CDX_BASE  = `https://index.commoncrawl.org/${CRAWL}-index`;

// ── PROHIBITED host fragments (ADR-0027) ─────────────────────────────────────
const PROHIBITED = [
  "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
  "wantedly.com", "bizreach.jp", "monster.com", "careerbuilder.com",
  "simplyhired.com", "dice.com",
];

function isProhibited(url) {
  const u = url.toLowerCase();
  return PROHIBITED.some(h => u.includes(h));
}

// ── ATS domains to query ─────────────────────────────────────────────────────
const ATS_TARGETS = [
  { pattern: "boards.greenhouse.io/*",      country_hint: null },
  { pattern: "jobs.lever.co/*",             country_hint: null },
  { pattern: "jobs.ashbyhq.com/*",          country_hint: null },
  { pattern: "jobs.smartrecruiters.com/*",  country_hint: null },
  { pattern: "apply.workable.com/*/j/*",    country_hint: null },
  { pattern: "jobs.breezy.hr/*",            country_hint: null },
  { pattern: "jobs.recruitee.com/*",        country_hint: null },
];

// ── ISCO title → code mapping ────────────────────────────────────────────────
// Ordered from most specific to least. First match wins.
const ISCO_RULES = [
  // 2512 Software developers
  [/software\s+engineer|software\s+dev|full.?stack|backend\s+eng|frontend\s+eng|web\s+dev|mobile\s+dev|ios\s+dev|android\s+dev|flutter|react\s+native/i, "2512"],
  // 2511 Systems analysts
  [/data\s+engineer|data\s+architect|solutions\s+architect|systems\s+analyst|bi\s+engineer|analytics\s+engineer/i, "2511"],
  // 2519 ICT NEC (ML, DevOps, Platform)
  [/machine\s+learning|ml\s+eng|ai\s+eng|data\s+scientist|nlp\s+eng|devops|sre|site\s+reliab|platform\s+eng|cloud\s+eng|infrastructure\s+eng|secur|devsec/i, "2519"],
  // 2431 Advertising/marketing
  [/marketing\s+manager|growth\s+market|demand\s+gen|performance\s+market|seo|content\s+market|brand\s+market/i, "2431"],
  // 2433 Sales professionals
  [/sales\s+eng|account\s+exec|account\s+manager|business\s+dev|solutions\s+eng|pre.?sales/i, "2433"],
  // 2423 HR professionals
  [/hr\s+manager|hr\s+business|human\s+res|people\s+ops|talent\s+acqui|recruiter|recruiting\s+manager/i, "2423"],
  // 2421 Management consultants
  [/product\s+manager|product\s+owner|program\s+manager|project\s+manager|scrum\s+master|agile\s+coach/i, "2421"],
  // 2411 Accountants
  [/accountant|financial\s+analyst|finance\s+manager|controller|cfo|fp&a|treasury|audit/i, "2411"],
  // 2611 Lawyers
  [/lawyer|attorney|legal\s+counsel|in.?house\s+counsel|general\s+counsel|paralegal|compliance\s+officer/i, "2611"],
  // 2166 Graphic/multimedia designers
  [/ux\s+design|ui\s+design|product\s+design|visual\s+design|graphic\s+design|brand\s+design|motion\s+design/i, "2166"],
  // 2310 University teachers
  [/professor|lecturer|faculty|researcher\s+at|research\s+scientist|postdoc/i, "2310"],
  // 2211 Medical doctors
  [/physician|doctor|md\b|medical\s+officer|hospitalist|clinician|radiolog/i, "2211"],
  // 2221 Nursing
  [/nurse|nursing|rn\b|np\b/i, "2221"],
  // 1120 Managing directors
  [/ceo|chief\s+exec|managing\s+director|president\b|general\s+manager|vp\s+of|vice\s+president/i, "1120"],
  // 1330 R&D managers
  [/cto|chief\s+tech|chief\s+prod|vp\s+eng|vp\s+product|director\s+of\s+eng|director\s+of\s+prod/i, "1330"],
  // 3512 QA technicians
  [/qa\s+eng|quality\s+assur|test\s+eng|sdet|software\s+test/i, "3512"],
  // 3514 Customer support technicians
  [/customer\s+success|customer\s+support|technical\s+support|support\s+eng/i, "3514"],
  // 3323 Sales reps
  [/sales\s+rep|inside\s+sales|outbound\s+sales|sdrbdr|account\s+dev/i, "3323"],
  // 4120 Administrative clerks
  [/executive\s+assist|office\s+manager|admin\s+coord|office\s+coord|administrative/i, "4120"],
  // 5222 Shop salespersons
  [/retail\s+manager|store\s+manager|retail\s+assoc/i, "5222"],
  // 7 Craft/trades
  [/electrician|plumber|carpenter|welder|machinist|tradesperson|construction\s+worker/i, "7"],
  // 8 Plant operators
  [/machine\s+operator|production\s+operator|assembly\s+tech|manufacturing\s+tech/i, "8"],
];

function titleToIsco(title) {
  if (!title) return null;
  for (const [re, code] of ISCO_RULES) {
    if (re.test(title)) return code;
  }
  return null;
}

// ── Extract JSON-LD JobPosting from HTML ─────────────────────────────────────
function extractJobPostings(html, sourceUrl) {
  const jobs = [];
  // Find all <script type="application/ld+json"> blocks
  const re = /<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    try {
      const raw = m[1].trim();
      const data = JSON.parse(raw);
      const items = Array.isArray(data) ? data : [data];
      for (const item of items) {
        if (!item || (item["@type"] !== "JobPosting" && item.type !== "JobPosting")) continue;
        // Normalise
        const title       = item.title || item.name || "";
        const company     = item.hiringOrganization?.name || item.hiringOrganization || "";
        const country     = item.jobLocation?.address?.addressCountry
                         || item.jobLocation?.[0]?.address?.addressCountry
                         || null;
        const location    = item.jobLocation?.address?.addressLocality
                         || item.jobLocation?.[0]?.address?.addressLocality
                         || null;
        const remote      = item.jobLocationType === "TELECOMMUTE"
                         || /remote/i.test(JSON.stringify(item.jobLocationType ?? ""));
        const empType     = Array.isArray(item.employmentType)
                         ? item.employmentType[0] : (item.employmentType || null);
        const salBase     = item.baseSalary;
        const salMin      = salBase?.value?.minValue ?? salBase?.minValue ?? null;
        const salMax      = salBase?.value?.maxValue ?? salBase?.maxValue ?? salMin;
        const salCur      = salBase?.currency ?? null;
        const postedAt    = item.datePosted || null;
        const expiresAt   = item.validThrough || null;
        const desc        = typeof item.description === "string"
                         ? item.description.replace(/<[^>]+>/g, " ").slice(0, 2000)
                         : null;
        if (!title) continue;
        if (isProhibited(sourceUrl)) continue;
        jobs.push({ title, company, country, location, remote, empType,
                    salMin, salMax, salCur, postedAt, expiresAt, desc });
      }
    } catch { /* skip malformed JSON-LD */ }
  }
  return jobs;
}

// ── Fetch CC CDX index for a domain pattern ───────────────────────────────────
async function queryCdx(pattern, limit = 500) {
  const url = `${CDX_BASE}?url=${encodeURIComponent(pattern)}&output=json&limit=${limit}&filter=status:200&fl=url,filename,offset,length,status`;
  const res = await fetch(url, {
    headers: { "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)" },
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    if (res.status === 404) return []; // no results for this crawl
    throw new Error(`CDX HTTP ${res.status} for ${pattern}`);
  }
  const text = await res.text();
  return text.trim().split("\n").filter(Boolean).map(line => {
    try { return JSON.parse(line); } catch { return null; }
  }).filter(Boolean);
}

// ── Fetch + decompress a WARC record ─────────────────────────────────────────
async function fetchWarcRecord(filename, offset, length) {
  const rangeEnd = parseInt(offset) + parseInt(length) - 1;
  const res = await fetch(`${CC_BASE}/${filename}`, {
    headers: {
      "Range": `bytes=${offset}-${rangeEnd}`,
      "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)",
    },
    signal: AbortSignal.timeout(20000),
  });
  if (!res.ok) throw new Error(`WARC fetch HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());

  // Decompress gzip
  return new Promise((resolve, reject) => {
    const chunks = [];
    const gunzip = createGunzip();
    gunzip.on("data", c => chunks.push(c));
    gunzip.on("end", () => resolve(Buffer.concat(chunks).toString("utf8", 0, 512_000)));
    gunzip.on("error", reject);
    gunzip.write(buf);
    gunzip.end();
  });
}

// Extract HTTP body from WARC payload
function extractHttpBody(warc) {
  const sep = "\r\n\r\n";
  const warcHeaderEnd = warc.indexOf(sep);
  if (warcHeaderEnd === -1) return null;
  const afterWarcHeader = warc.slice(warcHeaderEnd + sep.length);
  const httpHeaderEnd = afterWarcHeader.indexOf(sep);
  if (httpHeaderEnd === -1) return afterWarcHeader;
  return afterWarcHeader.slice(httpHeaderEnd + sep.length);
}

// ── pg pool ──────────────────────────────────────────────────────────────────
let _pool = null;
async function pool() {
  if (_pool) return _pool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60_000 });
  return _pool;
}
async function query(sql, vals = []) { const db = await pool(); return db.query(sql, vals); }

function makeid(url, title) {
  const h = Buffer.from(`${url}:${title}`).toString("base64url").slice(0, 32);
  return `cc:${CRAWL}:${h}`;
}

// ── Batch insert vertex_job_posting ──────────────────────────────────────────
const COLS = [
  "vertex_id","rkey","repo","label","source","source_license","source_url",
  "title","description","employer_name","isco_code","country","location",
  "remote_allowed","employment_type","salary_min","salary_max","salary_currency",
  "posted_at","expires_at","ingested_at",
];

async function batchInsert(rows) {
  if (rows.length === 0) return;
  const ph = []; const vals = []; let p = 1;
  for (const row of rows) {
    ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
    vals.push(...row);
  }
  await query(
    `INSERT INTO vertex_job_posting (${COLS.join(",")}) VALUES ${ph.join(",")}`,
    vals
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  const now = new Date().toISOString();
  console.log(`[cc-jobs] crawl=${CRAWL} limit=${LIMIT} dry-run=${DRY_RUN}`);

  // Load checkpoint
  let seen = new Set();
  try {
    const cp = JSON.parse(await readFile(CHECKPOINT, "utf8"));
    seen = new Set(cp.seen ?? []);
    console.log(`[cc-jobs] checkpoint: ${seen.size} already processed`);
  } catch { /* no checkpoint yet */ }

  let totalFetched = 0, totalInserted = 0, totalSkipped = 0;
  const insertBuffer = [];

  const perTarget = Math.ceil(LIMIT / ATS_TARGETS.length);

  for (const { pattern } of ATS_TARGETS) {
    console.log(`[cc-jobs] querying CDX: ${pattern} (limit=${perTarget})`);
    let cdxRecords;
    try {
      cdxRecords = await queryCdx(pattern, perTarget);
    } catch (e) {
      console.warn(`[cc-jobs] CDX query failed for ${pattern}: ${e.message}`);
      continue;
    }
    console.log(`[cc-jobs]   found ${cdxRecords.length} CDX records`);

    for (const rec of cdxRecords) {
      if (seen.has(rec.url)) { totalSkipped++; continue; }
      if (isProhibited(rec.url)) { seen.add(rec.url); totalSkipped++; continue; }

      // Throttle: 150ms between requests to be a polite bot
      await new Promise(r => setTimeout(r, 150));

      let html = null;
      try {
        const warc = await fetchWarcRecord(rec.filename, rec.offset, rec.length);
        html = extractHttpBody(warc);
      } catch (e) {
        console.warn(`[cc-jobs]   WARC fetch failed for ${rec.url}: ${e.message}`);
        seen.add(rec.url);
        continue;
      }

      if (!html) { seen.add(rec.url); continue; }

      const jobs = extractJobPostings(html, rec.url);
      totalFetched++;
      seen.add(rec.url);

      for (const j of jobs) {
        const vid   = makeid(rec.url, j.title);
        const rkey  = vid.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 128);
        const isco  = titleToIsco(j.title);
        insertBuffer.push([
          vid, rkey, RECRUIT_DID, COLLECTION,
          "commoncrawl", "crawl-public", rec.url,
          j.title, j.desc, j.company, isco,
          j.country, j.location, j.remote ?? false, j.empType ?? null,
          j.salMin, j.salMax, j.salCur,
          j.postedAt, j.expiresAt, now,
        ]);
      }

      // Flush batch
      if (insertBuffer.length >= BATCH) {
        if (!DRY_RUN) {
          try { await batchInsert(insertBuffer); } catch (e) {
            console.warn(`[cc-jobs] insert failed (batch): ${e.message}`);
          }
        }
        totalInserted += insertBuffer.length;
        insertBuffer.length = 0;
      }

      if (totalFetched % 50 === 0) {
        console.log(`[cc-jobs] fetched=${totalFetched} inserted=${totalInserted} skipped=${totalSkipped}`);
        await writeFile(CHECKPOINT, JSON.stringify({ seen: [...seen].slice(-50000) }));
      }

      if (totalFetched + totalInserted >= LIMIT) break;
    }

    if (totalFetched + totalInserted >= LIMIT) break;
  }

  // Final flush
  if (insertBuffer.length > 0) {
    if (!DRY_RUN) {
      try { await batchInsert(insertBuffer); } catch (e) {
        console.warn(`[cc-jobs] insert failed (final batch): ${e.message}`);
      }
    }
    totalInserted += insertBuffer.length;
  }

  console.log(`[cc-jobs] done  fetched=${totalFetched} inserted=${totalInserted} skipped=${totalSkipped}`);

  if (!DRY_RUN) {
    const { rows } = await query(`SELECT COUNT(*) AS cnt FROM vertex_job_posting WHERE source='commoncrawl'`);
    console.log(`[cc-jobs] vertex_job_posting[commoncrawl] total=${rows[0].cnt}`);
  }

  await writeFile("/tmp/cc-jobs-summary.json", JSON.stringify({
    crawl: CRAWL, fetched: totalFetched, inserted: totalInserted, skipped: totalSkipped, dry_run: DRY_RUN,
  }, null, 2));

  if (_pool) await _pool.end();
}

main().catch(e => { console.error(e); process.exit(1); });
