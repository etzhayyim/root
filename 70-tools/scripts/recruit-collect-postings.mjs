#!/usr/bin/env node
/**
 * Recruit — Job posting collector framework.
 *
 * Compliance gates:
 *   1. Source allowlist: usajobs | jobbank | eures | hellowork
 *      (matches recruit actor manifest governance.dataSources.allowed)
 *   2. Employer-anchor required: every posting MUST resolve to a
 *      vertex_legal_entity row via LEI / JP 法人番号 / SIREN / etc.
 *      Postings without employer match are SKIPPED (counted but not written).
 *
 * Source credentials (read from env, never logged):
 *   USAJOBS_KEY        — User-agent + Authorization-Key (https://developer.usajobs.gov/)
 *   USAJOBS_USER_AGENT — registered email
 *   EURES_KEY          — partnership credential (per-country)
 *   HELLOWORK_KEY      — JP 厚労省 API subscription
 *
 * Usage:
 *   node recruit-collect-postings.mjs --source usajobs --keyword "software" --limit 100
 *   node recruit-collect-postings.mjs --source usajobs --dry-run --limit 5
 */
import { writeFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const COLLECTOR_DID = "did:web:recruit.etzhayyim.com";
const PROGRESS_FILE = "/tmp/recruit-postings-progress.json";

const ALLOWED_SOURCES = ["usajobs", "jobbank", "eures", "hellowork"];
const PROHIBITED_HOST_FRAGMENTS = [
  "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
  "wantedly.com", "bizreach.jp",
];

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const hasFlag = (k) => args.includes(`--${k}`);

const SOURCE = getArg("source");
const KEYWORD = getArg("keyword", "");
const LIMIT = parseInt(getArg("limit", "100"), 10);
const PAGES = parseInt(getArg("pages", "1"), 10);
const DRY_RUN = hasFlag("dry-run");

if (!ALLOWED_SOURCES.includes(SOURCE)) {
  console.error(`error: --source must be one of: ${ALLOWED_SOURCES.join(", ")}`);
  process.exit(2);
}

// ── Compliance: hard-fail on prohibited domain anywhere in URL ────────────
function assertNotProhibited(url) {
  if (!url) return;
  for (const frag of PROHIBITED_HOST_FRAGMENTS) {
    if (url.toLowerCase().includes(frag)) {
      throw new Error(`compliance violation: prohibited domain detected in URL ${url} (fragment=${frag}). Source partnership required before ingest.`);
    }
  }
}

// ── pg pool ───────────────────────────────────────────────────────────────
let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 30000 });
  return _pgPool;
}

// ── Employer anchor resolver ──────────────────────────────────────────────
async function resolveEmployer({ name, lei, registryId, country }) {
  const pg = await pool();
  if (lei) {
    const r = await pg.query("SELECT vertex_id, name FROM vertex_legal_entity WHERE lei = $1 LIMIT 1", [lei]);
    if (r.rows[0]) return { did: r.rows[0].vertex_id, name: r.rows[0].name, registryId: lei };
  }
  if (registryId && country) {
    const r = await pg.query(
      "SELECT vertex_id, name FROM vertex_legal_entity WHERE source_record_id = $1 AND country = $2 LIMIT 1",
      [registryId, country],
    );
    if (r.rows[0]) return { did: r.rows[0].vertex_id, name: r.rows[0].name, registryId };
  }
  if (name) {
    const r = await pg.query(
      "SELECT vertex_id, name FROM vertex_legal_entity WHERE lower(name) = lower($1) LIMIT 1",
      [name],
    );
    if (r.rows[0]) return { did: r.rows[0].vertex_id, name: r.rows[0].name, registryId: null };
  }
  return null;
}

