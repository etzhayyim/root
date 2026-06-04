#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  SUPERSEDED — DO NOT RUN ON THE RELIGIOUS-CORP SUBSTRATE              ║
 * ║                                                                       ║
 * ║  Status: pre-religious-corp commercial-fund era artifact (RisingWave  ║
 * ║          + vertex_* graph schema, neither of which is part of the     ║
 * ║          current substrate per ADR-2605262130 + ADR-2605172000).      ║
 * ║                                                                       ║
 * ║  Superseded by: ADR-2605263800 (Global corporate-disclosure ingestion ║
 * ║                 via IPFS-pinned DataLad subdatasets) — W1 fetcher:    ║
 * ║                 70-tools/e7m-dataset/src/e7m_dataset/fetchers/        ║
 * ║                 sec_edgar.py                                          ║
 * ║                                                                       ║
 * ║  Why superseded (religious-corp substrate-fit):                       ║
 * ║    - DataLad subdataset + IPFS-pin storage (NOT RisingWave)           ║
 * ║    - com.etzhayyim.corp.{registryAttestation,disclosureAttestation,   ║
 * ║      filingEvent} Lexicon records (NOT vertex_* PG tables)            ║
 * ║    - Passive-only invariant per ADR-2605262400 §7 (no full live API   ║
 * ║      enumeration; uses SEC quarterly-index bulk archive only)         ║
 * ║    - CorpRegistrySensor / CorpDisclosureSensor / CorpFilingEventSensor║
 * ║      Protocols (pymagatama.organism.sensors.corp.*) consume the       ║
 * ║      pinned subdataset, not direct API output                         ║
 * ║    - Charter Rider §2(e)+§2(c) vendor-commercial-terminal deny-list   ║
 * ║      enforced at recipe lint (Bloomberg Terminal / Refinitiv / FactSet║
 * ║      / Moody's Orbis / D&B / Pitchbook / Crunchbase Pro PROHIBITED)   ║
 * ║                                                                       ║
 * ║  Operator action:                                                     ║
 * ║    - For new ingestion: use `e7m-dataset pull sec-edgar` (W1)         ║
 * ║    - For legacy data already in RW: read ADR-2605263800 §7 W4 plan    ║
 * ║                                                                       ║
 * ║  Removal scheduled: ADR-2605263800 W4 deliverable (after sensor       ║
 * ║                     parity is verified at W3).                        ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * SEC EDGAR disclosure ingest -> vertex_company_filing / vertex_company_fact.
 *
 * Purpose:
 *   Extend `vertex_legal_entity` anchors for US listed/reporting companies with:
 *   - filing metadata from SEC submissions API
 *   - selected structured facts from SEC companyfacts API
 *
 * Inputs:
 *   --ticker MSFT         Resolve CIK from SEC ticker list
 *   --cik 789019          Resolve company directly
 *   --filing-limit 20     Max recent filings to insert
 *   --facts-limit 50      Max fact rows to insert
 *   --dry-run             Fetch/resolve only, no writes
 *
 * Data sources:
 *   https://www.sec.gov/files/company_tickers.json
 *   https://data.sec.gov/submissions/CIK##########.json
 *   https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
 */

const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");

const RW_CONN = process.env.RW_CONN ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const COLLECTOR_DID = "did:web:legal-entity.etzhayyim.com";
const USER_AGENT = process.env.SEC_USER_AGENT ?? "etzhayyim-legal-entity/1.0 legal-entity@etzhayyim.com";

const args = process.argv.slice(2);
const getArg = (k, d = "") => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1] ?? d;
};
const hasFlag = (k) => args.includes(`--${k}`);

const TICKER = getArg("ticker", "").trim().toUpperCase();
const RAW_CIK = getArg("cik", "").trim();
const FILING_LIMIT = Math.max(1, parseInt(getArg("filing-limit", "20"), 10) || 20);
const FACT_LIMIT = Math.max(1, parseInt(getArg("facts-limit", "50"), 10) || 50);
const DRY_RUN = hasFlag("dry-run");

