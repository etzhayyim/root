#!/usr/bin/env node
/**
 * Recruit — Press release hiring signal ingest + demand forecast computation.
 *
 * Phase B: polls RSS feeds from PR TIMES, BusinessWire, Globe Newswire,
 * extracts hiring trigger signals (hiring|expansion|funding|new_product|office_open),
 * maps to ISCO codes via title/body keyword matching, inserts into vertex_press_signal,
 * then recomputes vertex_demand_forecast by joining with vertex_talent_cohort
 * (supply-side) and vertex_occupation_bls (wage benchmark).
 *
 * ADR-0018 compliance: aggregate demand signals only — no individual PII stored.
 * ADR-0027 compliance: source_license per-row, public RSS feeds only.
 *
 * RSS Sources (public, no key required):
 *   PR TIMES          — https://prtimes.jp/rss/allpresses/  (JP, CC-BY licensing per JP law)
 *   BusinessWire      — https://www.businesswire.com/rss/home/?rss=G1  (EN)
 *   Globe Newswire HR — https://www.globenewswire.com/RssFeed/subjectcode/47-Human+Resources%26Personnel (EN)
 *   EIN Presswire     — https://www.einpresswire.com/rss/  (EN)
 *   PRWeb             — https://www.prweb.com/rss2/prweb.xml (EN)
 *
 * Usage:
 *   node recruit-ingest-press-signals.mjs [--dry-run] [--year 2025]
 *   node recruit-ingest-press-signals.mjs --step signals       # RSS ingest only
 *   node recruit-ingest-press-signals.mjs --step forecasts     # recompute forecasts only
 *   node recruit-ingest-press-signals.mjs --step all           # both (default)
 */
import { writeFile, readFile } from "node:fs/promises";

const KOTOBA_URL     = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const RECRUIT_DID = "did:web:recruit.etzhayyim.com";
const NOW         = new Date().toISOString();
const YEAR        = process.argv.includes("--year")
  ? process.argv[process.argv.indexOf("--year") + 1]
  : String(new Date().getFullYear());

const args    = process.argv.slice(2);
const hasFlag = k => args.includes(`--${k}`);
const getArg  = (k, d) => { const i = args.indexOf(`--${k}`); return i === -1 ? d : args[i + 1] ?? d; };
const DRY_RUN = hasFlag("dry-run");
const STEP    = getArg("step", "all");

// ── RSS sources ───────────────────────────────────────────────────────────────
const RSS_SOURCES = [
  // Tech / startup news — rich in funding + hiring signals
  { id: "techcrunch",     url: "https://techcrunch.com/feed/",                                  country: null, license: "crawl-public", lang: "en" },
  { id: "venturebeat",    url: "https://venturebeat.com/feed/",                                 country: null, license: "crawl-public", lang: "en" },
  // Press wire services
  { id: "prnewswire",     url: "https://www.prnewswire.com/rss/news-releases-list.rss",         country: null, license: "crawl-public", lang: "en" },
  { id: "globenewswire",  url: "https://www.globenewswire.com/RssFeed/country/Japan",            country: "JP", license: "crawl-public", lang: "en" },
  { id: "globenewswire-us", url: "https://www.globenewswire.com/RssFeed/country/United+States", country: "US", license: "crawl-public", lang: "en" },
  // JP IT news — rich in 採用 / 人材 signals
  { id: "itmedia",        url: "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",             country: "JP", license: "crawl-public", lang: "ja" },
  { id: "nikkei-xtech",   url: "https://xtech.nikkei.com/rss/xtech-it.rdf",                    country: "JP", license: "crawl-public", lang: "ja" },
];

