#!/usr/bin/env node
/**
 * Recruit — Direct ATS job posting ingest (Greenhouse + Lever public APIs).
 *
 * Both Greenhouse and Lever expose **unauthenticated public APIs** for job boards —
 * no API key required, all data is publicly accessible on careers pages.
 *
 *   Greenhouse: https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
 *   Lever:      https://api.lever.co/v0/postings/{company}?mode=json
 *
 * ADR-0027 compliance:
 *   - source_license = "public-careers" (public job board data, facts not creative)
 *   - source_homepage records the upstream public API host
 *   - PROHIBITED_HOST_FRAGMENTS enforced (LinkedIn/Indeed etc. blocked)
 *   - real inserts require employer_did resolved from vertex_legal_entity
 *
 * NOTE: CC CDX fallback for `recruit-ingest-commoncrawl.mjs` remains available
 * when CC CDX API (index.commoncrawl.org) recovers from current 504 outage.
 *
 * Usage:
 *   node recruit-ingest-ats-direct.mjs [--dry-run] [--platform greenhouse|lever|all]
 *   node recruit-ingest-ats-direct.mjs --limit 100 --batch-size 50
 */
import { writeFile, readFile } from "node:fs/promises";
import { createRequire } from "node:module";

const KOTOBA_URL   = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const RECRUIT_DID = "did:web:recruit.etzhayyim.com";
const COLLECTION  = "com.etzhayyim.apps.recruit.jobPosting";
const NOW         = new Date().toISOString();

const args     = process.argv.slice(2);
const hasFlag  = k => args.includes(`--${k}`);
const getArg   = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const DRY_RUN  = hasFlag("dry-run");
const ALLOW_UNANCHORED = hasFlag("allow-unanchored");
const IGNORE_CHECKPOINT = hasFlag("ignore-checkpoint");
const PLATFORM = getArg("platform", "all");
const LIMIT    = parseInt(getArg("limit", "5000"), 10);
const BATCH    = parseInt(getArg("batch-size", "200"), 10);
const CHECKPOINT = "/tmp/ats-direct-checkpoint.json";
const PROHIBITED_HOST_FRAGMENTS = [
  "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
  "wantedly.com", "bizreach.jp",
];
const SOURCE_HOMEPAGES = {
  greenhouse: "https://boards-api.greenhouse.io",
  lever: "https://api.lever.co",
  ashby: "https://api.ashbyhq.com",
};
const graphRequire = createRequire(new URL("../../30-graph/graph-schema/package.json", import.meta.url));

function assertNotProhibited(url) {
  if (!url) return;
  const lower = String(url).toLowerCase();
  for (const fragment of PROHIBITED_HOST_FRAGMENTS) {
    if (lower.includes(fragment)) {
      throw new Error(`compliance violation: prohibited job URL ${url}`);
    }
  }
}

// ── ISCO title → code (ordered most-specific first) ──────────────────────────
const ISCO_RULES = [
  [/software\s+eng|software\s+dev|full.?stack|backend\s+(eng|dev)|frontend\s+(eng|dev)|web\s+dev|mobile\s+dev|ios\s+(eng|dev)|android\s+(eng|dev)|flutter|react\s+native/i, "2512"],
  [/data\s+eng|analytics\s+eng|bi\s+eng|data\s+architect|データエンジニア/i, "2511"],
  [/machine\s+learn|ml\s+eng|ai\s+eng|data\s+scien|nlp|llm|genai|devops|sre|site\s+reliab|platform\s+eng|cloud\s+eng|infra/i, "2519"],
  [/product\s+manag|product\s+owner|プロダクトマネージャ/i, "2421"],
  [/ux\s+design|ui\s+design|product\s+design|visual\s+design|brand\s+design|graphic\s+design|デザイナ/i, "2166"],
  [/market|growth\s+hack|seo|demand\s+gen|content\s+market|マーケティング/i, "2431"],
  [/sales\s+eng|account\s+(exec|manager)|biz\s+dev|business\s+dev|solutions\s+eng|営業|セールス/i, "2433"],
  [/hr\s+manager|hr\s+business|human\s+res|people\s+ops|talent\s+acqui|recruiter|採用担当|人事/i, "2423"],
  [/account|finance|financial\s+analyst|controller|cfo|fp&a|audit|会計|経理|財務/i, "2411"],
  [/security\s+eng|cybersec|infosec|pentest|appsec|セキュリティ/i, "2519"],
  [/qa\s+eng|quality\s+assur|test\s+eng|sdet|qe\b/i, "3512"],
  [/customer\s+success|customer\s+support|technical\s+support|カスタマー/i, "3514"],
  [/sales\s+rep|inside\s+sales|sdr|bdr|outbound\s+sales/i, "3323"],
  [/exec.*assist|office\s+manager|admin|coordinator|アシスタント/i, "4120"],
  [/ceo|cto|chief\s+exec|managing\s+director|general\s+manager|vp\s+(of\s+)?eng|director\s+of\s+eng|社長|代表/i, "1120"],
  [/legal|lawyer|counsel|compliance|弁護士|法務/i, "2611"],
  [/nurse|physician|doctor|医師|看護師/i, "2221"],
  [/teacher|professor|instructor|research\s+scien|postdoc|研究|教師/i, "2310"],
  [/supply\s+chain|logistics|procurement|調達|ロジスティクス/i, "1321"],
  [/civil\s+eng|mechanical\s+eng|electrical\s+eng|hardware\s+eng|機械設計|電気/i, "2141"],
];