if (!TICKER && !RAW_CIK) {
  console.error("usage: node 70-tools/scripts/sec-edgar-disclosure-ingest.mjs --ticker MSFT | --cik 789019 [--filing-limit 20] [--facts-limit 50] [--dry-run]");
  process.exit(2);
}

let _pool = null;
async function pool() {
  if (_pool) return _pool;
  _pool = new pg.Pool({ connectionString: RW_CONN, max: 2, statement_timeout: 60000 });
  return _pool;
}

function normalizeCik(v) {
  const digits = String(v ?? "").replace(/\D/g, "");
  if (!digits) return "";
  return digits.padStart(10, "0");
}

function secFetchJson(url) {
  return fetch(url, {
    headers: {
      "User-Agent": USER_AGENT,
      "Accept": "application/json",
    },
    signal: AbortSignal.timeout(30000),
  }).then(async (resp) => {
    if (!resp.ok) throw new Error(`SEC ${resp.status} for ${url}: ${(await resp.text()).slice(0, 200)}`);
    return resp.json();
  });
}

function secFetchText(url) {
  return fetch(url, {
    headers: {
      "User-Agent": USER_AGENT,
      "Accept": "text/html,application/xhtml+xml,text/plain",
    },
    signal: AbortSignal.timeout(30000),
  }).then(async (resp) => {
    if (!resp.ok) throw new Error(`SEC ${resp.status} for ${url}: ${(await resp.text()).slice(0, 200)}`);
    return resp.text();
  });
}

async function resolveCikFromTicker(ticker) {
  const data = await secFetchJson("https://www.sec.gov/files/company_tickers.json");
  for (const item of Object.values(data)) {
    if (String(item.ticker ?? "").toUpperCase() === ticker) {
      return normalizeCik(item.cik_str);
    }
  }
  throw new Error(`ticker not found in SEC ticker list: ${ticker}`);
}

async function resolveCompanyAnchor(cik) {
  const pgPool = await pool();
  const q = await pgPool.query(
    `SELECT vertex_id, name, country, jurisdiction
       FROM vertex_legal_entity
      WHERE source = 'edgar_usa'
        AND (source_record_id = $1 OR registration_number = $1 OR rkey = $1)
      LIMIT 1`,
    [String(parseInt(cik, 10))],
  );
  if (q.rows[0]) return q.rows[0];
  return {
    vertex_id: `le:edgar_usa:${cik}`,
    name: null,
    country: "US",
    jurisdiction: "US",
  };
}

function buildRecentFilings(submissions, companyDid, cik) {
  const recent = submissions?.filings?.recent;
  if (!recent) return [];
  const forms = recent.form ?? [];
  const accessionNumbers = recent.accessionNumber ?? [];
  const filingDates = recent.filingDate ?? [];
  const reportDates = recent.reportDate ?? [];
  const primaryDocuments = recent.primaryDocument ?? [];
  const primaryDocDescriptions = recent.primaryDocDescription ?? [];

  const allowedForms = new Set(["10-K", "10-Q", "20-F", "40-F", "6-K", "8-K"]);
  const out = [];

  for (let i = 0; i < forms.length; i++) {
    const form = String(forms[i] ?? "");
    if (!allowedForms.has(form)) continue;
    const accessionNo = String(accessionNumbers[i] ?? "");
    if (!accessionNo) continue;
    const accessionCompact = accessionNo.replace(/-/g, "");
    const filingDate = String(filingDates[i] ?? "");
    const reportDate = String(reportDates[i] ?? "");
    const primaryDocument = String(primaryDocuments[i] ?? "");
    const filingUrl = primaryDocument
      ? `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${accessionCompact}/${primaryDocument}`
      : `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${accessionCompact}/`;

    const fiscalYear = /^\d{4}-/.test(reportDate) ? parseInt(reportDate.slice(0, 4), 10) : null;
    const fiscalQuarter = form === "10-Q"
      ? Math.max(1, Math.min(4, Math.ceil((new Date(reportDate || filingDate).getUTCMonth() + 1) / 3)))
      : null;

    out.push({
      vertex_id: `filing:edgar:${cik}:${accessionCompact}`,
      rkey: accessionCompact.slice(0, 63),
      repo: COLLECTOR_DID,
      label: "com.etzhayyim.apps.legalEntity.companyFiling",
      company_did: companyDid,
      filing_source: "sec_edgar",
      filing_type: form,
      filing_date: filingDate || null,
      period_start: null,
      period_end: reportDate || null,
      fiscal_year: fiscalYear,
      fiscal_quarter: fiscalQuarter,
      accession_no: accessionNo,
      filing_url: filingUrl,
      issuer_name: submissions?.name ?? null,
      issuer_ticker: Array.isArray(submissions?.tickers) ? submissions.tickers[0] ?? null : null,
      issuer_exchange: Array.isArray(submissions?.exchanges) ? submissions.exchanges[0] ?? null : null,
      country: "US",
      language: "en",
      source_license: "public-domain",
      ingested_at: new Date().toISOString(),
      props: JSON.stringify({
        secPrimaryDocDescription: primaryDocDescriptions[i] ?? "",
      }),
    });
  }

  return out.slice(0, FILING_LIMIT);
}

