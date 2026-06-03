/**
 * crypto-asset-freeze rw-free — kotoba-E2E registry.
 *
 * Plaintext path (incidentProjection): sdk.write / sdk.read — public aggregate
 * counts by chain × status (no wallet/case PII).
 * E2E path (freezeIncident, freezeRequest): sdk.encryptedWrite /
 * sdk.encryptedRead — CUI / LE bodies sealed in the kotoba envelope
 * (ADR-2605181100), read-cap = owner DID (+ explicit LE-agency recipients).
 * The substrate never sees wallet addresses or case ids in plaintext.
 *
 * Freeze/unfreeze EXECUTION + recursive wallet-trace INFERENCE stay etzhayyim
 * (consent-capability) — only the resulting data records live here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  INCIDENT_INNER_TYPE,
  PROJECTION_COLLECTION,
  REQUEST_INNER_TYPE,
  incidentRkey,
  isPct,
  isUint,
  isWalletAddress,
  projectionDidFor,
  projectionRkey,
  requestRkey,
  type CoverageInput,
  type CoverageOutput,
  type CreateIncidentInput,
  type CreateIncidentOutput,
  type FreezeIncidentBody,
  type FreezeIncidentView,
  type FreezeRequestBody,
  type FreezeRequestView,
  type GetIncidentInput,
  type GetIncidentOutput,
  type IncidentProjectionRecord,
  type IncidentProjectionView,
  type ListIncidentsInput,
  type ListIncidentsOutput,
  type ListProjectionsInput,
  type ListProjectionsOutput,
  type ListRequestsInput,
  type ListRequestsOutput,
  type RecordProjectionInput,
  type RecordProjectionOutput,
  type RequestFreezeInput,
  type RequestFreezeOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Incident projection (PLAINTEXT) ────────────────────────────────

export async function recordProjection(e: Etzhayyim, input: RecordProjectionInput): Promise<RecordProjectionOutput> {
  if (!input.projectionId || !input.chain || !input.status) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.incidentCount)) return { status: "rejected", error: "invalidIncidentCount" };
  const rkey = projectionRkey(input.projectionId);
  const existing = await e.read<IncidentProjectionRecord>({ collection: PROJECTION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", projectionUri: existing.records[0].uri, did: existing.records[0].value.did, projectionId: input.projectionId };
  }
  const now = new Date().toISOString();
  const did = projectionDidFor(input.projectionId);
  const record: IncidentProjectionRecord = {
    did,
    projectionId: input.projectionId,
    chain: input.chain,
    status: input.status,
    incidentCount: input.incidentCount,
    generatedAt: input.generatedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: PROJECTION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", projectionUri: receipt.uri, did, projectionId: input.projectionId };
}

export async function listProjections(e: Etzhayyim, input: ListProjectionsInput = {}): Promise<ListProjectionsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<IncidentProjectionRecord>({ collection: PROJECTION_COLLECTION, cursor: input.cursor, limit });
  const items: IncidentProjectionView[] = resp.records
    .filter((r) => (!input.chain || r.value.chain === input.chain) && (!input.status || r.value.status === input.status))
    .map((r) => ({ ...r.value, projectionUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Freeze incident (E2E-ENCRYPTED, CUI / LE) ──────────────────────

export async function createIncident(e: Etzhayyim, input: CreateIncidentInput): Promise<CreateIncidentOutput> {
  if (!input.incidentId || !input.sourceCaseId || !input.sourceApp || !input.chain) return { status: "rejected", error: "missingRequiredFields" };
  if (!isPct(input.priority)) return { status: "rejected", error: "invalidPriority" };
  if (!Array.isArray(input.walletAddresses) || input.walletAddresses.length === 0) return { status: "rejected", error: "missingWalletAddresses" };
  if (!input.walletAddresses.every(isWalletAddress)) return { status: "rejected", error: "invalidWalletAddress" };
  const body: FreezeIncidentBody = {
    incidentId: input.incidentId,
    sourceCaseId: input.sourceCaseId,
    sourceApp: input.sourceApp,
    chain: input.chain,
    priority: input.priority,
    walletAddresses: input.walletAddresses,
    courtOrderCid: input.courtOrderCid,
    status: input.status ?? "open",
    openedAt: input.openedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: INCIDENT_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: incidentRkey(input.incidentId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, incidentId: input.incidentId, walletCount: input.walletAddresses.length };
}

async function scanIncidents(e: Etzhayyim, maxScan: number): Promise<FreezeIncidentView[]> {
  const out: FreezeIncidentView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<FreezeIncidentBody>({ innerType: INCIDENT_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listIncidents(e: Etzhayyim, input: ListIncidentsInput = {}): Promise<ListIncidentsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanIncidents(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((c) => (!input.chain || c.chain === input.chain) && (!input.status || c.status === input.status));
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getIncident(e: Etzhayyim, input: GetIncidentInput): Promise<GetIncidentOutput> {
  if (!input.incidentId) return { error: "invalidIncidentId" };
  const all = await scanIncidents(e, DEFAULT_MAX_SCAN);
  const found = all.find((c) => c.incidentId === input.incidentId);
  if (!found) return { error: "notFound" };
  return { incident: found };
}

// ─── Freeze request (E2E-ENCRYPTED, CUI / LE) ───────────────────────

export async function requestFreeze(e: Etzhayyim, input: RequestFreezeInput): Promise<RequestFreezeOutput> {
  if (!input.requestId || !input.incidentId || !input.exchange) return { status: "rejected", error: "missingRequiredFields" };
  if (!isWalletAddress(input.walletAddress)) return { status: "rejected", error: "invalidWalletAddress" };
  const body: FreezeRequestBody = {
    requestId: input.requestId,
    incidentId: input.incidentId,
    exchange: input.exchange,
    walletAddress: input.walletAddress,
    chain: input.chain ?? "",
    status: input.status ?? "requested",
    requestedAt: input.requestedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: REQUEST_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: requestRkey(input.requestId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, requestId: input.requestId };
}

async function scanRequests(e: Etzhayyim, maxScan: number): Promise<FreezeRequestView[]> {
  const out: FreezeRequestView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<FreezeRequestBody>({ innerType: REQUEST_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listRequests(e: Etzhayyim, input: ListRequestsInput = {}): Promise<ListRequestsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanRequests(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((r) => (!input.incidentId || r.incidentId === input.incidentId) && (!input.exchange || r.exchange === input.exchange));
  return { items: filtered.slice(0, limit), total: filtered.length };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const projectionsByChain: Record<string, number> = {};
  let incidentProjectionCount = 0;
  let cursor: string | undefined;
  while (incidentProjectionCount < maxScan) {
    const page = await e.read<IncidentProjectionRecord>({ collection: PROJECTION_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      projectionsByChain[r.value.chain] = (projectionsByChain[r.value.chain] ?? 0) + 1;
      incidentProjectionCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const freezeIncidentCount = (await scanIncidents(e, maxScan)).length;
  const freezeRequestCount = (await scanRequests(e, maxScan)).length;
  return {
    incidentProjectionCount,
    freezeIncidentCount,
    freezeRequestCount,
    projectionsByChain,
    truncated: incidentProjectionCount >= maxScan || freezeIncidentCount >= maxScan || freezeRequestCount >= maxScan,
  };
}
