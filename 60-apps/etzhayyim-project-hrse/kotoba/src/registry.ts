/**
 * hrse kotoba — public company + jobPosting catalog + coverage.
 * AT PDS records (no RW). Postings FK→company. PUBLIC listing data only — the
 * job-seeker side (profiles/proposals/billing/placement) stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  COMPANY_COLLECTION,
  ENGAGEMENT_TYPES,
  JOB_POSTING_COLLECTION,
  SECURITY_CATEGORIES,
  SENIORITIES,
  companyDidFor,
  companyRkey,
  isUintString,
  postingDidFor,
  postingRkey,
  type AddJobPostingInput,
  type AddJobPostingOutput,
  type CompanyRecord,
  type CompanyView,
  type CoverageInput,
  type CoverageOutput,
  type GetCompanyInput,
  type GetCompanyOutput,
  type JobPostingRecord,
  type JobPostingView,
  type ListCompaniesInput,
  type ListCompaniesOutput,
  type ListJobPostingsInput,
  type ListJobPostingsOutput,
  type RegisterCompanyInput,
  type RegisterCompanyOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
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

// ─── Company ────────────────────────────────────────────────────────

export async function registerCompany(e: Etzhayyim, input: RegisterCompanyInput): Promise<RegisterCompanyOutput> {
  if (!input.companyId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = companyRkey(input.companyId);
  const existing = await e.read<CompanyRecord>({ collection: COMPANY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", companyUri: existing.records[0].uri, did: existing.records[0].value.did, companyId: input.companyId };
  }
  const did = companyDidFor(input.companyId);
  const record: CompanyRecord = {
    did,
    companyId: input.companyId,
    name: input.name,
    industry: input.industry,
    region: input.region,
    website: input.website,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: COMPANY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", companyUri: receipt.uri, did, companyId: input.companyId };
}

export async function getCompany(e: Etzhayyim, input: GetCompanyInput): Promise<GetCompanyOutput> {
  if (!input.companyId) return { error: "invalidCompanyId" };
  const resp = await e.read<CompanyRecord>({ collection: COMPANY_COLLECTION, rkey: companyRkey(input.companyId) }).catch(() => ({ records: [] }));
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
      if (input.region && v.region !== input.region) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, companyUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Job posting ────────────────────────────────────────────────────

export async function addJobPosting(e: Etzhayyim, input: AddJobPostingInput): Promise<AddJobPostingOutput> {
  if (!input.postingId || !input.companyId || !input.title || !input.postedAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!SECURITY_CATEGORIES.has(input.category)) return { status: "rejected", error: "invalidCategory" };
  if (!SENIORITIES.has(input.seniority)) return { status: "rejected", error: "invalidSeniority" };
  if (!ENGAGEMENT_TYPES.has(input.engagementType)) return { status: "rejected", error: "invalidEngagementType" };
  if (input.compMinJpy != null && !isUintString(input.compMinJpy)) return { status: "rejected", error: "compMinJpyMustBeUintString" };
  if (input.compMaxJpy != null && !isUintString(input.compMaxJpy)) return { status: "rejected", error: "compMaxJpyMustBeUintString" };
  if (!(await exists(e, COMPANY_COLLECTION, companyRkey(input.companyId)))) {
    return { status: "companyNotFound", error: `companyNotFound:${input.companyId}` };
  }
  const rkey = postingRkey(input.postingId);
  const existing = await e.read<JobPostingRecord>({ collection: JOB_POSTING_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", postingUri: existing.records[0].uri, did: existing.records[0].value.did, postingId: input.postingId };
  }
  const did = postingDidFor(input.postingId);
  const record: JobPostingRecord = {
    did,
    postingId: input.postingId,
    companyId: input.companyId,
    title: input.title,
    category: input.category,
    requiredSkills: input.requiredSkills,
    seniority: input.seniority,
    engagementType: input.engagementType,
    compMinJpy: input.compMinJpy,
    compMaxJpy: input.compMaxJpy,
    location: input.location,
    remote: input.remote,
    postedAt: input.postedAt,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: JOB_POSTING_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", postingUri: receipt.uri, did, postingId: input.postingId };
}

export async function listJobPostings(e: Etzhayyim, input: ListJobPostingsInput = {}): Promise<ListJobPostingsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<JobPostingRecord>({ collection: JOB_POSTING_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: JobPostingView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.companyId && v.companyId !== input.companyId) return false;
      if (input.category && v.category !== input.category) return false;
      if (input.seniority && v.seniority !== input.seniority) return false;
      if (input.engagementType && v.engagementType !== input.engagementType) return false;
      if (input.remote != null && v.remote !== input.remote) return false;
      if (q) {
        const hay = [v.title, ...(v.requiredSkills ?? [])].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .map((r) => ({ ...r.value, postingUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const postingsByCategory: Record<string, number> = {};
  const postingsBySeniority: Record<string, number> = {};
  const companyCount = await scanAll<CompanyRecord>(e, COMPANY_COLLECTION, maxScan, () => {});
  const jobPostingCount = await scanAll<JobPostingRecord>(e, JOB_POSTING_COLLECTION, maxScan, (v) => {
    postingsByCategory[v.category] = (postingsByCategory[v.category] ?? 0) + 1;
    postingsBySeniority[v.seniority] = (postingsBySeniority[v.seniority] ?? 0) + 1;
  });
  return {
    companyCount,
    jobPostingCount,
    postingsByCategory,
    postingsBySeniority,
    truncated: companyCount >= maxScan || jobPostingCount >= maxScan,
  };
}