const FACT_SPECS = [
  {
    canonical: "revenue",
    namespace: "us-gaap",
    concepts: [
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "Revenues",
      "SalesRevenueNet",
      "SalesRevenueGoodsNet",
    ],
  },
  {
    canonical: "employee_count",
    namespace: "dei",
    concepts: [
      "EntityNumberOfEmployees",
      "NumberOfEmployees",
    ],
  },
  {
    canonical: "assets",
    namespace: "us-gaap",
    concepts: [
      "Assets",
    ],
  },
  {
    canonical: "net_income",
    namespace: "us-gaap",
    concepts: [
      "NetIncomeLoss",
      "ProfitLoss",
    ],
  },
];

function pickFactUnits(conceptNode) {
  if (!conceptNode?.units) return [];
  const preferred = ["USD", "USD/shares", "pure", "shares"];
  const unitKeys = Object.keys(conceptNode.units);
  const ordered = [...preferred.filter((u) => unitKeys.includes(u)), ...unitKeys.filter((u) => !preferred.includes(u))];
  return ordered.flatMap((unit) => (conceptNode.units[unit] ?? []).map((item) => ({ unit, ...item })));
}

function buildFacts(companyFacts, companyDid, cik) {
  const out = [];

  for (const spec of FACT_SPECS) {
    const nsRoot = companyFacts?.facts?.[spec.namespace];
    if (!nsRoot) continue;

    for (const conceptName of spec.concepts) {
      const concept = nsRoot[conceptName];
      if (!concept) continue;

      const values = pickFactUnits(concept)
        .filter((item) => item?.val !== undefined && item?.val !== null)
        .sort((a, b) => String(b.end ?? b.fy ?? "").localeCompare(String(a.end ?? a.fy ?? "")));

      for (const item of values) {
        const end = String(item.end ?? item.frame ?? item.fy ?? "");
        const fy = item.fy ? Number(item.fy) : (/^\d{4}-/.test(end) ? parseInt(end.slice(0, 4), 10) : null);
        const fq = item.fp && /^Q[1-4]$/.test(item.fp) ? parseInt(item.fp.slice(1), 10) : null;
        const accessionNo = String(item.accn ?? "");
        const accessionCompact = accessionNo.replace(/-/g, "");
        const filingDid = accessionCompact ? `filing:edgar:${cik}:${accessionCompact}` : null;
        const value = typeof item.val === "number" ? item.val : Number(item.val);

        out.push({
          vertex_id: `fact:edgar:${cik}:${spec.canonical}:${accessionCompact || end || out.length}`,
          rkey: `${spec.canonical}-${accessionCompact || end}`.replace(/[^a-zA-Z0-9_-]/g, "-").slice(0, 63),
          repo: COLLECTOR_DID,
          label: "com.etzhayyim.apps.legalEntity.companyFact",
          company_did: companyDid,
          filing_did: filingDid,
          fact_namespace: spec.namespace,
          fact_name: spec.canonical,
          fact_value_num: Number.isFinite(value) ? value : null,
          fact_value_text: Number.isFinite(value) ? null : String(item.val ?? ""),
          unit: item.unit ?? null,
          currency: String(item.unit ?? "").toUpperCase() === "USD" ? "USD" : null,
          period_start: item.start ?? null,
          period_end: item.end ?? null,
          as_of_date: item.end ?? item.frame ?? null,
          fiscal_year: fy,
          fiscal_quarter: fq,
          source_url: accessionCompact
            ? `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${accessionCompact}/`
            : "https://data.sec.gov/api/xbrl/companyfacts/",
          source_method: "sec_companyfacts",
          confidence: 0.95,
          ingested_at: new Date().toISOString(),
        });
      }
      break;
    }
  }

  return out
    .sort((a, b) => String(b.as_of_date ?? "").localeCompare(String(a.as_of_date ?? "")))
    .slice(0, FACT_LIMIT);
}

