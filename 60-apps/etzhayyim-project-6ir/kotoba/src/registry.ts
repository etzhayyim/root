/**
 * 6ir kotoba — company + filing + earnings + analyst-coverage registries
 * + coverage. AT PDS records (no RW). Filings / earnings / analyses FK-reference
 * an existing company (by ticker). Public IR open-data; monetary values are
 * decimal-string micros.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ANALYSIS_COLLECTION,
  COMPANY_COLLECTION,
  EARNINGS_COLLECTION,
  FILING_COLLECTION,
  FORM_TYPES,
  RATINGS,
  analysisDidFor,
  analysisRkey,
  companyDidFor,
  companyRkey,
  earningsDidFor,
  earningsRkey,
  filingDidFor,
  filingRkey,
  isIntStringSigned,
  isUintString,
  isValidTicker,
  type AddFilingInput,
  type AddFilingOutput,
  type AnalysisRecord,
  type AnalysisView,
  type CompanyRecord,
  type CompanyView,
  type CoverageInput,
  type CoverageOutput,
  type DefineCompanyInput,
  type DefineCompanyOutput,
  type EarningsRecord,
  type EarningsView,
  type FilingRecord,
  type FilingView,
  type GetCompanyInput,
  type GetCompanyOutput,
  type GetFilingInput,
  type GetFilingOutput,
  type ListAnalysesInput,
  type ListAnalysesOutput,
  type ListCompaniesInput,
  type ListCompaniesOutput,
  type ListEarningsInput,
  type ListEarningsOutput,
  type ListFilingsInput,
  type ListFilingsOutput,
  type RecordEarningsInput,
  type RecordEarningsOutput,
  type SubmitAnalysisInput,
  type SubmitAnalysisOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

// ─── Company ────────────────────────────────────────────────────────

export async function defineCompany(e: Etzhayyim, input: DefineCompanyInput): Promise<DefineCompanyOutput> {
  if (!input.ticker || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const ticker = input.ticker.toUpperCase();
  if (!isValidTicker(ticker)) return { status: "rejected", error: "invalidTicker" };
  const rkey = companyRkey(ticker);
  const existing = await e.read<CompanyRecord>({ collection: COMPANY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", companyUri: existing.records[0].uri, did: existing.records[0].value.did, ticker };
  }
  const did = companyDidFor(ticker);
  const record: CompanyRecord = {
    did,
    ticker,
    name: input.name,
    cik: input.cik,
    exchange: input.exchange,
    sector: input.sector,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: COMPANY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "defined", companyUri: receipt.uri, did, ticker };
}

export async function getCompany(e: Etzhayyim, input: GetCompanyInput): Promise<GetCompanyOutput> {
  if (!input.ticker) return { error: "invalidTicker" };
  const resp = await e.read<CompanyRecord>({ collection: COMPANY_COLLECTION, rkey: companyRkey(input.ticker.toUpperCase()) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { company: { ...r.value, companyUri: r.uri } };
}

export async function listCompanies(e: Etzhayyim, input: ListCompaniesInput = {}): Promise<ListCompaniesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CompanyRecord>({ collection: COMPANY_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: CompanyView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.exchange && v.exchange !== input.exchange) return false;
      if (input.sector && v.sector !== input.sector) return false;
      // App-layer substring search (AT PDS exact-match only, no CONTAINS).
      if (q && !(v.ticker.toLowerCase().includes(q) || v.name.toLowerCase().includes(q))) return false;
      return true;
    })
    .map((r) => ({ ...r.value, companyUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Filing ─────────────────────────────────────────────────────────

export async function addFiling(e: Etzhayyim, input: AddFilingInput): Promise<AddFilingOutput> {
  if (!input.filingId || !input.ticker || !input.filedAt) return { status: "rejected", error: "missingRequiredFields" };
  if (!FORM_TYPES.has(input.formType)) return { status: "rejected", error: "invalidFormType" };
  const ticker = input.ticker.toUpperCase();
  if (!(await exists(e, COMPANY_COLLECTION, companyRkey(ticker)))) {
    return { status: "companyNotFound", error: `companyNotFound:${ticker}` };
  }
  const rkey = filingRkey(input.filingId);
  const existing = await e.read<FilingRecord>({ collection: FILING_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", filingUri: existing.records[0].uri, did: existing.records[0].value.did, filingId: input.filingId };
  }
  const did = filingDidFor(input.filingId);
  const record: FilingRecord = {
    did,
    filingId: input.filingId,
    ticker,
    formType: input.formType,
    filedAt: input.filedAt,
    periodEnd: input.periodEnd,
    documentRef: input.documentRef,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: FILING_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", filingUri: receipt.uri, did, filingId: input.filingId };
}

export async function getFiling(e: Etzhayyim, input: GetFilingInput): Promise<GetFilingOutput> {
  if (!input.filingId) return { error: "invalidFilingId" };
  const resp = await e.read<FilingRecord>({ collection: FILING_COLLECTION, rkey: filingRkey(input.filingId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { filing: { ...r.value, filingUri: r.uri } };
}

export async function listFilings(e: Etzhayyim, input: ListFilingsInput = {}): Promise<ListFilingsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<FilingRecord>({ collection: FILING_COLLECTION, cursor: input.cursor, limit });
  const ticker = input.ticker?.toUpperCase();
  const items: FilingView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (ticker && v.ticker !== ticker) return false;
      if (input.formType && v.formType !== input.formType) return false;
      if (input.since && v.filedAt < input.since) return false;
      return true;
    })
    .map((r) => ({ ...r.value, filingUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Earnings ───────────────────────────────────────────────────────

export async function recordEarnings(e: Etzhayyim, input: RecordEarningsInput): Promise<RecordEarningsOutput> {
  if (!input.earningsId || !input.ticker || !input.fiscalPeriod || !input.reportedAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isIntStringSigned(input.epsMicros)) return { status: "rejected", error: "invalidEpsMicros" };
  if (!isUintString(input.revenueMicros)) return { status: "rejected", error: "invalidRevenueMicros" };
  const ticker = input.ticker.toUpperCase();
  if (!(await exists(e, COMPANY_COLLECTION, companyRkey(ticker)))) {
    return { status: "companyNotFound", error: `companyNotFound:${ticker}` };
  }
  const rkey = earningsRkey(input.earningsId);
  const existing = await e.read<EarningsRecord>({ collection: EARNINGS_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", earningsUri: existing.records[0].uri, did: existing.records[0].value.did, earningsId: input.earningsId };
  }
  const did = earningsDidFor(input.earningsId);
  const record: EarningsRecord = {
    did,
    earningsId: input.earningsId,
    ticker,
    fiscalPeriod: input.fiscalPeriod,
    reportedAt: input.reportedAt,
    epsMicros: input.epsMicros,
    revenueMicros: input.revenueMicros,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: EARNINGS_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", earningsUri: receipt.uri, did, earningsId: input.earningsId };
}

export async function listEarnings(e: Etzhayyim, input: ListEarningsInput = {}): Promise<ListEarningsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<EarningsRecord>({ collection: EARNINGS_COLLECTION, cursor: input.cursor, limit });
  const ticker = input.ticker?.toUpperCase();
  const items: EarningsView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (ticker && v.ticker !== ticker) return false;
      if (input.since && v.reportedAt < input.since) return false;
      return true;
    })
    .map((r) => ({ ...r.value, earningsUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Analyst coverage ───────────────────────────────────────────────

export async function submitAnalysis(e: Etzhayyim, input: SubmitAnalysisInput): Promise<SubmitAnalysisOutput> {
  if (!input.analysisId || !input.ticker || !input.analystDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.analystDid.startsWith("did:")) return { status: "rejected", error: "invalidAnalystDid" };
  if (!RATINGS.has(input.rating)) return { status: "rejected", error: "invalidRating" };
  if (input.priceTargetMicros != null && !isUintString(input.priceTargetMicros)) {
    return { status: "rejected", error: "invalidPriceTargetMicros" };
  }
  const ticker = input.ticker.toUpperCase();
  if (!(await exists(e, COMPANY_COLLECTION, companyRkey(ticker)))) {
    return { status: "companyNotFound", error: `companyNotFound:${ticker}` };
  }
  const rkey = analysisRkey(input.analysisId);
  const existing = await e.read<AnalysisRecord>({ collection: ANALYSIS_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", analysisUri: existing.records[0].uri, did: existing.records[0].value.did, analysisId: input.analysisId };
  }
  const did = analysisDidFor(input.analysisId);
  const record: AnalysisRecord = {
    did,
    analysisId: input.analysisId,
    ticker,
    analystDid: input.analystDid,
    rating: input.rating,
    priceTargetMicros: input.priceTargetMicros,
    note: input.note,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ANALYSIS_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "submitted", analysisUri: receipt.uri, did, analysisId: input.analysisId };
}

export async function listAnalyses(e: Etzhayyim, input: ListAnalysesInput = {}): Promise<ListAnalysesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AnalysisRecord>({ collection: ANALYSIS_COLLECTION, cursor: input.cursor, limit });
  const ticker = input.ticker?.toUpperCase();
  const items: AnalysisView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (ticker && v.ticker !== ticker) return false;
      if (input.rating && v.rating !== input.rating) return false;
      if (input.analystDid && v.analystDid !== input.analystDid) return false;
      return true;
    })
    .map((r) => ({ ...r.value, analysisUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

async function countAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const companyCount = await countAll<CompanyRecord>(e, COMPANY_COLLECTION, maxScan, () => {});
  const filingsByForm: Record<string, number> = {};
  const filingCount = await countAll<FilingRecord>(e, FILING_COLLECTION, maxScan, (v) => {
    filingsByForm[v.formType] = (filingsByForm[v.formType] ?? 0) + 1;
  });
  const earningsCount = await countAll<EarningsRecord>(e, EARNINGS_COLLECTION, maxScan, () => {});
  const analysesByRating: Record<string, number> = {};
  const analysisCount = await countAll<AnalysisRecord>(e, ANALYSIS_COLLECTION, maxScan, (v) => {
    analysesByRating[v.rating] = (analysesByRating[v.rating] ?? 0) + 1;
  });
  return {
    companyCount,
    filingCount,
    earningsCount,
    analysisCount,
    filingsByForm,
    analysesByRating,
    truncated:
      companyCount >= maxScan || filingCount >= maxScan || earningsCount >= maxScan || analysisCount >= maxScan,
  };
}
