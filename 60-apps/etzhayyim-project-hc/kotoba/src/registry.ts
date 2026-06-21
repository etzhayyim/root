/**
 * hc kotoba — registry. Intel E2E reference shape.
 *
 * Plaintext path (contractTemplate): sdk.write / sdk.read — public legal catalog.
 * E2E path (spApplication): sdk.encryptedWrite / sdk.encryptedRead — SP KYC/KYB
 * PII+CUI body sealed in the kotoba envelope (ADR-2605181100), read-cap = owner
 * DID. The substrate never sees legalName / contactEmail / findings in plaintext.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CONTRACT_TEMPLATE_COLLECTION,
  SP_APPLICATION_INNER_TYPE,
  contractDidFor,
  contractRkey,
  isEmail,
  isVerdict,
  spRkey,
  type ContractTemplateRecord,
  type ContractTemplateView,
  type CoverageInput,
  type CoverageOutput,
  type GetContractInput,
  type GetContractOutput,
  type GetSpApplicationInput,
  type GetSpApplicationOutput,
  type ListContractsInput,
  type ListContractsOutput,
  type ListSpApplicationsInput,
  type ListSpApplicationsOutput,
  type RegisterContractInput,
  type RegisterContractOutput,
  type RegisterSpApplicationInput,
  type RegisterSpApplicationOutput,
  type SpApplicationBody,
  type SpApplicationView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Contract template (PLAINTEXT) ──────────────────────────────────

export async function registerContract(e: Etzhayyim, input: RegisterContractInput): Promise<RegisterContractOutput> {
  if (!input.contractType || !input.locale) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = contractRkey(input.contractType, input.locale);
  const existing = await e
    .read<ContractTemplateRecord>({ collection: CONTRACT_TEMPLATE_COLLECTION, rkey })
    .catch(() => ({ records: [] as Array<{ uri: string; value: ContractTemplateRecord }> }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      templateUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      contractType: input.contractType,
      locale: input.locale,
    };
  }
  const now = new Date().toISOString();
  const did = contractDidFor(input.contractType, input.locale);
  const record: ContractTemplateRecord = {
    did,
    contractType: input.contractType,
    locale: input.locale,
    governingLaw: input.governingLaw ?? "Japan",
    jurisdiction: input.jurisdiction ?? "Tokyo District Court",
    effectiveDate: input.effectiveDate ?? now,
    rev: input.rev ?? "1",
    createdAt: now,
  };
  const receipt = await e.write({ collection: CONTRACT_TEMPLATE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", templateUri: receipt.uri, did, contractType: input.contractType, locale: input.locale };
}

export async function getContract(e: Etzhayyim, input: GetContractInput): Promise<GetContractOutput> {
  if (!input.contractType || !input.locale) return { error: "missingRequiredFields" };
  const rkey = contractRkey(input.contractType, input.locale);
  const resp = await e.read<ContractTemplateRecord>({ collection: CONTRACT_TEMPLATE_COLLECTION, rkey });
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { template: { ...hit.value, templateUri: hit.uri } };
}

export async function listContracts(e: Etzhayyim, input: ListContractsInput = {}): Promise<ListContractsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ContractTemplateRecord>({ collection: CONTRACT_TEMPLATE_COLLECTION, cursor: input.cursor, limit });
  const items: ContractTemplateView[] = resp.records
    .filter((r) => (!input.contractType || r.value.contractType === input.contractType) && (!input.locale || r.value.locale === input.locale))
    .map((r) => ({ ...r.value, templateUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── SP application (E2E-ENCRYPTED, PII + CUI) ──────────────────────

export async function registerSpApplication(e: Etzhayyim, input: RegisterSpApplicationInput): Promise<RegisterSpApplicationOutput> {
  if (!input.applicationId || !input.legalName || !input.countryIso3 || !input.category) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isEmail(input.contactEmail)) return { status: "rejected", error: "invalidContactEmail" };
  const verdict = input.verdict ?? "pending";
  if (!isVerdict(verdict)) return { status: "rejected", error: "invalidVerdict" };
  const body: SpApplicationBody = {
    applicationId: input.applicationId,
    legalName: input.legalName,
    tradeName: input.tradeName,
    contactEmail: input.contactEmail,
    countryIso3: input.countryIso3,
    lei: input.lei,
    category: input.category,
    factoryType: input.factoryType,
    documents: input.documents,
    isicCodes: input.isicCodes ?? [],
    verdict,
    sanctionsClear: input.sanctionsClear,
    legalEntityVerified: input.legalEntityVerified,
    findings: input.findings,
    submittedAt: input.submittedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: SP_APPLICATION_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: spRkey(input.applicationId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, applicationId: input.applicationId };
}

async function scanApplications(e: Etzhayyim, maxScan: number): Promise<SpApplicationView[]> {
  const out: SpApplicationView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<SpApplicationBody>({ innerType: SP_APPLICATION_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listSpApplications(e: Etzhayyim, input: ListSpApplicationsInput = {}): Promise<ListSpApplicationsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanApplications(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter(
    (a) => (!input.countryIso3 || a.countryIso3 === input.countryIso3) && (!input.verdict || a.verdict === input.verdict),
  );
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getSpApplication(e: Etzhayyim, input: GetSpApplicationInput): Promise<GetSpApplicationOutput> {
  if (!input.applicationId) return { error: "invalidApplicationId" };
  const all = await scanApplications(e, DEFAULT_MAX_SCAN);
  const found = all.find((a) => a.applicationId === input.applicationId);
  if (!found) return { error: "notFound" };
  return { application: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const templatesByLocale: Record<string, number> = {};
  let contractTemplateCount = 0;
  let cursor: string | undefined;
  while (contractTemplateCount < maxScan) {
    const page = await e.read<ContractTemplateRecord>({ collection: CONTRACT_TEMPLATE_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      templatesByLocale[r.value.locale] = (templatesByLocale[r.value.locale] ?? 0) + 1;
      contractTemplateCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const apps = await scanApplications(e, maxScan);
  const applicationsByVerdict: Record<string, number> = {};
  for (const a of apps) {
    applicationsByVerdict[a.verdict] = (applicationsByVerdict[a.verdict] ?? 0) + 1;
  }
  return {
    contractTemplateCount,
    spApplicationCount: apps.length,
    templatesByLocale,
    applicationsByVerdict,
    truncated: contractTemplateCount >= maxScan || apps.length >= maxScan,
  };
}