function decodeHtmlText(html) {
  return String(html ?? "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&#160;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function parseUsLongDateToIso(value) {
  const m = String(value ?? "").match(/^([A-Za-z]+) (\d{1,2}), (\d{4})$/);
  if (!m) return "";
  const monthNames = {
    january: "01", february: "02", march: "03", april: "04",
    may: "05", june: "06", july: "07", august: "08",
    september: "09", october: "10", november: "11", december: "12",
  };
  const mm = monthNames[m[1].toLowerCase()];
  if (!mm) return "";
  return `${m[3]}-${mm}-${m[2].padStart(2, "0")}`;
}

async function buildEmployeeFallbackFact(submissions, companyDid, cik, existingFacts) {
  if (existingFacts.some((row) => row.fact_name === "employee_count")) return null;
  const recent = submissions?.filings?.recent;
  if (!recent) return null;

  for (let i = 0; i < (recent.form?.length ?? 0); i++) {
    const form = String(recent.form?.[i] ?? "");
    if (!["10-K", "20-F", "40-F"].includes(form)) continue;
    const accessionNo = String(recent.accessionNumber?.[i] ?? "");
    if (!accessionNo) continue;
    const accessionCompact = accessionNo.replace(/-/g, "");
    const primaryDocument = String(recent.primaryDocument?.[i] ?? "");
    const filingUrl = primaryDocument
      ? `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${accessionCompact}/${primaryDocument}`
      : `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${accessionCompact}/`;

    let text = "";
    try {
      text = decodeHtmlText(await secFetchText(filingUrl));
    } catch {
      continue;
    }

    const patterns = [
      /As of ([A-Za-z]+ \d{1,2}, \d{4}), we employed approximately ([\d,]+) people on a full-time basis/i,
      /As of ([A-Za-z]+ \d{1,2}, \d{4}), we employed approximately ([\d,]+) employees/i,
      /we employed approximately ([\d,]+) people on a full-time basis/i,
      /we employed approximately ([\d,]+) employees/i,
    ];
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (!match) continue;
      const asOfDateText = match[1] && /, \d{4}$/.test(match[1]) ? match[1] : String(recent.reportDate?.[i] ?? recent.filingDate?.[i] ?? "");
      const employeeCount = Number(String(match[2] ?? match[1] ?? "").replace(/,/g, ""));
      if (!Number.isFinite(employeeCount)) continue;
      const isoDate = /^\d{4}-\d{2}-\d{2}$/.test(asOfDateText)
        ? asOfDateText
        : (parseUsLongDateToIso(asOfDateText) || String(recent.reportDate?.[i] ?? recent.filingDate?.[i] ?? ""));
      return {
        vertex_id: `fact:edgar:${cik}:employee_count:${accessionCompact || isoDate || "fallback"}`,
        rkey: `employee_count-${accessionCompact || isoDate || "fallback"}`.replace(/[^a-zA-Z0-9_-]/g, "-").slice(0, 63),
        repo: COLLECTOR_DID,
        label: "com.etzhayyim.apps.legalEntity.companyFact",
        company_did: companyDid,
        filing_did: accessionCompact ? `filing:edgar:${cik}:${accessionCompact}` : null,
        fact_namespace: "sec-text",
        fact_name: "employee_count",
        fact_value_num: employeeCount,
        fact_value_text: null,
        unit: "employees",
        currency: null,
        period_start: null,
        period_end: isoDate || null,
        as_of_date: isoDate || null,
        fiscal_year: /^\d{4}-/.test(isoDate) ? parseInt(isoDate.slice(0, 4), 10) : null,
        fiscal_quarter: null,
        source_url: filingUrl,
        source_method: "sec_filing_text",
        confidence: 0.9,
        ingested_at: new Date().toISOString(),
      };
    }
  }

  return null;
}

