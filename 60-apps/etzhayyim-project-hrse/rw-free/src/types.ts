/**
 * hrse rw-free — public cybersecurity freelance JOB-BOARD catalog (hiring
 * company + job posting).
 *
 * Per ADR-2606011400 (Consensys pattern, applied per-FUNCTION) + ADR-2605172400.
 *
 * SPLIT (this app is (c) mixed — a cybersecurity-specialized freelance-matching
 * marketplace, the lawfirm-style professional-services twin):
 *   PUBLIC (THIS PACKAGE) — the consumer-facing browse surface: open job
 *   postings (role, required skills, comp range, location, remote) + the public
 *   identity of the hiring company. No applicant/freelancer PII, no settlement,
 *   no fulfillment liability on the listing itself.
 *     → migrated to etzhayyim front (AT PDS records, replaces RW/Postgres).
 *
 *   MARKETPLACE BACKEND (STAYS etzhayyim, NOT in this package) — freelancer profiles
 *   (job-seeker PII → Custody), proposals / applications (candidate PII +
 *   matching → Custody/Liability), the matching engine, applicant evaluation,
 *   Clerk subscription / billing (→ Settlement), and placement (fulfillment
 *   liability). Consumed via consent-capability (the Infura model — matching
 *   engine living etzhayyim-side is the point).
 *
 * AT-Lexicon: no float. Comp ranges are decimal JPY STRINGS. The job posting
 * MUST carry only public listing data — never an applicant/freelancer field.
 *
 * Identity hierarchy:
 *   did:web:hrse.etzhayyim.com                       — controller
 *   did:web:hrse.etzhayyim.com:co:{companyId}        — a hiring company
 *   did:web:hrse.etzhayyim.com:job:{postingId}       — a job posting
 */

export const HRSE_DID_PREFIX = "did:web:hrse.etzhayyim.com:" as const;

export const COMPANY_COLLECTION = "com.etzhayyim.apps.hrse.company";
export const JOB_POSTING_COLLECTION = "com.etzhayyim.apps.hrse.jobPosting";

// ─── Enums ──────────────────────────────────────────────────────────

export type SecurityCategory =
  | "pentest"
  | "appsec"
  | "cloud-sec"
  | "soc"
  | "incident-response"
  | "grc"
  | "forensics"
  | "threat-intel"
  | "other";
export type Seniority = "junior" | "mid" | "senior" | "lead" | "principal" | "other";
export type EngagementType = "contract" | "part-time" | "full-time" | "project" | "other";

export const SECURITY_CATEGORIES: ReadonlySet<string> = new Set([
  "pentest",
  "appsec",
  "cloud-sec",
  "soc",
  "incident-response",
  "grc",
  "forensics",
  "threat-intel",
  "other",
]);
export const SENIORITIES: ReadonlySet<string> = new Set(["junior", "mid", "senior", "lead", "principal", "other"]);
export const ENGAGEMENT_TYPES: ReadonlySet<string> = new Set(["contract", "part-time", "full-time", "project", "other"]);

// ─── Company (public hiring-org identity) ───────────────────────────

export interface CompanyRecord {
  did: string;
  companyId: string;
  name: string;
  industry?: string;
  region?: string;
  website?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface CompanyView extends CompanyRecord {
  companyUri: string;
}
export interface RegisterCompanyInput {
  companyId: string;
  name: string;
  industry?: string;
  region?: string;
  website?: string;
  sourceUrl?: string;
}
export interface RegisterCompanyOutput {
  status: "registered" | "alreadyExists" | "rejected";
  companyUri?: string;
  did?: string;
  companyId?: string;
  error?: string;
}
export interface GetCompanyInput {
  companyId: string;
}
export interface GetCompanyOutput {
  company?: CompanyView;
  error?: string;
}
export interface ListCompaniesInput {
  region?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListCompaniesOutput {
  items: CompanyView[];
  cursor?: string;
  total: number;
}

// ─── Job posting (public listing — NO applicant PII) ────────────────

export interface JobPostingRecord {
  did: string;
  postingId: string;
  /** FK → company. */
  companyId: string;
  title: string;
  category: SecurityCategory;
  /** Public required-skills tags. */
  requiredSkills?: string[];
  seniority: Seniority;
  engagementType: EngagementType;
  /** Comp band, JPY (decimal strings), optional. */
  compMinJpy?: string;
  compMaxJpy?: string;
  location?: string;
  remote?: boolean;
  postedAt: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface JobPostingView extends JobPostingRecord {
  postingUri: string;
}
export interface AddJobPostingInput {
  postingId: string;
  companyId: string;
  title: string;
  category: SecurityCategory;
  seniority: Seniority;
  engagementType: EngagementType;
  postedAt: string;
  requiredSkills?: string[];
  compMinJpy?: string;
  compMaxJpy?: string;
  location?: string;
  remote?: boolean;
  sourceUrl?: string;
}
export interface AddJobPostingOutput {
  status: "added" | "alreadyExists" | "rejected" | "companyNotFound";
  postingUri?: string;
  did?: string;
  postingId?: string;
  error?: string;
}
export interface ListJobPostingsInput {
  companyId?: string;
  category?: SecurityCategory;
  seniority?: Seniority;
  engagementType?: EngagementType;
  remote?: boolean;
  /** App-layer substring search over title + required skills. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListJobPostingsOutput {
  items: JobPostingView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  companyCount?: number;
  jobPostingCount?: number;
  postingsByCategory?: Record<string, number>;
  postingsBySeniority?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUintString(s: string): boolean {
  return /^\d+$/.test(s);
}

export function companyDidFor(id: string): string {
  return `${HRSE_DID_PREFIX}co:${id.toLowerCase()}`;
}
export function companyRkey(id: string): string {
  return `co-${id.toLowerCase()}`;
}
export function postingDidFor(id: string): string {
  return `${HRSE_DID_PREFIX}job:${id.toLowerCase()}`;
}
export function postingRkey(id: string): string {
  return `job-${id.toLowerCase()}`;
}