function titleToIsco(title) {
  if (!title) return null;
  for (const [re, code] of ISCO_RULES) {
    if (re.test(title)) return code;
  }
  return null;
}

// ── Greenhouse companies ──────────────────────────────────────────────────────
// Public boards — all posted openly, no key required.
const GREENHOUSE_COMPANIES = [
  // AI / ML / LLM
  "anthropic", "cohere", "mistral", "huggingface", "scale-ai", "weights-biases",
  "datarobot", "c3-ai", "veritone", "abacus-ai", "imbue", "adept",
  "aleph-alpha", "ai21-labs", "nomic", "contextual-ai", "vectara",
  "predibase", "cleanlab", "snorkel-ai", "superwise", "arize-ai",
  // Cloud / Infra / DevOps
  "cloudflare", "fastly", "hashicorp", "pulumi", "replicated",
  "1password", "doppler", "snyk", "lacework", "wiz", "orca-security",
  "datadog", "pagerduty", "honeycomb-io", "grafana", "chronosphere",
  "confluent", "elastic", "couchbase", "cockroachdb", "yugabyte",
  "teleport", "tailscale", "twingate", "strongdm",
  "buildkite", "circleci", "harness", "cortex-io",
  "chef", "chef-software", "puppet", "spacelift",
  "samsara", "armis", "claroty",
  // Fintech / Payments
  "stripe", "brex", "mercury-technologies", "ramp", "plaid", "marqeta",
  "chime", "green-dot", "kraken", "coinbase", "ripple",
  "affirm", "blend", "opendoor", "roofstock", "divvy",
  "bill-com", "tipalti", "payoneer", "airwallex-us",
  "carta", "equityzen", "secfi",
  "klarna-us", "zip-co", "parafin", "jeeves",
  // Developer Tools / SaaS
  "notion-so", "retool", "airtable", "figma", "miro", "webflow",
  "contentful", "sanity-io", "netlify", "vercel-career",
  "linear", "height-app", "shortcut", "plane-so",
  "loom", "descript", "grain", "fathom-video",
  "readme", "stoplight", "speakeasy-api",
  "postman", "insomnia", "hoppscotch",
  // Data / Analytics / BI
  "databricks", "dbt-labs", "fivetran", "airbyte", "hightouch",
  "amplitude", "mixpanel", "heap", "fullstory", "sprig",
  "census-data", "rudderstack", "segment-io",
  "metaplane", "monte-carlo-data", "acceldata",
  "preset-io", "lightdash", "holistics",
  "starburst", "ahana", "upsolver",
  // Enterprise / HR / People Ops
  "rippling", "deel", "lattice", "leapsome", "personio", "remote-com",
  "workos", "okta", "jumpcloud",
  "gusto", "bamboohr", "culture-amp", "15five", "betterworks",
  "hibob", "nmbrs", "cezanne-hr",
  "greenhouse-software", "lever-co", "ashby-hq",
  // Marketing / CX
  "klaviyo", "attentive", "yotpo", "recharge", "postscript",
  "gorgias", "zendesk-greenhouse", "freshworks",
  "intercom", "help-scout", "front-app",
  "customer-io", "braze", "iterable",
  "twilio-greenhouse", "sendbird",
  // Commerce / Marketplace
  "shopify", "faire-wholesale", "fabric-commerce",
  "nacelle", "tapcart", "rebuy",
  // Security
  "cyberark", "illumio", "semgrep", "socket", "drata",
  "secureframe", "vanta", "laika", "oneleet",
  "legitimate-security", "aikido-security", "bearer",
  "endor-labs", "ox-security", "apiiro",
  // Health / Bio / Pharma
  "tempus", "recursion", "benchling", "veeva-systems",
  "guardant-health", "grail", "natera", "invitae",
  "ro-health", "hims-hers", "sesame-care",
  "canvas-medical", "commure", "regard",
  // Vertical SaaS
  "toast-tab", "touchbistro", "lightspeed-hq",
  "procore", "buildops", "fieldwire",
  "veeva-systems", "inovalon", "privia-health",
  // Logistics / Supply Chain
  "project44", "flexport-greenhouse", "loadsmart",
  "stord", "shipbob", "shipmonk",
  // Japan / APAC
  "mercari", "paidy", "smarthr", "freee", "money-forward",
  "sansan", "m3inc", "chatwork-inc",
  "kaizen-platform", "appier",
];

