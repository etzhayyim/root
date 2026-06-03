/**
 * tia rw-free — registry. kotoba-E2E split.
 *
 * Plaintext path (protectedPlatform): sdk.write / sdk.read — public catalog.
 * E2E paths (protectedAccount / detectionResult): sdk.encryptedWrite /
 * sdk.encryptedRead — PII + per-person threat findings sealed in the kotoba
 * envelope (ADR-2605181100), read-cap = owner DID. The substrate never sees the
 * account PII or detection findings in plaintext.
 *
 * Gemini similarity INFERENCE + platform takedown ACTIONS stay etzhayyim (consumed
 * via consent-capability); only their resulting DATA records live here as E2E.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ACCOUNT_INNER_TYPE,
  DETECTION_INNER_TYPE,
  PLATFORM_COLLECTION,
  accountRkey,
  detectionRkey,
  isHttpUrl,
  isPct,
  platformDidFor,
  platformRkey,
  type CoverageInput,
  type CoverageOutput,
  type DetectionResultBody,
  type DetectionResultView,
  type GetAccountInput,
  type GetAccountOutput,
  type GetPlatformInput,
  type GetPlatformOutput,
  type ListAccountsInput,
  type ListAccountsOutput,
  type ListDetectionsInput,
  type ListDetectionsOutput,
  type ListPlatformsInput,
  type ListPlatformsOutput,
  type ProtectedAccountBody,
  type ProtectedAccountView,
  type ProtectedPlatformRecord,
  type ProtectedPlatformView,
  type RecordDetectionInput,
  type RecordDetectionOutput,
  type RegisterAccountInput,
  type RegisterAccountOutput,
  type RegisterPlatformInput,
  type RegisterPlatformOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Protected platform (PLAINTEXT catalog) ─────────────────────────

export async function registerPlatform(e: Etzhayyim, input: RegisterPlatformInput): Promise<RegisterPlatformOutput> {
  if (!input.platformType || !input.displayName) return { status: "rejected", error: "missingRequiredFields" };
  if (!isHttpUrl(input.seekUrl)) return { status: "rejected", error: "invalidSeekUrl" };
  const rkey = platformRkey(input.platformType);
  const existing = await e.read<ProtectedPlatformRecord>({ collection: PLATFORM_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", platformUri: existing.records[0].uri, did: existing.records[0].value.did, platformType: input.platformType };
  }
  const now = new Date().toISOString();
  const did = platformDidFor(input.platformType);
  const record: ProtectedPlatformRecord = {
    did,
    platformType: input.platformType,
    displayName: input.displayName,
    seekUrl: input.seekUrl,
    createdAt: now,
  };
  const receipt = await e.write({ collection: PLATFORM_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", platformUri: receipt.uri, did, platformType: input.platformType };
}

export async function listPlatforms(e: Etzhayyim, input: ListPlatformsInput = {}): Promise<ListPlatformsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ProtectedPlatformRecord>({ collection: PLATFORM_COLLECTION, cursor: input.cursor, limit });
  const items: ProtectedPlatformView[] = resp.records
    .filter((r) => !input.platformType || r.value.platformType === input.platformType)
    .map((r) => ({ ...r.value, platformUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

export async function getPlatform(e: Etzhayyim, input: GetPlatformInput): Promise<GetPlatformOutput> {
  if (!input.platformType) return { error: "invalidPlatformType" };
  const resp = await e.read<ProtectedPlatformRecord>({ collection: PLATFORM_COLLECTION, rkey: platformRkey(input.platformType) }).catch(() => ({ records: [] }));
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { platform: { ...hit.value, platformUri: hit.uri } };
}

// ─── Protected account (E2E-ENCRYPTED, PII) ─────────────────────────

export async function registerAccount(e: Etzhayyim, input: RegisterAccountInput): Promise<RegisterAccountOutput> {
  if (!input.accountId || !input.ownerDid || !input.platformType || !input.accountName || !input.userId) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (input.accountUrl !== undefined && !isHttpUrl(input.accountUrl)) return { status: "rejected", error: "invalidAccountUrl" };
  const body: ProtectedAccountBody = {
    accountId: input.accountId,
    ownerDid: input.ownerDid,
    platformType: input.platformType,
    accountName: input.accountName,
    userId: input.userId,
    accountUrl: input.accountUrl,
    registeredAt: input.registeredAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: ACCOUNT_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: accountRkey(input.accountId),
  });
  return { status: "registered", uri: receipt.uri, keyId: receipt.keyId, accountId: input.accountId };
}

async function scanAccounts(e: Etzhayyim, maxScan: number): Promise<ProtectedAccountView[]> {
  const out: ProtectedAccountView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<ProtectedAccountBody>({ innerType: ACCOUNT_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listAccounts(e: Etzhayyim, input: ListAccountsInput = {}): Promise<ListAccountsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanAccounts(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((a) => !input.platformType || a.platformType === input.platformType);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getAccount(e: Etzhayyim, input: GetAccountInput): Promise<GetAccountOutput> {
  if (!input.accountId) return { error: "invalidAccountId" };
  const all = await scanAccounts(e, DEFAULT_MAX_SCAN);
  const found = all.find((a) => a.accountId === input.accountId);
  if (!found) return { error: "notFound" };
  return { account: found };
}

// ─── Detection result (E2E-ENCRYPTED, threat intel) ─────────────────

export async function recordDetection(e: Etzhayyim, input: RecordDetectionInput): Promise<RecordDetectionOutput> {
  if (!input.detectionId || !input.internetAccountId || !input.platformType) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isPct(input.similarityScore)) return { status: "rejected", error: "invalidSimilarityScore" };
  if (input.suspectUrl !== undefined && !isHttpUrl(input.suspectUrl)) return { status: "rejected", error: "invalidSuspectUrl" };
  const body: DetectionResultBody = {
    detectionId: input.detectionId,
    internetAccountId: input.internetAccountId,
    platformType: input.platformType,
    similarityScore: input.similarityScore,
    suspectUrl: input.suspectUrl,
    detectedAt: input.detectedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: DETECTION_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: detectionRkey(input.detectionId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, detectionId: input.detectionId };
}

async function scanDetections(e: Etzhayyim, maxScan: number): Promise<DetectionResultView[]> {
  const out: DetectionResultView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<DetectionResultBody>({ innerType: DETECTION_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listDetections(e: Etzhayyim, input: ListDetectionsInput = {}): Promise<ListDetectionsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanDetections(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((d) => !input.internetAccountId || d.internetAccountId === input.internetAccountId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const accountsByPlatform: Record<string, number> = {};
  let protectedPlatformCount = 0;
  let cursor: string | undefined;
  while (protectedPlatformCount < maxScan) {
    const page = await e.read<ProtectedPlatformRecord>({ collection: PLATFORM_COLLECTION, cursor, limit: PAGE_LIMIT });
    protectedPlatformCount += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const accounts = await scanAccounts(e, maxScan);
  for (const a of accounts) {
    accountsByPlatform[a.platformType] = (accountsByPlatform[a.platformType] ?? 0) + 1;
  }
  const detectionResultCount = (await scanDetections(e, maxScan)).length;
  return {
    protectedPlatformCount,
    protectedAccountCount: accounts.length,
    detectionResultCount,
    accountsByPlatform,
    truncated:
      protectedPlatformCount >= maxScan || accounts.length >= maxScan || detectionResultCount >= maxScan,
  };
}
