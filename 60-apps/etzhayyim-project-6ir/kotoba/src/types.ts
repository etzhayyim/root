/**
 * 6ir kotoba — investor-relations intelligence record types.
 *
 * Per ADR-2606011400. 6ir ("6-figure IR") serves PUBLIC investor-relations
 * open-data: companies + filings (10-K/10-Q/8-K…) + earnings + analyst coverage.
 * Registry on AT PDS records (replaces the dispatcher's RW backing). ADR-2605172000
 * kotoba.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean public open-data — no PII custody (only
 * public company/filing data + analyst DIDs), no settlement, no fulfillment
 * liability. etzhayyim front. Capabilities mirror kotodama.jsonld:
 * listCompanies / getCompany / searchCompanies / listFilings / getFiling /
 * listEarnings / submitAnalysis / listAlerts(→listAnalyses).
 *
 * Monetary values are decimal STRINGS in micros (AT-Lexicon has no float; bigint
 * is not JSON-serializable). EPS may be negative ("-230000"); revenue / price
 * targets are non-negative.
 *
 * Identity hierarchy:
 *   did:web:6ir.etzhayyim.com                          — controller
 *   did:web:6ir.etzhayyim.com:company:{ticker}         — a company
 *   did:web:6ir.etzhayyim.com:filing:{filingId}        — a filing
 *   did:web:6ir.etzhayyim.com:earnings:{earningsId}    — an earnings report
 *   did:web:6ir.etzhayyim.com:analysis:{analysisId}    — an analyst note
 */

export const SIXIR_DID_PREFIX = "did:web:6ir.etzhayyim.com:" as const;

export const COMPANY_COLLECTION = "com.etzhayyim.apps.sixir.company";
export const FILING_COLLECTION = "com.etzhayyim.apps.sixir.filing";
export const EARNINGS_COLLECTION = "com.etzhayyim.apps.sixir.earnings";
export const ANALYSIS_COLLECTION = "com.etzhayyim.apps.sixir.analysis";

// ─── Company ────────────────────────────────────────────────────────

export interface CompanyRecord {
  did: string;
  /** Canonical key — exchange ticker (upper). */
  ticker: string;
  name: string;
  /** SEC CIK (optional). */
  cik?: string;
  exchange?: string;
  sector?: string;
  createdAt: string;
}
export interface CompanyView extends CompanyRecord {
  companyUri: string;
}
export interface DefineCompanyInput {
  ticker: string;
  name: string;
  cik?: string;
  exchange?: string;
  sector?: string;
}
export interface DefineCompanyOutput {
  status: "defined" | "alreadyExists" | "rejected";
  companyUri?: string;
  did?: string;
  ticker?: string;
  error?: string;
}
export interface GetCompanyInput {
  ticker: string;
}
export interface GetCompanyOutput {
  company?: CompanyView;
  error?: string;
}
export interface ListCompaniesInput {
  exchange?: string;
  sector?: string;
  /** App-layer substring match over ticker/name (AT PDS has no text search). */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListCompaniesOutput {
  items: CompanyView[];
  cursor?: string;
  total: number;
}

// ─── Filing ─────────────────────────────────────────────────────────

export type FormType = "10-K" | "10-Q" | "8-K" | "S-1" | "20-F" | "6-K" | "DEF 14A" | "other";

export interface FilingRecord {
  did: string;
  filingId: string;
  /** FK → company ticker. */
  ticker: string;
  formType: FormType;
  filedAt: string;
  /** Period covered (YYYY-MM-DD), optional. */
  periodEnd?: string;
  /** IPFS CID or source URL of the document. */
  documentRef?: string;
  createdAt: string;
}
export interface FilingView extends FilingRecord {
  filingUri: string;
}
export interface AddFilingInput {
  filingId: string;
  ticker: string;
  formType: FormType;
  filedAt: string;
  periodEnd?: string;
  documentRef?: string;
}
export interface AddFilingOutput {
  status: "added" | "alreadyExists" | "rejected" | "companyNotFound";
  filingUri?: string;
  did?: string;
  filingId?: string;
  error?: string;
}
export interface GetFilingInput {
  filingId: string;
}
export interface GetFilingOutput {
  filing?: FilingView;
  error?: string;
}
export interface ListFilingsInput {
  ticker?: string;
  formType?: FormType;
  since?: string;
  limit?: number;
  cursor?: string;
}
export interface ListFilingsOutput {
  items: FilingView[];
  cursor?: string;
  total: number;
}

// ─── Earnings ───────────────────────────────────────────────────────

export interface EarningsRecord {
  did: string;
  earningsId: string;
  /** FK → company ticker. */
  ticker: string;
  /** Fiscal period label, e.g. "2026Q1". */
  fiscalPeriod: string;
  reportedAt: string;
  /** EPS in micros, decimal string; may be negative. */
  epsMicros: string;
  /** Revenue in micros, decimal string; non-negative. */
  revenueMicros: string;
  createdAt: string;
}
export interface EarningsView extends EarningsRecord {
  earningsUri: string;
}
export interface RecordEarningsInput {
  earningsId: string;
  ticker: string;
  fiscalPeriod: string;
  reportedAt: string;
  epsMicros: string;
  revenueMicros: string;
}
export interface RecordEarningsOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "companyNotFound";
  earningsUri?: string;
  did?: string;
  earningsId?: string;
  error?: string;
}
export interface ListEarningsInput {
  ticker?: string;
  since?: string;
  limit?: number;
  cursor?: string;
}
export interface ListEarningsOutput {
  items: EarningsView[];
  cursor?: string;
  total: number;
}