// ── Hiring trigger patterns ───────────────────────────────────────────────────
// Each rule: { type, score, patterns[] (OR'd) }
const TRIGGER_RULES = [
  {
    type: "funding",
    score: 0.9,
    en: [/series [A-F]\b|seed\s+round|raised \$|funding round|venture\s+capital|investment\s+of|backed by/i],
    ja: [/シリーズ[A-F]|資金調達|出資|資本参加|VCからの/],
  },
  {
    type: "hiring",
    score: 1.0,
    en: [/\bhiring\b|now\s+hiring|we.re\s+(growing|hiring|recruiting)|open\s+(role|position|job)|join\s+(our|the)\s+team|careers?\s+at|looking\s+for\s+(a|an)|seeking\s+(a|an)|new\s+role\b/i],
    ja: [/採用|募集|求人|スタッフ募集|人材採用|採用強化|新規採用|増員/],
  },
  {
    type: "expansion",
    score: 0.8,
    en: [/new\s+office|expand|expansion|new\s+market|launch(es|ing|ed)?\s+in|enters?\s+(the\s+)?[A-Z]|opens?\s+(in|office)|new\s+headquarters/i],
    ja: [/新拠点|オフィス開設|新市場|海外展開|事業拡大|拡大|進出|新規事業/],
  },
  {
    type: "new_product",
    score: 0.6,
    en: [/launch(es|ed)?\s+(new\s+)?product|releases?\s+(new\s+)?|introduces?\s+(new\s+)?|unveil|new\s+(ai|platform|service|feature|solution)/i],
    ja: [/新サービス|新製品|サービス開始|ローンチ|リリース|提供開始|プロダクト/],
  },
  {
    type: "office_open",
    score: 0.85,
    en: [/grand\s+open|opens?\s+(new\s+)?(office|headquarter|campus|hub|center|centre)|new\s+location/i],
    ja: [/グランドオープン|オープン|開業|開設|新オフィス|新本社/],
  },
];

function detectTrigger(text) {
  let bestType = null, bestScore = 0;
  for (const rule of TRIGGER_RULES) {
    const patterns = [...(rule.en ?? []), ...(rule.ja ?? [])];
    if (patterns.some(p => p.test(text))) {
      if (rule.score > bestScore) { bestScore = rule.score; bestType = rule.type; }
    }
  }
  return bestType ? { type: bestType, score: bestScore } : null;
}

// ── ISCO code mapping from press release title/body ───────────────────────────
const ISCO_RULES = [
  [/software\s+eng|software\s+dev|full.?stack|backend|frontend|web\s+dev|mobile\s+dev|プログラマ|エンジニア.*開発/i, "2512"],
  [/data\s+(engineer|architect|platform)|analytics\s+eng|bi\s+eng|データエンジニア/i, "2511"],
  [/machine\s+learn|ai\s+eng|ml\s+eng|data\s+scien|nlp|devops|sre|cloud\s+eng|インフラ|クラウド/i, "2519"],
  [/product\s+manag|プロダクトマネージャ/i, "2421"],
  [/ux|ui\s+design|デザイナ|グラフィックデザイン/i, "2166"],
  [/market|マーケティング|広告|growth\s+hack/i, "2431"],
  [/sales\s+eng|account\s+(exec|manager)|business\s+dev|営業/i, "2433"],
  [/hr|human\s+res|talent\s+acqui|recruiter|採用担当|人事/i, "2423"],
  [/account|finance|会計|経理|財務/i, "2411"],
  [/nurse|医師|看護師|doctor|physician/i, "2221"],
  [/teacher|instructor|教師|講師|professor/i, "2310"],
  [/legal|lawyer|counsel|法律|弁護士/i, "2611"],
  [/ceo|cto|director|chief\s+|managing\s+director|社長|代表取締役/i, "1120"],
];

function extractIscoCodes(text) {
  const codes = new Set();
  for (const [re, code] of ISCO_RULES) {
    if (re.test(text)) codes.add(code);
  }
  return [...codes].slice(0, 5);
}