// ── Lever companies ───────────────────────────────────────────────────────────
const LEVER_COMPANIES = [
  // AI / LLM / ML
  "openai", "stability-ai", "together-ai", "perplexity", "ideogram",
  "runway-ml", "character", "inflection", "cohere-lever",
  "anyscale", "modal-labs", "banana-dev", "replicate",
  "labelbox", "scale-lever", "encord", "hasty-ai",
  "clarifai", "roboflow", "landing-ai",
  // Developer Infrastructure
  "vercel", "supabase", "planetscale", "neon-tech", "fly-io", "turso",
  "render", "railway-lever", "cyclic-sh",
  "posthog", "highlight-run", "signoz",
  "trigger-dev", "inngest", "quirrel",
  "prisma", "drizzle-team", "diesel-rs",
  "wundergraph", "grafbase", "hasura",
  // Fintech
  "wise", "paysend", "melio", "treasury-prime", "modern-treasury",
  "stripe-lever", "moov-financial", "unit-co",
  "bond-financial", "synctera", "bankos",
  "found-business", "nearside", "relay-fi",
  // Data / BI
  "census", "rudderstack", "metabase", "lightdash", "evidence-dev",
  "transformdata", "sdf-labs", "malloy-data",
  // HR / Payroll
  "gusto", "rippling-lever", "bamboohr-lever", "culture-amp-lever",
  "remote-lever", "oyster-hr", "pilot-co",
  "wave-hq", "weel",
  // Commerce / DTC
  "recharge", "gorgias", "postscript", "loop", "narvar",
  "rebuy-lever", "nosto", "talon-one",
  // Security
  "tailscale", "twingate", "teleport", "gitguardian", "aikido-security",
  "nightfall-ai", "cycode", "legit-security",
  "stackhawk", "escape-tech",
  // Vertical / Other
  "canva-lever", "loom-lever", "figma-lever",
  "draftbit", "framer", "penpot",
  "deel-lever", "remote-first", "oyster-lever",
  // Japan / APAC
  "layerx", "opn", "rakus", "visasq",
  "yayoi-co", "freee-lever", "ubie",
];

// ── Ashby companies ───────────────────────────────────────────────────────────
// Ashby public API: GET https://jobs.ashbyhq.com/api/non-user-graphql (POST GraphQL)
// Simple endpoint: https://api.ashbyhq.com/posting-api/job-board/{org} (no auth for public boards)
const ASHBY_COMPANIES = [
  // AI / ML
  "modal", "anyscale", "together", "nomic", "llamaindex",
  "weaviate", "qdrant", "chroma", "pinecone-lever",
  "dust-tt", "langchain", "haystack",
  // Dev infra
  "posthog", "highlight", "logfire", "axiom",
  "inngest", "trigger", "windmill",
  "trpc", "convex", "liveblocks",
  // SaaS
  "linear-ashby", "height", "plane",
  "dub-co", "cal-com", "crowd-dev",
  // Fintech
  "fern-api", "speakeasy", "stainless",
  // Japan
  "ubie-ashby", "yper",
];