// ── Source: USAJOBS ───────────────────────────────────────────────────────
async function fetchUsaJobs({ keyword, page }) {
  const key = process.env.USAJOBS_KEY;
  const ua = process.env.USAJOBS_USER_AGENT;
  if (!key || !ua) {
    throw new Error("USAJOBS_KEY and USAJOBS_USER_AGENT env vars required (free signup at https://developer.usajobs.gov/)");
  }
  const url = new URL("https://data.usajobs.gov/api/Search");
  if (keyword) url.searchParams.set("Keyword", keyword);
  url.searchParams.set("ResultsPerPage", "25");
  url.searchParams.set("Page", String(page));
  const res = await fetch(url, {
    headers: {
      "Host": "data.usajobs.gov",
      "User-Agent": ua,
      "Authorization-Key": key,
    },
  });
  if (!res.ok) throw new Error(`USAJOBS HTTP ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const j = await res.json();
  const items = j?.SearchResult?.SearchResultItems ?? [];
  return items.map((it) => {
    const d = it.MatchedObjectDescriptor ?? {};
    return {
      sourceId: it.MatchedObjectId,
      sourceUrl: d.PositionURI,
      title: d.PositionTitle,
      description: (d.QualificationSummary ?? "").slice(0, 4000),
      employer: {
        name: d.OrganizationName,
        registryId: d.DepartmentName, // US federal agency code
        country: "USA",
      },
      onetSocCode: d.JobCategory?.[0]?.Code,
      country: "USA",
      location: (d.PositionLocationDisplay ?? "").slice(0, 200),
      employmentType: d.PositionSchedule?.[0]?.Name,
      salaryMin: parseFloat(d.PositionRemuneration?.[0]?.MinimumRange ?? "0") || null,
      salaryMax: parseFloat(d.PositionRemuneration?.[0]?.MaximumRange ?? "0") || null,
      salaryCurrency: d.PositionRemuneration?.[0]?.Currency ?? "USD",
      postedAt: d.PublicationStartDate,
      expiresAt: d.ApplicationCloseDate,
    };
  });
}

const FETCHERS = {
  usajobs: fetchUsaJobs,
  jobbank: async () => { throw new Error("jobbank: collector not yet implemented (open feed not located 2026-04-14)"); },
  eures: async () => { throw new Error("eures: collector blocked by robots.txt (requires partnership credential)"); },
  hellowork: async () => { throw new Error("hellowork: collector requires JP 厚労省 API subscription"); },
};

// ── Writer ────────────────────────────────────────────────────────────────
async function writePostings(postings) {
  const cols = [
    "vertex_id", "rkey", "repo", "label",
    "source", "source_license", "source_id", "source_url",
    "title", "description",
    "employer_did", "employer_name", "employer_registry_id",
    "isco_code", "onet_soc_code",
    "country", "location", "remote_allowed", "employment_type",
    "salary_min", "salary_max", "salary_currency",
    "posted_at", "expires_at", "ingested_at",
  ];
  const ph = []; const vals = []; let p = 1;
  const now = new Date().toISOString();
  for (const post of postings) {
    const vid = `posting:${SOURCE}:${post.sourceId}`;
    const rkey = `${SOURCE}-${String(post.sourceId).replace(/[^a-zA-Z0-9]/g, "-").slice(0, 63)}`;
    const license = SOURCE === "usajobs" ? "public-domain" : "publisher-licensed";
    const row = [
      vid, rkey, COLLECTOR_DID, "com.etzhayyim.apps.recruit.jobPosting",
      SOURCE, license, String(post.sourceId), post.sourceUrl,
      post.title, post.description,
      post.employerResolved.did, post.employerResolved.name, post.employerResolved.registryId,
      post.iscoCode ?? null, post.onetSocCode ?? null,
      post.country, post.location, post.remoteAllowed ?? null, post.employmentType,
      post.salaryMin, post.salaryMax, post.salaryCurrency,
      post.postedAt, post.expiresAt, now,
    ];
    ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
    vals.push(...row);
  }
  if (!ph.length) return 0;
  const pg = await pool();
  await pg.query(`INSERT INTO vertex_job_posting (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
  return ph.length;
}

// ── Main ──────────────────────────────────────────────────────────────────
async function main() {
  console.log(`[${SOURCE}] collect start  keyword="${KEYWORD}" pages=${PAGES} limit=${LIMIT} dry-run=${DRY_RUN}`);
  const fetcher = FETCHERS[SOURCE];
  let totalFetched = 0, totalAnchored = 0, totalSkipped = 0, totalWritten = 0;
  const buffer = [];

  for (let page = 1; page <= PAGES; page++) {
    const items = await fetcher({ keyword: KEYWORD, page });
    if (!items.length) break;
    totalFetched += items.length;

    for (const item of items) {
      if (totalAnchored >= LIMIT) break;
      assertNotProhibited(item.sourceUrl);
      const anchored = await resolveEmployer({
        name: item.employer.name,
        lei: item.employer.lei,
        registryId: item.employer.registryId,
        country: item.employer.country,
      });
      if (!anchored) {
        totalSkipped += 1;
        continue;
      }
      buffer.push({ ...item, employerResolved: anchored });
      totalAnchored += 1;
    }
    console.log(`[${SOURCE}] page=${page} fetched=${items.length} anchored=${totalAnchored} skipped=${totalSkipped}`);
    if (totalAnchored >= LIMIT) break;
  }

  if (buffer.length && !DRY_RUN) {
    totalWritten = await writePostings(buffer);
  } else if (DRY_RUN) {
    totalWritten = buffer.length;
  }

  await writeFile(PROGRESS_FILE, JSON.stringify({
    source: SOURCE, keyword: KEYWORD, totalFetched, totalAnchored, totalSkipped, totalWritten,
  }, null, 2));

  if (_pgPool) await _pgPool.end();
  console.log(`[${SOURCE}] done  fetched=${totalFetched} anchored=${totalAnchored} skipped=${totalSkipped} written=${totalWritten}`);
  if (totalSkipped > 0) {
    console.log(`[${SOURCE}] note: ${totalSkipped} postings dropped due to missing employer anchor in vertex_legal_entity`);
  }
}

main().catch((err) => { console.error(err.message); process.exit(1); });