// ── Country detection from text ───────────────────────────────────────────────
const COUNTRY_HINTS = [
  [/\bJapan\b|日本|Tokyo|Osaka|東京|大阪/i, "JP"],
  [/\bUSA?\b|\bUnited States\b|\bAmerica\b|New York|San Francisco|Silicon Valley/i, "US"],
  [/\bUK\b|\bUnited Kingdom\b|London|Britain/i, "GB"],
  [/\bGermany\b|\bDeutschland\b|Berlin|Munich/i, "DE"],
  [/\bFrance\b|Paris\b/i, "FR"],
  [/\bAustralia\b|Sydney|Melbourne/i, "AU"],
  [/\bCanada\b|Toronto|Vancouver/i, "CA"],
  [/\bIndia\b|Bangalore|Mumbai|Delhi/i, "IN"],
  [/\bChina\b|Beijing|Shanghai|中国/i, "CN"],
  [/\bSingapore\b|シンガポール/i, "SG"],
];

function detectCountry(text, defaultCountry) {
  if (defaultCountry) return defaultCountry;
  for (const [re, cc] of COUNTRY_HINTS) {
    if (re.test(text)) return cc;
  }
  return null;
}

// ── RSS fetch + parse ─────────────────────────────────────────────────────────
function parseRssItems(xml) {
  const items = [];
  const re = /<item>([\s\S]*?)<\/item>/gi;
  let m;
  while ((m = re.exec(xml)) !== null) {
    const block = m[1];
    const get = (tag) => {
      const r = new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]></${tag}>|<${tag}[^>]*>([^<]*)</${tag}>`, "i");
      const r2 = r.exec(block);
      return r2 ? (r2[1] ?? r2[2] ?? "").trim() : "";
    };
    const link    = get("link") || get("guid");
    const title   = get("title");
    const desc    = get("description").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 1000);
    const pubDate = get("pubDate");
    if (title && link) items.push({ link, title, desc, pubDate });
  }
  return items;
}

async function fetchRss(source) {
  const res = await fetch(source.url, {
    headers: { "User-Agent": "etzhayyim-recruit-bot/1.0 (+https://etzhayyim.com/recruit)", "Accept": "application/rss+xml, application/xml, text/xml" },
    signal: AbortSignal.timeout(20000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return parseRssItems(await res.text());
}

// ── pg pool ───────────────────────────────────────────────────────────────────
let _pool = null;
async function pool() {
  if (_pool) return _pool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 120_000 });
  return _pool;
}
async function query(sql, vals = []) { const db = await pool(); return db.query(sql, vals); }

// ── Step 1: ingest RSS signals ────────────────────────────────────────────────
async function stepSignals() {
  console.log("[press] step=signals");

  let totalNew = 0;

  for (const source of RSS_SOURCES) {
    console.log(`[press]   fetching ${source.id} ...`);
    let items;
    try {
      items = await fetchRss(source);
    } catch (e) {
      console.warn(`[press]   FAILED ${source.id}: ${e.message}`);
      continue;
    }
    console.log(`[press]   ${source.id}: ${items.length} items`);

    const rows = [];
    for (const item of items) {
      const full  = `${item.title} ${item.desc}`;
      const trig  = detectTrigger(full);
      if (!trig) continue;  // skip non-hiring articles

      const iscoCodes = extractIscoCodes(full);
      const country   = detectCountry(full, source.country);
      const vid       = `press:${source.id}:${Buffer.from(item.link).toString("base64url").slice(0, 32)}`;
      const published = item.pubDate ? new Date(item.pubDate).toISOString() : NOW;

      // Extract company name: try first word-group before verb in title
      const compMatch = item.title.match(/^(.+?)\s+(?:raises|announces|launches|opens|expands|hires|recruiting|採用|資金調達)/i);
      const compName  = compMatch ? compMatch[1].trim().slice(0, 255) : null;

      rows.push([
        vid,
        source.id,
        item.link.slice(0, 2048),
        source.license,
        compName,
        null,  // company_did (unresolved)
        item.title.slice(0, 1024),
        item.desc.slice(0, 2000),
        trig.type,
        trig.score,
        JSON.stringify(iscoCodes),
        country,
        published,
        NOW,
      ]);
    }

    if (rows.length === 0) continue;

    // Check which already exist
    const existVids = new Set(
      (await query(`SELECT vertex_id FROM vertex_press_signal WHERE vertex_id = ANY($1)`, [rows.map(r => r[0])])).rows.map(r => r.vertex_id)
    );
    const newRows = rows.filter(r => !existVids.has(r[0]));
    if (newRows.length === 0) { console.log(`[press]   ${source.id}: all ${rows.length} already exist`); continue; }

    if (!DRY_RUN) {
      const cols = ["vertex_id","source","source_url","source_license","company_name","company_did",
                    "headline","body_snippet","trigger_type","trigger_score","isco_codes",
                    "country","published_at","detected_at"];
      const ph = []; const vals = []; let p = 1;
      for (const row of newRows) {
        ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
        vals.push(...row);
      }
      await query(`INSERT INTO vertex_press_signal (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
    }
    console.log(`[press]   ${source.id}: inserted ${newRows.length} new signals`);
    totalNew += newRows.length;
  }

  console.log(`[press] signals done  new=${totalNew}`);
  return totalNew;
}