// ─── Analyst coverage ───────────────────────────────────────────────

export type Rating = "strongBuy" | "buy" | "hold" | "sell" | "strongSell";

export interface AnalysisRecord {
  did: string;
  analysisId: string;
  /** FK → company ticker. */
  ticker: string;
  analystDid: string;
  rating: Rating;
  /** Price target in micros, decimal string, non-negative (optional). */
  priceTargetMicros?: string;
  note?: string;
  createdAt: string;
}
export interface AnalysisView extends AnalysisRecord {
  analysisUri: string;
}
export interface SubmitAnalysisInput {
  analysisId: string;
  ticker: string;
  analystDid: string;
  rating: Rating;
  priceTargetMicros?: string;
  note?: string;
}
export interface SubmitAnalysisOutput {
  status: "submitted" | "alreadyExists" | "rejected" | "companyNotFound";
  analysisUri?: string;
  did?: string;
  analysisId?: string;
  error?: string;
}
export interface ListAnalysesInput {
  ticker?: string;
  rating?: Rating;
  analystDid?: string;
  limit?: number;
  cursor?: string;
}
export interface ListAnalysesOutput {
  items: AnalysisView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  companyCount?: number;
  filingCount?: number;
  earningsCount?: number;
  analysisCount?: number;
  filingsByForm?: Record<string, number>;
  analysesByRating?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const FORM_TYPES: ReadonlySet<string> = new Set([
  "10-K", "10-Q", "8-K", "S-1", "20-F", "6-K", "DEF 14A", "other",
]);
export const RATINGS: ReadonlySet<string> = new Set([
  "strongBuy", "buy", "hold", "sell", "strongSell",
]);

/** Non-negative integer string (micros). */
export function isUintString(s: string): boolean {
  return /^\d+$/.test(s);
}
/** Signed integer string (micros) — EPS may be negative. */
export function isIntStringSigned(s: string): boolean {
  return /^-?\d+$/.test(s);
}
export function isValidTicker(s: string): boolean {
  return /^[A-Z0-9.\-]{1,12}$/.test(s);
}

export function companyDidFor(ticker: string): string {
  return `${SIXIR_DID_PREFIX}company:${ticker.toLowerCase()}`;
}
export function companyRkey(ticker: string): string {
  return `company-${ticker.toLowerCase()}`;
}
export function filingDidFor(id: string): string {
  return `${SIXIR_DID_PREFIX}filing:${id.toLowerCase()}`;
}
export function filingRkey(id: string): string {
  return `filing-${id.toLowerCase()}`;
}
export function earningsDidFor(id: string): string {
  return `${SIXIR_DID_PREFIX}earnings:${id.toLowerCase()}`;
}
export function earningsRkey(id: string): string {
  return `earnings-${id.toLowerCase()}`;
}
export function analysisDidFor(id: string): string {
  return `${SIXIR_DID_PREFIX}analysis:${id.toLowerCase()}`;
}
export function analysisRkey(id: string): string {
  return `analysis-${id.toLowerCase()}`;
}