// ── pg pool ───────────────────────────────────────────────────────────────────
let _pool = null;
async function pool() {
  if (_pool) return _pool;
  const pg = graphRequire("pg");
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60_000 });
  return _pool;
}
async function query(sql, vals = []) { const db = await pool(); return db.query(sql, vals); }

// ── Insert batch ──────────────────────────────────────────────────────────────
const COLS = [
  "vertex_id","rkey","repo","label","source","source_license","source_homepage","source_id","source_url",
  "title","description","employer_did","employer_name","employer_registry_id","isco_code","country","location",
  "remote_allowed","employment_type","salary_min","salary_max","salary_currency",
  "posted_at","expires_at","ingested_at",
];
const EMPLOYER_DID_INDEX = COLS.indexOf("employer_did");
const EMPLOYER_NAME_INDEX = COLS.indexOf("employer_name");
const EMPLOYER_REGISTRY_ID_INDEX = COLS.indexOf("employer_registry_id");
const COUNTRY_INDEX = COLS.indexOf("country");

async function batchInsert(rows) {
  if (rows.length === 0) return 0;
  let inserted = 0;
  for (const row of rows) {
    const placeholders = row.map((_, i) => {
      const n = i + 1;
      if (n === 18) return `$${n}::boolean`;
      if (n === 20 || n === 21) return `$${n}::bigint`;
      return `$${n}::varchar`;
    }).join(",");
    const result = await query(
      `INSERT INTO vertex_job_posting (${COLS.join(",")})
       SELECT ${placeholders}
       WHERE NOT EXISTS (
         SELECT 1 FROM vertex_job_posting
         WHERE source = $5 AND source_id = $8
       )`,
      row,
    );
    inserted += result.rowCount ?? 0;
  }
  return inserted;
}

function makeId(source, company, externalId) {
  return `${source}:${company}:${externalId}`;
}
function makeRkey(vid) { return vid.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 128); }

function normalizeEmployerName(name) {
  return String(name ?? "")
    .replace(/\b(inc|inc\.|llc|ltd|ltd\.|limited|corp|corp\.|corporation|co|co\.|company|gmbh|kk|k\.k\.)\b/gi, "")
    .replace(/[株式会社（）()]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

async function resolveEmployerAnchor(row) {
  const employerName = row[EMPLOYER_NAME_INDEX];
  if (!employerName) return null;
  const normalized = normalizeEmployerName(employerName);
  if (!normalized) return null;
  const country = row[COUNTRY_INDEX];
  // Keep live ingest bounded: broad LIKE scans over vertex_legal_entity can
  // time out on the production graph. Fuzzy reconciliation belongs in a
  // separate backfill/reconcile job, not the posting fetch path.
  const { rows } = await query(
    `
    SELECT vertex_id, name, source_record_id
    FROM vertex_legal_entity
    WHERE lower(name) = lower($1)
       OR lower(name) = lower($2)
    ORDER BY
      CASE WHEN lower(name) = lower($1) THEN 0 ELSE 1 END,
      CASE WHEN $3::varchar IS NOT NULL AND country = $3 THEN 0 ELSE 1 END,
      length(name)
    LIMIT 1
    `,
    [employerName, normalized, country],
  );
  const match = rows[0];
  if (!match) return null;
  return {
    did: match.vertex_id,
    name: match.name ?? employerName,
    registryId: match.source_record_id ?? null,
  };
}

async function anchorRows(rows) {
  if (DRY_RUN) return { rows, skipped: 0 };
  if (ALLOW_UNANCHORED) return { rows, skipped: 0 };
  if (process.env.RECRUIT_ENABLE_LIVE_ANCHOR_LOOKUP !== "1") {
    return { rows: [], skipped: rows.length };
  }
  const anchored = [];
  let skipped = 0;
  for (const row of rows) {
    const anchor = await resolveEmployerAnchor(row);
    if (!anchor && !ALLOW_UNANCHORED) {
      skipped += 1;
      continue;
    }
    if (anchor) {
      row[EMPLOYER_DID_INDEX] = anchor.did;
      row[EMPLOYER_NAME_INDEX] = anchor.name;
      row[EMPLOYER_REGISTRY_ID_INDEX] = anchor.registryId;
    }
    anchored.push(row);
  }
  return { rows: anchored, skipped };
}

// ── Greenhouse ingest ─────────────────────────────────────────────────────────
async function ingestGreenhouse(company, seen) {
  const url = `https://boards-api.greenhouse.io/v1/boards/${company}/jobs?content=true`;
  let data;
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)" },
      signal: AbortSignal.timeout(15000),
    });
    if (res.status === 404) return [];  // company not on GH or board is private
    if (!res.ok) return [];
    data = await res.json();
  } catch {
    return [];
  }

  const jobs = data?.jobs ?? [];
  const rows = [];
  for (const job of jobs) {
    const vid = makeId("greenhouse", company, String(job.id));
    if (seen.has(vid)) continue;
    seen.add(vid);

    const title   = job.title ?? "";
    const isco    = titleToIsco(title);
    const loc     = job.location?.name ?? null;
    const country = loc ? guessCountry(loc) : null;
    const remote  = /remote/i.test(loc ?? "") || /remote/i.test(title);
    const dept    = job.departments?.[0]?.name ?? null;
    const content = job.content?.replace(/<[^>]+>/g, " ").trim().slice(0, 2000) ?? null;
    const appUrl  = job.absolute_url ?? url;
    assertNotProhibited(appUrl);
    const updated = job.updated_at ? new Date(job.updated_at).toISOString() : NOW;

    rows.push([
      vid, makeRkey(vid), RECRUIT_DID, COLLECTION,
      "greenhouse", "public-careers", SOURCE_HOMEPAGES.greenhouse, String(job.id), appUrl,
      title, content, null, company, null, isco,
      country, loc, remote, dept,
      null, null, null,
      updated, null, NOW,
    ]);
  }
  return rows;
}