// ── ISO-2 → ILO-3 country code mapping ───────────────────────────────────────
const ISO2_TO_ILO3 = {
  US:"USA", JP:"JPN", CN:"CHN", DE:"DEU", FR:"FRA", GB:"GBR", CA:"CAN",
  AU:"AUS", IN:"IND", KR:"KOR", BR:"BRA", MX:"MEX", IT:"ITA", ES:"ESP",
  NL:"NLD", SE:"SWE", CH:"CHE", SG:"SGP", HK:"HKG", TW:"TWN", PL:"POL",
  RU:"RUS", ZA:"ZAF", NG:"NGA", ID:"IDN", TR:"TUR", AR:"ARG", CO:"COL",
  PE:"PER", CL:"CHL", PT:"PRT", BE:"BEL", AT:"AUT", DK:"DNK", NO:"NOR",
  FI:"FIN", NZ:"NZL", IE:"IRL", IL:"ISR", UA:"UKR", RO:"ROU", HU:"HUN",
  CZ:"CZE",
};

// ── Step 2: recompute demand forecasts ────────────────────────────────────────
async function stepForecasts() {
  console.log("[press] step=forecasts");

  // Press signals: expand JSON isco_codes arrays into individual (isco, country) pairs
  const { rows: sigRows } = await query(`
    SELECT isco_codes, country, COUNT(*) AS signal_count, AVG(trigger_score) AS avg_score
    FROM vertex_press_signal
    GROUP BY isco_codes, country
  `);
  const sigMap = {}; // "isco4:cc2" → { count, score }
  for (const row of sigRows) {
    let codes;
    try { codes = JSON.parse(row.isco_codes ?? "[]"); } catch { continue; }
    const cc = row.country ?? "WORLD";
    for (const isco of codes) {
      const k = `${isco}:${cc}`;
      if (!sigMap[k]) sigMap[k] = { count: 0, score: 0 };
      sigMap[k].count += Number(row.signal_count);
      sigMap[k].score += Number(row.avg_score) * Number(row.signal_count);
    }
  }
  for (const k of Object.keys(sigMap)) sigMap[k].score /= sigMap[k].count;

  // Job posting counts grouped by isco_code (4-digit) and country
  const { rows: postRows } = await query(`
    SELECT isco_code, country, COUNT(*) AS cnt
    FROM vertex_job_posting
    WHERE isco_code IS NOT NULL
    GROUP BY isco_code, country
  `);
  const postMap = {}; // "isco4:cc2" → count
  for (const r of postRows) {
    const k = `${r.isco_code}:${r.country ?? "WORLD"}`;
    postMap[k] = (postMap[k] ?? 0) + Number(r.cnt);
  }
  // Also add keys from postMap that are missing in sigMap (job-posting-only demand)
  for (const [k, cnt] of Object.entries(postMap)) {
    if (!sigMap[k]) sigMap[k] = { count: 0, score: 0.5 }; // baseline score
    sigMap[k].posting_count = cnt;
  }

  // Cohort supply: ILO uses ISCO 1-digit majors + 3-letter country codes
  // Pull both latest year and year-1 as fallback
  const { rows: cohortRows } = await query(`
    SELECT isco_code, country, MAX(size_thousands) AS size_k
    FROM vertex_talent_cohort
    WHERE isco_code IN ('1','2','3','4','5','6','7','8','9')
    GROUP BY isco_code, country
  `);
  // Build supply map: major → 3-letter-cc → supply_k
  const supplyMajor = {}; // "major:CC3" → k
  const supplyWorld = {}; // "major" → world total k
  for (const r of cohortRows) {
    const major = r.isco_code;
    const cc3   = r.country;
    const k     = `${major}:${cc3}`;
    supplyMajor[k] = (supplyMajor[k] ?? 0) + parseFloat(r.size_k || 0);
    // Accumulate world total from ILO X01 (world aggregate)
    if (cc3 === "X01") supplyWorld[major] = parseFloat(r.size_k || 0);
  }

  // BLS wage benchmarks: isco_code in vertex_occupation_bls is the ISCO major (1-digit)
  const { rows: blsRows } = await query(`
    SELECT isco_code, AVG(a_mean) AS avg_wage
    FROM vertex_occupation_bls
    WHERE isco_code IS NOT NULL AND a_mean IS NOT NULL
    GROUP BY isco_code
  `);
  const wageMap = {}; // major → avg annual USD
  for (const r of blsRows) wageMap[r.isco_code] = parseFloat(r.avg_wage) || null;

  // Skills per ISCO 4-digit code.
  // Note: edge_occupation_skill.occupation_id uses ESCO key format (key_NNNNN) which
  // doesn't match vertex_occupation.vertex_id (URI format). Pending FK repair migration.
  // Using curated ESCO-derived skill lists per ISCO unit group as interim data.
  const ISCO_SKILLS = {
    "1120": ["strategic planning","leadership","organisational management","stakeholder communication","business development"],
    "1330": ["research and development","technology strategy","team leadership","innovation management","product roadmap"],
    "1321": ["supply chain management","procurement","inventory management","vendor management","logistics coordination"],
    "2114": ["research methodology","data analysis","scientific writing","experiment design","statistical analysis"],
    "2141": ["mechanical engineering","CAD","structural analysis","manufacturing processes","product design"],
    "2166": ["graphic design","UI/UX design","typography","Adobe Creative Suite","visual communication"],
    "2211": ["clinical diagnosis","patient care","medical procedures","electronic health records","pharmacology"],
    "2221": ["patient care","nursing procedures","clinical assessment","medication administration","health monitoring"],
    "2310": ["curriculum development","educational assessment","teaching","academic research","learning design"],
    "2411": ["financial analysis","accounting","financial modelling","audit","Excel/spreadsheet"],
    "2421": ["project management","Agile","stakeholder management","business analysis","requirements gathering"],
    "2423": ["talent acquisition","employee onboarding","performance management","HRIS","labour law"],
    "2431": ["digital marketing","SEO/SEM","content creation","social media marketing","market analysis"],
    "2433": ["customer relationship management","B2B sales","negotiation","Salesforce","sales forecasting"],
    "2511": ["SQL","data modelling","database design","ETL","data warehousing"],
    "2512": ["software development","object-oriented programming","debugging","version control","API design"],
    "2519": ["machine learning","cloud infrastructure","Python","Docker/Kubernetes","CI/CD"],
    "2611": ["legal research","contract drafting","regulatory compliance","litigation","legal writing"],
    "3323": ["prospecting","cold outreach","pipeline management","CRM","objection handling"],
    "3512": ["test automation","quality assurance","bug tracking","test planning","Selenium/Cypress"],
    "3514": ["customer success","onboarding","product knowledge","issue resolution","customer retention"],
    "4120": ["calendar management","communication","document management","office software","administrative support"],
  };
  const skillMap = {}; // isco4 → string[]
  for (const [isco, skills] of Object.entries(ISCO_SKILLS)) skillMap[isco] = skills;

  // Merge sigMap + postMap → unified demand entries
  const allKeys = new Set([...Object.keys(sigMap), ...Object.keys(postMap)]);

  const forecastRows = [];
  for (const key of allKeys) {
    const [isco4, cc2] = key.split(":");
    const major   = isco4.slice(0, 1);
    const cc3     = ISO2_TO_ILO3[cc2] ?? null;
    const sig     = sigMap[key] ?? { count: 0, score: 0.3 };
    const posting = postMap[key] ?? 0;

    // Supply: prefer country-specific, fallback world
    const supply  = (cc3 && supplyMajor[`${major}:${cc3}`]) ?? supplyWorld[major] ?? null;
    const wage    = wageMap[major] ?? null;
    const skills  = skillMap[isco4] ?? skillMap[`${major}000`] ?? [];

    // demand_score: weighted sum of signal strength + posting velocity (0-100)
    const signalScore  = Math.min(sig.count * sig.score * 8, 60);
    const postingScore = Math.min(posting * 0.01, 40);
    const demand       = Math.round(signalScore + postingScore);

    const vid = `forecast:${YEAR}:${isco4}:${cc2}`;
    forecastRows.push([
      vid, isco4, cc2, YEAR,
      demand, supply, wage, "USD",
      JSON.stringify(["permanent", "contract", "dispatch"]),
      JSON.stringify(skills),
      sig.count, posting,
      NOW,
    ]);
  }

  console.log(`[press] forecasts computed=${forecastRows.length}`);

  if (!DRY_RUN && forecastRows.length > 0) {
    // Delete old forecasts for this period
    await query(`DELETE FROM vertex_demand_forecast WHERE period = '${YEAR}'`);

    const cols = ["vertex_id","isco_code","country","period","demand_score","supply_size_k",
                  "typical_salary","salary_currency","engagement_types","top_skills",
                  "press_signal_count","posting_count","computed_at"];

    for (let i = 0; i < forecastRows.length; i += 200) {
      const batch = forecastRows.slice(i, i + 200);
      const ph = []; const vals = []; let p = 1;
      for (const row of batch) {
        ph.push(`(${row.map(() => `$${p++}`).join(",")})`);
        vals.push(...row);
      }
      await query(`INSERT INTO vertex_demand_forecast (${cols.join(",")}) VALUES ${ph.join(",")}`, vals);
    }
    console.log(`[press] forecasts written=${forecastRows.length}`);
  }

  // Print top demand forecast
  const topForecasts = forecastRows
    .sort((a, b) => b[4] - a[4])
    .slice(0, 15);
  console.log("[press] top demand forecasts:");
  for (const f of topForecasts) {
    const skills = JSON.parse(f[9] ?? "[]").slice(0, 2).join(", ");
    console.log(`  isco=${f[1]} country=${f[2]} demand_score=${f[4]?.toFixed(1)} supply_k=${f[5]?.toFixed(0)} wage_usd=${f[6]?.toFixed(0)} skills=[${skills}]`);
  }

  return forecastRows;
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`[press] start  step=${STEP}  dry-run=${DRY_RUN}  year=${YEAR}`);
  const t0 = Date.now();

  let signalCount = 0, forecasts = [];

  if (STEP === "all" || STEP === "signals")   signalCount = await stepSignals();
  if (STEP === "all" || STEP === "forecasts") forecasts   = await stepForecasts();

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`[press] done  elapsed=${elapsed}s`);

  if (!DRY_RUN) {
    const { rows } = await query(`
      SELECT COUNT(*) AS signals FROM vertex_press_signal
    `);
    const { rows: fc } = await query(`
      SELECT COUNT(*) AS forecasts FROM vertex_demand_forecast WHERE period = '${YEAR}'
    `);
    console.log(`[press] vertex_press_signal total=${rows[0].signals}`);
    console.log(`[press] vertex_demand_forecast[${YEAR}] total=${fc[0].forecasts}`);
  }

  await writeFile("/tmp/press-signals-summary.json", JSON.stringify({
    year: YEAR, step: STEP, dry_run: DRY_RUN,
    new_signals: signalCount,
    forecasts_computed: Array.isArray(forecasts) ? forecasts.length : 0,
    elapsed_s: elapsed,
  }, null, 2));

  if (_pool) await _pool.end();
}

main().catch(e => { console.error(e); process.exit(1); });
