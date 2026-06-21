/**
 * open-ossekai kotoba — kotoba-E2E registry.
 *
 * Plaintext path (arbitrageOpportunity): sdk.write / sdk.read — L2 public-good
 * information-asymmetry catalog (no subject PII).
 * E2E path (jochoAssessment): sdk.encryptedWrite / sdk.encryptedRead — L3
 * per-person Well-Becoming jocho scores sealed in the kotoba envelope
 * (ADR-2605181100), read-cap = owner/subject DID + consented recipients
 * (ADR-0018 Tier-3). The substrate never sees a person's jocho scores in
 * plaintext.
 *
 * L1 LLM intel-brief generation + jocho-scoring inference + framing-audit +
 * fiat sales-lead propagation stay etzhayyim (consumed via consent-capability) —
 * only the resulting jocho DATA migrates here, E2E-sealed.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ARBITRAGE_COLLECTION,
  JOCHO_INNER_TYPE,
  arbitrageDidFor,
  arbitrageRkey,
  jochoRkey,
  isPct,
  isScopeKind,
  isSeverity,
  isUint,
  type ArbitrageOpportunityRecord,
  type ArbitrageOpportunityView,
  type CoverageInput,
  type CoverageOutput,
  type GetArbitrageInput,
  type GetArbitrageOutput,
  type GetJochoInput,
  type GetJochoOutput,
  type JochoAssessmentBody,
  type JochoAssessmentView,
  type ListArbitrageInput,
  type ListArbitrageOutput,
  type ListJochoInput,
  type ListJochoOutput,
  type RecordJochoInput,
  type RecordJochoOutput,
  type RegisterArbitrageInput,
  type RegisterArbitrageOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Arbitrage opportunity (PLAINTEXT) ──────────────────────────────

export async function registerArbitrage(e: Etzhayyim, input: RegisterArbitrageInput): Promise<RegisterArbitrageOutput> {
  if (!input.arbId || !input.topicCategory) return { status: "rejected", error: "missingRequiredFields" };
  if (!isSeverity(input.severity)) return { status: "rejected", error: "invalidSeverity" };
  if (!isScopeKind(input.scopeKind)) return { status: "rejected", error: "invalidScopeKind" };
  if (!isUint(input.estimatedAffectedPopulation)) return { status: "rejected", error: "invalidEstimatedAffectedPopulation" };
  const rkey = arbitrageRkey(input.arbId);
  const existing = await e.read<ArbitrageOpportunityRecord>({ collection: ARBITRAGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", arbUri: existing.records[0].uri, did: existing.records[0].value.did, arbId: input.arbId };
  }
  const now = new Date().toISOString();
  const did = arbitrageDidFor(input.arbId);
  const record: ArbitrageOpportunityRecord = {
    did,
    arbId: input.arbId,
    topicCategory: input.topicCategory,
    scopeKind: input.scopeKind,
    severity: input.severity,
    estimatedAffectedPopulation: input.estimatedAffectedPopulation,
    status: input.status ?? "open",
    generatedAt: input.generatedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: ARBITRAGE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", arbUri: receipt.uri, did, arbId: input.arbId };
}

export async function getArbitrage(e: Etzhayyim, input: GetArbitrageInput): Promise<GetArbitrageOutput> {
  if (!input.arbId) return { error: "invalidArbId" };
  const resp = await e.read<ArbitrageOpportunityRecord>({ collection: ARBITRAGE_COLLECTION, rkey: arbitrageRkey(input.arbId) }).catch(() => ({ records: [] }));
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { opportunity: { ...hit.value, arbUri: hit.uri } };
}

export async function listArbitrage(e: Etzhayyim, input: ListArbitrageInput = {}): Promise<ListArbitrageOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ArbitrageOpportunityRecord>({ collection: ARBITRAGE_COLLECTION, cursor: input.cursor, limit });
  const items: ArbitrageOpportunityView[] = resp.records
    .filter((r) => !input.topicCategory || r.value.topicCategory === input.topicCategory)
    .filter((r) => !input.severity || r.value.severity === input.severity)
    .map((r) => ({ ...r.value, arbUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Jocho assessment (E2E-ENCRYPTED, PII Tier-3) ───────────────────

export async function recordJocho(e: Etzhayyim, input: RecordJochoInput): Promise<RecordJochoOutput> {
  if (!input.assessmentId || !input.subjectDid || !input.consentDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.targetKyuDan) return { status: "rejected", error: "missingTargetKyuDan" };
  for (const v of [input.engagement, input.competence, input.contribution, input.growth, input.resilience]) {
    if (!isPct(v)) return { status: "rejected", error: "invalidAxisScore" };
  }
  const body: JochoAssessmentBody = {
    assessmentId: input.assessmentId,
    subjectDid: input.subjectDid,
    engagement: input.engagement,
    competence: input.competence,
    contribution: input.contribution,
    growth: input.growth,
    resilience: input.resilience,
    targetKyuDan: input.targetKyuDan,
    consentDid: input.consentDid,
    assessedAt: input.assessedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit consented recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: JOCHO_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: jochoRkey(input.assessmentId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, assessmentId: input.assessmentId };
}

async function scanJocho(e: Etzhayyim, maxScan: number): Promise<JochoAssessmentView[]> {
  const out: JochoAssessmentView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<JochoAssessmentBody>({ innerType: JOCHO_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listJocho(e: Etzhayyim, input: ListJochoInput = {}): Promise<ListJochoOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanJocho(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((j) => !input.subjectDid || j.subjectDid === input.subjectDid);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getJocho(e: Etzhayyim, input: GetJochoInput): Promise<GetJochoOutput> {
  if (!input.assessmentId) return { error: "invalidAssessmentId" };
  const all = await scanJocho(e, DEFAULT_MAX_SCAN);
  const found = all.find((j) => j.assessmentId === input.assessmentId);
  if (!found) return { error: "notFound" };
  return { assessment: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const opportunitiesByCategory: Record<string, number> = {};
  let arbitrageOpportunityCount = 0;
  let cursor: string | undefined;
  while (arbitrageOpportunityCount < maxScan) {
    const page = await e.read<ArbitrageOpportunityRecord>({ collection: ARBITRAGE_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      opportunitiesByCategory[r.value.topicCategory] = (opportunitiesByCategory[r.value.topicCategory] ?? 0) + 1;
      arbitrageOpportunityCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const jochoAssessmentCount = (await scanJocho(e, maxScan)).length;
  return {
    arbitrageOpportunityCount,
    jochoAssessmentCount,
    opportunitiesByCategory,
    truncated: arbitrageOpportunityCount >= maxScan || jochoAssessmentCount >= maxScan,
  };
}
