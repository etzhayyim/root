/**
 * webya kotoba — registry. kotoba-E2E split.
 *
 * Plaintext path (siteCatalog / template / page / generationJob / domain):
 *   sdk.write / sdk.read — the published web presence + public DNS proof tokens
 *   + ops timeline are public by definition. FK (page → site) enforced via
 *   exists().
 * E2E path (clientContact / legalDisclosure): sdk.encryptedWrite /
 *   sdk.encryptedRead — contact PII + 士業 per-person regulated credentials
 *   sealed in the kotoba envelope (ADR-2605181100); read-cap = owner DID +
 *   explicit recipients. The substrate never sees the PII in plaintext.
 *
 * STAYS etzhayyim (consent-capability): LLM/LangGraph site-generation INFERENCE +
 * CF-for-SaaS custom-hostname provisioning CALL + CF_API_TOKEN credential
 * custody. Only the resulting DATA records migrate here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CLIENT_CONTACT_INNER_TYPE,
  DOMAIN_COLLECTION,
  GENERATION_JOB_COLLECTION,
  LEGAL_DISCLOSURE_INNER_TYPE,
  PAGE_COLLECTION,
  SITE_CATALOG_COLLECTION,
  TEMPLATE_COLLECTION,
  clientContactRkey,
  disclosureRkey,
  domainRkey,
  isDisclosureType,
  isProfessionKind,
  isUint,
  jobRkey,
  pageRkey,
  siteRkey,
  templateRkey,
  webyaDidFor,
  type ClientContactBody,
  type ClientContactView,
  type CoverageInput,
  type CoverageOutput,
  type DomainRecord,
  type DomainView,
  type GenerationJobRecord,
  type GenerationJobView,
  type GetClientContactInput,
  type GetClientContactOutput,
  type GetDisclosureInput,
  type GetDisclosureOutput,
  type GetSiteInput,
  type GetSiteOutput,
  type LegalDisclosureBody,
  type LegalDisclosureView,
  type ListClientContactsInput,
  type ListClientContactsOutput,
  type ListDisclosuresInput,
  type ListDisclosuresOutput,
  type ListDomainsInput,
  type ListDomainsOutput,
  type ListJobsInput,
  type ListJobsOutput,
  type ListPagesInput,
  type ListPagesOutput,
  type ListSitesInput,
  type ListSitesOutput,
  type ListTemplatesInput,
  type ListTemplatesOutput,
  type PageRecord,
  type PageView,
  type RecordClientContactInput,
  type RecordClientContactOutput,
  type RecordDisclosureInput,
  type RecordDisclosureOutput,
  type RegisterDomainInput,
  type RegisterDomainOutput,
  type RegisterJobInput,
  type RegisterJobOutput,
  type RegisterPageInput,
  type RegisterPageOutput,
  type RegisterSiteInput,
  type RegisterSiteOutput,
  type RegisterTemplateInput,
  type RegisterTemplateOutput,
  type SiteCatalogRecord,
  type SiteCatalogView,
  type TemplateRecord,
  type TemplateView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── FK helper ──────────────────────────────────────────────────────

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]);
}

// ─── Site catalog (PLAINTEXT) ───────────────────────────────────────

export async function registerSite(e: Etzhayyim, input: RegisterSiteInput): Promise<RegisterSiteOutput> {
  if (!input.siteId || !input.siteName || !input.subdomain) return { status: "rejected", error: "missingRequiredFields" };
  if (!isProfessionKind(input.professionKind)) return { status: "rejected", error: "invalidProfessionKind" };
  const rkey = siteRkey(input.siteId);
  const existing = await e.read<SiteCatalogRecord>({ collection: SITE_CATALOG_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", siteUri: existing.records[0].uri, did: existing.records[0].value.did, siteId: input.siteId };
  }
  const now = new Date().toISOString();
  const did = webyaDidFor("site", input.siteId);
  const record: SiteCatalogRecord = {
    did,
    siteId: input.siteId,
    siteName: input.siteName,
    professionKind: input.professionKind,
    status: input.status ?? "draft",
    subdomain: input.subdomain,
    customDomain: input.customDomain,
    sslStatus: input.sslStatus ?? "none",
    publishedAt: input.publishedAt,
    createdAt: now,
  };
  const receipt = await e.write({ collection: SITE_CATALOG_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", siteUri: receipt.uri, did, siteId: input.siteId };
}

export async function getSite(e: Etzhayyim, input: GetSiteInput): Promise<GetSiteOutput> {
  if (!input.siteId) return { error: "invalidSiteId" };
  const resp = await e.read<SiteCatalogRecord>({ collection: SITE_CATALOG_COLLECTION, rkey: siteRkey(input.siteId) }).catch(() => ({ records: [] }));
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { site: { ...hit.value, siteUri: hit.uri } };
}

export async function listSites(e: Etzhayyim, input: ListSitesInput = {}): Promise<ListSitesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SiteCatalogRecord>({ collection: SITE_CATALOG_COLLECTION, cursor: input.cursor, limit });
  const items: SiteCatalogView[] = resp.records
    .filter((r) => !input.professionKind || r.value.professionKind === input.professionKind)
    .filter((r) => !input.status || r.value.status === input.status)
    .map((r) => ({ ...r.value, siteUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Template (PLAINTEXT) ───────────────────────────────────────────

export async function registerTemplate(e: Etzhayyim, input: RegisterTemplateInput): Promise<RegisterTemplateOutput> {
  if (!input.templateId || !input.htmlSkeleton) return { status: "rejected", error: "missingRequiredFields" };
  if (!isProfessionKind(input.professionKind)) return { status: "rejected", error: "invalidProfessionKind" };
  if (input.version !== undefined && !isUint(input.version)) return { status: "rejected", error: "invalidVersion" };
  const rkey = templateRkey(input.templateId);
  const existing = await e.read<TemplateRecord>({ collection: TEMPLATE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", templateUri: existing.records[0].uri, did: existing.records[0].value.did, templateId: input.templateId };
  }
  const now = new Date().toISOString();
  const did = webyaDidFor("tpl", input.templateId);
  const record: TemplateRecord = {
    did,
    templateId: input.templateId,
    professionKind: input.professionKind,
    pages: input.pages ?? [],
    htmlSkeleton: input.htmlSkeleton,
    version: input.version ?? 1,
    active: input.active ?? true,
    createdAt: now,
  };
  const receipt = await e.write({ collection: TEMPLATE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", templateUri: receipt.uri, did, templateId: input.templateId };
}

export async function listTemplates(e: Etzhayyim, input: ListTemplatesInput = {}): Promise<ListTemplatesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TemplateRecord>({ collection: TEMPLATE_COLLECTION, cursor: input.cursor, limit });
  const items: TemplateView[] = resp.records
    .filter((r) => !input.professionKind || r.value.professionKind === input.professionKind)
    .map((r) => ({ ...r.value, templateUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Page (PLAINTEXT, FK → siteCatalog) ─────────────────────────────

export async function registerPage(e: Etzhayyim, input: RegisterPageInput): Promise<RegisterPageOutput> {
  if (!input.pageId || !input.siteId || !input.slug || !input.title) return { status: "rejected", error: "missingRequiredFields" };
  if (!(await exists(e, SITE_CATALOG_COLLECTION, siteRkey(input.siteId)))) return { status: "rejected", error: "siteNotFound" };
  const rkey = pageRkey(input.pageId);
  const existing = await e.read<PageRecord>({ collection: PAGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", pageUri: existing.records[0].uri, did: existing.records[0].value.did, pageId: input.pageId };
  }
  const now = new Date().toISOString();
  const did = webyaDidFor("page", input.pageId);
  const record: PageRecord = {
    did,
    pageId: input.pageId,
    siteId: input.siteId,
    slug: input.slug,
    title: input.title,
    metaDescription: input.metaDescription,
    htmlContent: input.htmlContent,
    jsonLd: input.jsonLd,
    status: input.status ?? "draft",
    updatedAt: now,
  };
  const receipt = await e.write({ collection: PAGE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", pageUri: receipt.uri, did, pageId: input.pageId };
}

export async function listPages(e: Etzhayyim, input: ListPagesInput = {}): Promise<ListPagesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PageRecord>({ collection: PAGE_COLLECTION, cursor: input.cursor, limit });
  const items: PageView[] = resp.records
    .filter((r) => !input.siteId || r.value.siteId === input.siteId)
    .map((r) => ({ ...r.value, pageUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Generation job (PLAINTEXT, public ops timeline, FK → site) ─────

export async function registerJob(e: Etzhayyim, input: RegisterJobInput): Promise<RegisterJobOutput> {
  if (!input.jobId || !input.siteId) return { status: "rejected", error: "missingRequiredFields" };
  if (input.llmCallsCount !== undefined && !isUint(input.llmCallsCount)) return { status: "rejected", error: "invalidLlmCallsCount" };
  if (input.revisionCount !== undefined && !isUint(input.revisionCount)) return { status: "rejected", error: "invalidRevisionCount" };
  if (!(await exists(e, SITE_CATALOG_COLLECTION, siteRkey(input.siteId)))) return { status: "rejected", error: "siteNotFound" };
  const rkey = jobRkey(input.jobId);
  const existing = await e.read<GenerationJobRecord>({ collection: GENERATION_JOB_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", jobUri: existing.records[0].uri, did: existing.records[0].value.did, jobId: input.jobId };
  }
  const now = new Date().toISOString();
  const did = webyaDidFor("job", input.jobId);
  const record: GenerationJobRecord = {
    did,
    jobId: input.jobId,
    siteId: input.siteId,
    status: input.status ?? "pending",
    llmCallsCount: input.llmCallsCount ?? 0,
    revisionCount: input.revisionCount ?? 0,
    startedAt: input.startedAt ?? now,
    completedAt: input.completedAt,
  };
  const receipt = await e.write({ collection: GENERATION_JOB_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", jobUri: receipt.uri, did, jobId: input.jobId };
}

export async function listJobs(e: Etzhayyim, input: ListJobsInput = {}): Promise<ListJobsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<GenerationJobRecord>({ collection: GENERATION_JOB_COLLECTION, cursor: input.cursor, limit });
  const items: GenerationJobView[] = resp.records
    .filter((r) => !input.siteId || r.value.siteId === input.siteId)
    .filter((r) => !input.status || r.value.status === input.status)
    .map((r) => ({ ...r.value, jobUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Domain (PLAINTEXT, public DNS mapping, FK → site) ──────────────

export async function registerDomain(e: Etzhayyim, input: RegisterDomainInput): Promise<RegisterDomainOutput> {
  if (!input.domainId || !input.siteId || !input.domain) return { status: "rejected", error: "missingRequiredFields" };
  if (!(await exists(e, SITE_CATALOG_COLLECTION, siteRkey(input.siteId)))) return { status: "rejected", error: "siteNotFound" };
  const rkey = domainRkey(input.domainId);
  const existing = await e.read<DomainRecord>({ collection: DOMAIN_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", domainUri: existing.records[0].uri, did: existing.records[0].value.did, domainId: input.domainId };
  }
  const now = new Date().toISOString();
  const did = webyaDidFor("dom", input.domainId);
  const record: DomainRecord = {
    did,
    domainId: input.domainId,
    siteId: input.siteId,
    domain: input.domain,
    sslStatus: input.sslStatus ?? "pending",
    ownershipVerified: input.ownershipVerified ?? false,
    cnameTarget: input.cnameTarget ?? "proxy-webya.etzhayyim.com",
    verificationTxtName: input.verificationTxtName,
    verificationTxtValue: input.verificationTxtValue,
    provisionedAt: input.provisionedAt,
    createdAt: now,
  };
  const receipt = await e.write({ collection: DOMAIN_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", domainUri: receipt.uri, did, domainId: input.domainId };
}

export async function listDomains(e: Etzhayyim, input: ListDomainsInput = {}): Promise<ListDomainsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<DomainRecord>({ collection: DOMAIN_COLLECTION, cursor: input.cursor, limit });
  const items: DomainView[] = resp.records
    .filter((r) => !input.siteId || r.value.siteId === input.siteId)
    .filter((r) => !input.sslStatus || r.value.sslStatus === input.sslStatus)
    .map((r) => ({ ...r.value, domainUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Client contact (E2E-ENCRYPTED, contact PII) ────────────────────

export async function recordClientContact(e: Etzhayyim, input: RecordClientContactInput): Promise<RecordClientContactOutput> {
  if (!input.clientId || !input.siteId || !input.representativeName || !input.address) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const body: ClientContactBody = {
    clientId: input.clientId,
    siteId: input.siteId,
    representativeName: input.representativeName,
    address: input.address,
    email: input.email,
    phone: input.phone,
    orgDid: input.orgDid,
    recordedAt: input.recordedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: CLIENT_CONTACT_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: clientContactRkey(input.clientId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, clientId: input.clientId };
}

async function scanClientContacts(e: Etzhayyim, maxScan: number): Promise<ClientContactView[]> {
  const out: ClientContactView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<ClientContactBody>({ innerType: CLIENT_CONTACT_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listClientContacts(e: Etzhayyim, input: ListClientContactsInput = {}): Promise<ListClientContactsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanClientContacts(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((c) => !input.siteId || c.siteId === input.siteId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getClientContact(e: Etzhayyim, input: GetClientContactInput): Promise<GetClientContactOutput> {
  if (!input.clientId) return { error: "invalidClientId" };
  const all = await scanClientContacts(e, DEFAULT_MAX_SCAN);
  const found = all.find((c) => c.clientId === input.clientId);
  if (!found) return { error: "notFound" };
  return { contact: found };
}

// ─── Legal disclosure (E2E-ENCRYPTED, per-person regulated credentials) ─

export async function recordDisclosure(e: Etzhayyim, input: RecordDisclosureInput): Promise<RecordDisclosureOutput> {
  if (!input.disclosureId || !input.siteId || !input.disclosureValue || !input.representativeName) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isProfessionKind(input.professionKind)) return { status: "rejected", error: "invalidProfessionKind" };
  if (!isDisclosureType(input.disclosureType)) return { status: "rejected", error: "invalidDisclosureType" };
  const body: LegalDisclosureBody = {
    disclosureId: input.disclosureId,
    siteId: input.siteId,
    professionKind: input.professionKind,
    disclosureType: input.disclosureType,
    disclosureValue: input.disclosureValue,
    representativeName: input.representativeName,
    verifiedAt: input.verifiedAt,
    recordedAt: input.recordedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: LEGAL_DISCLOSURE_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: disclosureRkey(input.disclosureId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, disclosureId: input.disclosureId };
}

async function scanDisclosures(e: Etzhayyim, maxScan: number): Promise<LegalDisclosureView[]> {
  const out: LegalDisclosureView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<LegalDisclosureBody>({ innerType: LEGAL_DISCLOSURE_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listDisclosures(e: Etzhayyim, input: ListDisclosuresInput = {}): Promise<ListDisclosuresOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanDisclosures(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((d) => !input.siteId || d.siteId === input.siteId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getDisclosure(e: Etzhayyim, input: GetDisclosureInput): Promise<GetDisclosureOutput> {
  if (!input.disclosureId) return { error: "invalidDisclosureId" };
  const all = await scanDisclosures(e, DEFAULT_MAX_SCAN);
  const found = all.find((d) => d.disclosureId === input.disclosureId);
  if (!found) return { error: "notFound" };
  return { disclosure: found };
}

// ─── Coverage rollup (countAll over both stores) ────────────────────

async function countAll(e: Etzhayyim, collection: string, maxScan: number): Promise<{ count: number; byStatus?: Record<string, number> }> {
  let count = 0;
  let cursor: string | undefined;
  while (count < maxScan) {
    const page = await e.read<SiteCatalogRecord>({ collection, cursor, limit: PAGE_LIMIT });
    count += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return { count };
}

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const sitesByStatus: Record<string, number> = {};
  let siteCatalogCount = 0;
  let cursor: string | undefined;
  while (siteCatalogCount < maxScan) {
    const page = await e.read<SiteCatalogRecord>({ collection: SITE_CATALOG_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      sitesByStatus[r.value.status] = (sitesByStatus[r.value.status] ?? 0) + 1;
      siteCatalogCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const templateCount = (await countAll(e, TEMPLATE_COLLECTION, maxScan)).count;
  const pageCount = (await countAll(e, PAGE_COLLECTION, maxScan)).count;
  const generationJobCount = (await countAll(e, GENERATION_JOB_COLLECTION, maxScan)).count;
  const domainCount = (await countAll(e, DOMAIN_COLLECTION, maxScan)).count;
  const clientContactCount = (await scanClientContacts(e, maxScan)).length;
  const legalDisclosureCount = (await scanDisclosures(e, maxScan)).length;
  return {
    siteCatalogCount,
    templateCount,
    pageCount,
    generationJobCount,
    domainCount,
    clientContactCount,
    legalDisclosureCount,
    sitesByStatus,
    truncated:
      siteCatalogCount >= maxScan ||
      clientContactCount >= maxScan ||
      legalDisclosureCount >= maxScan,
  };
}