// ── Lever ingest ──────────────────────────────────────────────────────────────
async function ingestLever(company, seen) {
  const url = `https://api.lever.co/v0/postings/${company}?mode=json`;
  let data;
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)" },
      signal: AbortSignal.timeout(15000),
    });
    if (res.status === 404) return [];
    if (!res.ok) return [];
    data = await res.json();
  } catch {
    return [];
  }

  const jobs = Array.isArray(data) ? data : (data?.postings ?? []);
  const rows = [];
  for (const job of jobs) {
    const vid = makeId("lever", company, job.id ?? job.text);
    if (seen.has(vid)) continue;
    seen.add(vid);

    const title   = job.text ?? "";
    const isco    = titleToIsco(title);
    const loc     = job.categories?.location ?? job.workplaceType ?? null;
    const country = loc ? guessCountry(loc) : null;
    const remote  = job.workplaceType === "remote" || /remote/i.test(loc ?? "");
    const dept    = job.categories?.department ?? null;
    const content = job.descriptionPlain?.slice(0, 2000)
                 ?? job.description?.replace(/<[^>]+>/g, " ").slice(0, 2000)
                 ?? null;
    const appUrl  = job.hostedUrl ?? url;
    assertNotProhibited(appUrl);
    const created = job.createdAt ? new Date(job.createdAt).toISOString() : NOW;

    rows.push([
      vid, makeRkey(vid), RECRUIT_DID, COLLECTION,
      "lever", "public-careers", SOURCE_HOMEPAGES.lever, String(job.id ?? job.text), appUrl,
      title, content, null, company, null, isco,
      country, loc, remote, dept,
      null, null, null,
      created, null, NOW,
    ]);
  }
  return rows;
}