async function insertRows(table, cols, rows) {
  if (!rows.length) return 0;
  if (DRY_RUN) return rows.length;
  const pgPool = await pool();
  let inserted = 0;
  for (const row of rows) {
    const vertexId = row.vertex_id ?? null;
    if (!vertexId) continue;
    const exists = await pgPool.query(
      `SELECT 1 FROM ${table} WHERE vertex_id = $1 LIMIT 1`,
      [vertexId],
    );
    if (exists.rowCount) continue;
    const vals = cols.map((c) => row[c] ?? null);
    const placeholders = vals.map((_, i) => `$${i + 1}`).join(",");
    const result = await pgPool.query(
      `INSERT INTO ${table} (${cols.join(",")}) VALUES (${placeholders})`,
      vals,
    );
    inserted += Number(result.rowCount ?? 0);
  }
  return inserted;
}

async function main() {
  const cik = RAW_CIK ? normalizeCik(RAW_CIK) : await resolveCikFromTicker(TICKER);
  const companyAnchor = await resolveCompanyAnchor(cik);

  console.log(`[sec-disclosure] cik=${cik} ticker=${TICKER || "-"} company_did=${companyAnchor.vertex_id} dry-run=${DRY_RUN}`);

  const submissions = await secFetchJson(`https://data.sec.gov/submissions/CIK${cik}.json`);
  const companyFacts = await secFetchJson(`https://data.sec.gov/api/xbrl/companyfacts/CIK${cik}.json`);

  const filings = buildRecentFilings(submissions, companyAnchor.vertex_id, cik);
  const facts = buildFacts(companyFacts, companyAnchor.vertex_id, cik);
  const employeeFallback = await buildEmployeeFallbackFact(submissions, companyAnchor.vertex_id, cik, facts);
  if (employeeFallback) facts.unshift(employeeFallback);

  const filingCols = [
    "vertex_id", "rkey", "repo", "label", "company_did",
    "filing_source", "filing_type", "filing_date", "period_start", "period_end",
    "fiscal_year", "fiscal_quarter", "accession_no", "filing_url",
    "issuer_name", "issuer_ticker", "issuer_exchange", "country", "language",
    "source_license", "ingested_at", "props",
  ];
  const factCols = [
    "vertex_id", "rkey", "repo", "label", "company_did", "filing_did",
    "fact_namespace", "fact_name", "fact_value_num", "fact_value_text",
    "unit", "currency", "period_start", "period_end", "as_of_date",
    "fiscal_year", "fiscal_quarter", "source_url", "source_method", "confidence", "ingested_at",
  ];

  const insertedFilings = await insertRows("vertex_company_filing", filingCols, filings);
  const insertedFacts = await insertRows("vertex_company_fact", factCols, facts);

  const summary = {
    cik,
    ticker: TICKER || submissions?.tickers?.[0] || null,
    companyDid: companyAnchor.vertex_id,
    filingsFetched: filings.length,
    factsFetched: facts.length,
    filingsInserted: insertedFilings,
    factsInserted: insertedFacts,
    dryRun: DRY_RUN,
  };

  console.log(JSON.stringify(summary, null, 2));
  if (_pool) await _pool.end();
}

main().catch(async (err) => {
  console.error(err?.stack || String(err));
  if (_pool) await _pool.end();
  process.exit(1);
});