// ── Ashby ingest ──────────────────────────────────────────────────────────────
async function ingestAshby(company, seen) {
  // Ashby public posting API — no auth required for public boards
  const url = `https://api.ashbyhq.com/posting-api/job-board/${company}`;
  let data;
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)" },
      signal: AbortSignal.timeout(15000),
    });
    if (res.status === 404 || res.status === 403) return [];
    if (!res.ok) return [];
    data = await res.json();
  } catch {
    return [];
  }

  const jobs = data?.jobs ?? data?.jobPostings ?? [];
  const rows = [];
  for (const job of jobs) {
    const vid = makeId("ashby", company, job.id ?? job.externalId ?? job.title);
    if (seen.has(vid)) continue;
    seen.add(vid);

    const title   = job.title ?? "";
    const isco    = titleToIsco(title);
    const loc     = job.location ?? job.locationName ?? null;
    const country = loc ? guessCountry(loc) : null;
    const remote  = job.isRemote === true || /remote/i.test(loc ?? "");
    const dept    = job.department ?? job.team ?? null;
    const content = job.descriptionSocial?.slice(0, 2000)
                 ?? job.descriptionPlain?.slice(0, 2000) ?? null;
    const appUrl  = job.jobUrl ?? job.applyUrl ?? url;
    assertNotProhibited(appUrl);
    const created = job.publishedAt ? new Date(job.publishedAt).toISOString() : NOW;

    rows.push([
      vid, makeRkey(vid), RECRUIT_DID, COLLECTION,
      "ashby", "public-careers", SOURCE_HOMEPAGES.ashby, String(job.id ?? job.externalId ?? job.title), appUrl,
      title, content, null, company, null, isco,
      country, loc, remote, dept,
      null, null, null,
      created, job.expiresAt ?? null, NOW,
    ]);
  }
  return rows;
}

function guessCountry(loc) {
  if (!loc) return null;
  const l = loc.toLowerCase();
  if (/japan|tokyo|osaka|kyoto|fukuoka|nagoya|東京|大阪/.test(l)) return "JP";
  if (/united states|usa|\bus\b|new york|san francisco|sf bay|seattle|austin|chicago|boston|los angeles|remote/.test(l)) return "US";
  if (/united kingdom|london|\buk\b|manchester|edinburgh/.test(l)) return "GB";
  if (/germany|berlin|munich|hamburg|德国/.test(l)) return "DE";
  if (/canada|toronto|vancouver|montreal|ottawa/.test(l)) return "CA";
  if (/australia|sydney|melbourne|brisbane/.test(l)) return "AU";
  if (/india|bangalore|bengaluru|mumbai|delhi|hyderabad|pune/.test(l)) return "IN";
  if (/singapore|シンガポール/.test(l)) return "SG";
  if (/france|paris|lyon|marseille/.test(l)) return "FR";
  if (/netherlands|amsterdam|rotterdam/.test(l)) return "NL";
  if (/poland|warsaw|krakow|wroclaw/.test(l)) return "PL";
  if (/brazil|são paulo|sao paulo|rio/.test(l)) return "BR";
  if (/spain|madrid|barcelona/.test(l)) return "ES";
  if (/sweden|stockholm/.test(l)) return "SE";
  if (/israel|tel aviv/.test(l)) return "IL";
  if (/ukraine|kyiv|lviv/.test(l)) return "UA";
  if (/mexico|cdmx|monterrey/.test(l)) return "MX";
  if (/colombia|bogota|medellin/.test(l)) return "CO";
  if (/argentina|buenos aires/.test(l)) return "AR";
  if (/switzerland|zurich|geneva/.test(l)) return "CH";
  if (/ireland|dublin/.test(l)) return "IE";
  if (/south korea|korea|seoul/.test(l)) return "KR";
  if (/china|beijing|shanghai|shenzhen/.test(l)) return "CN";
  return null;
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`[ats] platform=${PLATFORM}  limit=${LIMIT}  dry-run=${DRY_RUN} allow_unanchored=${ALLOW_UNANCHORED} ignore_checkpoint=${IGNORE_CHECKPOINT}`);

  // Load checkpoint (seen vertex_ids). Dry-runs must not depend on or mutate
  // operational state, otherwise verification changes later ingest behavior.
  let seen = new Set();
  if (!DRY_RUN && !IGNORE_CHECKPOINT) {
    try {
      const cp = JSON.parse(await readFile(CHECKPOINT, "utf8"));
      seen = new Set(cp.seen ?? []);
      console.log(`[ats] checkpoint: ${seen.size} already seen`);
    } catch { /* no checkpoint */ }
  }

  let total = 0;
  let fetched = 0;
  let totalSkipped = 0;
  const buffer = [];

  const enqueueRows = async (rows) => {
    const remaining = LIMIT - (total + buffer.length);
    if (remaining <= 0 || rows.length === 0) return 0;
    const { rows: anchorChecked, skipped } = await anchorRows(rows);
    totalSkipped += skipped;
    const accepted = anchorChecked.slice(0, remaining);
    fetched += accepted.length;
    buffer.push(...accepted);
    return accepted.length;
  };

  const flush = async () => {
    if (buffer.length === 0) return;
    if (!DRY_RUN) {
      try { total += await batchInsert(buffer); }
      catch (e) { console.warn(`[ats] insert failed: ${e.message}`); }
    } else {
      total += buffer.length;
    }
    buffer.length = 0;
  };

  // ── Greenhouse ──
  if (PLATFORM === "all" || PLATFORM === "greenhouse") {
    let ghDone = 0, ghFound = 0;
    for (const company of GREENHOUSE_COMPANIES) {
      if (total + buffer.length >= LIMIT) break;
      await new Promise(r => setTimeout(r, 80)); // polite throttle
      const rows = await ingestGreenhouse(company, seen);
      ghDone++;
      if (rows.length > 0) {
        const accepted = await enqueueRows(rows);
        ghFound += accepted;
        if (ghDone % 5 === 0)
          console.log(`[ats] greenhouse ${ghDone}/${GREENHOUSE_COMPANIES.length}  new=${ghFound}`);
      }
      if (buffer.length >= BATCH) await flush();
    }
    await flush();
    console.log(`[ats] greenhouse done  companies=${ghDone}  jobs=${ghFound}`);
  }

  // ── Lever ──
  if (PLATFORM === "all" || PLATFORM === "lever") {
    let lvDone = 0, lvFound = 0;
    for (const company of LEVER_COMPANIES) {
      if (total >= LIMIT) break;
      await new Promise(r => setTimeout(r, 80));
      const rows = await ingestLever(company, seen);
      lvDone++;
      if (rows.length > 0) {
        const accepted = await enqueueRows(rows);
        lvFound += accepted;
        if (lvDone % 5 === 0)
          console.log(`[ats] lever ${lvDone}/${LEVER_COMPANIES.length}  new=${lvFound}`);
      }
      if (buffer.length >= BATCH) await flush();
    }
    await flush();
    console.log(`[ats] lever done  companies=${lvDone}  jobs=${lvFound}`);
  }

  // ── Ashby ──
  if (PLATFORM === "all" || PLATFORM === "ashby") {
    let abDone = 0, abFound = 0;
    for (const company of ASHBY_COMPANIES) {
      if (total + buffer.length >= LIMIT) break;
      await new Promise(r => setTimeout(r, 80));
      const rows = await ingestAshby(company, seen);
      abDone++;
      if (rows.length > 0) {
        const accepted = await enqueueRows(rows);
        abFound += accepted;
        if (abDone % 5 === 0)
          console.log(`[ats] ashby ${abDone}/${ASHBY_COMPANIES.length}  new=${abFound}`);
      }
      if (buffer.length >= BATCH) await flush();
    }
    await flush();
    console.log(`[ats] ashby done  companies=${abDone}  jobs=${abFound}`);
  }

  console.log(`[ats] total inserted=${total}  dry-run=${DRY_RUN}`);

  if (!DRY_RUN && !IGNORE_CHECKPOINT) {
    const { rows } = await query(`
      SELECT source, COUNT(*) AS cnt
      FROM vertex_job_posting
      WHERE source IN ('greenhouse','lever','ashby')
      GROUP BY source ORDER BY source
    `);
    rows.forEach(r => console.log(`[ats] vertex_job_posting[${r.source}] total=${r.cnt}`));
  }

  // Save checkpoint
  if (!DRY_RUN) {
    await writeFile(CHECKPOINT, JSON.stringify({ seen: [...seen].slice(-100000) }));
  }
  await writeFile("/tmp/ats-direct-summary.json", JSON.stringify({
    platform: PLATFORM, fetched, inserted: total, skipped: totalSkipped + Math.max(0, fetched - total), dry_run: DRY_RUN,
    allow_unanchored: ALLOW_UNANCHORED,
    ignore_checkpoint: IGNORE_CHECKPOINT,
    privacyMode: "public-postings-only",
    greenhouse_companies: GREENHOUSE_COMPANIES.length,
    lever_companies: LEVER_COMPANIES.length,
    ashby_companies: ASHBY_COMPANIES.length,
  }, null, 2));

  if (_pool) await _pool.end();
}

main().catch(e => { console.error(e); process.exit(1); });
