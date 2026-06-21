/**
 * yabai kotoba — registry. kotoba-E2E split.
 *
 * Plaintext path (threatIndicator): sdk.write / sdk.read — public CTI reference
 * (CVE / MITRE / ASN / IOC) shared in the clear.
 * E2E path (riskAssessment): sdk.encryptedWrite / sdk.encryptedRead — per-subject
 * CUI/LE risk scores sealed in the kotoba envelope (ADR-2605181100), read-cap =
 * owner DID + explicit recipients. The substrate never sees subject PII in
 * plaintext.
 *
 * WAF enforcement / blocking actions, live sanctions-feed screening, and LLM
 * analysis inference STAY etzhayyim (consumed via consent-capability); only the
 * resulting DATA records migrate here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  RISK_ASSESSMENT_INNER_TYPE,
  THREAT_INDICATOR_COLLECTION,
  assessmentRkey,
  indicatorDidFor,
  indicatorRkey,
  isIndicatorType,
  isPct,
  isRiskBand,
  type CoverageInput,
  type CoverageOutput,
  type GetAssessmentInput,
  type GetAssessmentOutput,
  type GetIndicatorInput,
  type GetIndicatorOutput,
  type ListAssessmentsInput,
  type ListAssessmentsOutput,
  type ListIndicatorsInput,
  type ListIndicatorsOutput,
  type RecordAssessmentInput,
  type RecordAssessmentOutput,
  type RegisterIndicatorInput,
  type RegisterIndicatorOutput,
  type RiskAssessmentBody,
  type RiskAssessmentView,
  type ThreatIndicatorRecord,
  type ThreatIndicatorView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Threat indicator (PLAINTEXT) ───────────────────────────────────

export async function registerIndicator(e: Etzhayyim, input: RegisterIndicatorInput): Promise<RegisterIndicatorOutput> {
  if (!input.indicatorId || !input.value || !input.source) return { status: "rejected", error: "missingRequiredFields" };
  if (!isIndicatorType(input.indicatorType)) return { status: "rejected", error: "invalidIndicatorType" };
  if (!isPct(input.severity)) return { status: "rejected", error: "invalidSeverity" };
  const rkey = indicatorRkey(input.indicatorId);
  const existing = await e
    .read<ThreatIndicatorRecord>({ collection: THREAT_INDICATOR_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", indicatorUri: existing.records[0].uri, did: existing.records[0].value.did, indicatorId: input.indicatorId };
  }
  const now = new Date().toISOString();
  const did = indicatorDidFor(input.indicatorId);
  const record: ThreatIndicatorRecord = {
    did,
    indicatorId: input.indicatorId,
    indicatorType: input.indicatorType,
    value: input.value,
    severity: input.severity,
    source: input.source,
    observedAt: input.observedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: THREAT_INDICATOR_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", indicatorUri: receipt.uri, did, indicatorId: input.indicatorId };
}

export async function listIndicators(e: Etzhayyim, input: ListIndicatorsInput = {}): Promise<ListIndicatorsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ThreatIndicatorRecord>({ collection: THREAT_INDICATOR_COLLECTION, cursor: input.cursor, limit });
  const items: ThreatIndicatorView[] = resp.records
    .filter((r) => !input.indicatorType || r.value.indicatorType === input.indicatorType)
    .map((r) => ({ ...r.value, indicatorUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

export async function getIndicator(e: Etzhayyim, input: GetIndicatorInput): Promise<GetIndicatorOutput> {
  if (!input.indicatorId) return { error: "invalidIndicatorId" };
  const rkey = indicatorRkey(input.indicatorId);
  const resp = await e
    .read<ThreatIndicatorRecord>({ collection: THREAT_INDICATOR_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { indicator: { ...hit.value, indicatorUri: hit.uri } };
}

// ─── Risk assessment (E2E-ENCRYPTED, CUI + LE) ──────────────────────

export async function recordAssessment(e: Etzhayyim, input: RecordAssessmentInput): Promise<RecordAssessmentOutput> {
  if (!input.assessmentId || !input.subjectDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!isPct(input.riskScore)) return { status: "rejected", error: "invalidRiskScore" };
  if (!isPct(input.confidence)) return { status: "rejected", error: "invalidConfidence" };
  if (!isRiskBand(input.band)) return { status: "rejected", error: "invalidBand" };
  const body: RiskAssessmentBody = {
    assessmentId: input.assessmentId,
    subjectDid: input.subjectDid,
    riskScore: input.riskScore,
    band: input.band,
    confidence: input.confidence,
    signals: input.signals ?? [],
    assessedAt: input.assessedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: RISK_ASSESSMENT_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: assessmentRkey(input.assessmentId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, assessmentId: input.assessmentId };
}

async function scanAssessments(e: Etzhayyim, maxScan: number): Promise<RiskAssessmentView[]> {
  const out: RiskAssessmentView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<RiskAssessmentBody>({ innerType: RISK_ASSESSMENT_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listAssessments(e: Etzhayyim, input: ListAssessmentsInput = {}): Promise<ListAssessmentsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanAssessments(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((a) => !input.band || a.band === input.band);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getAssessment(e: Etzhayyim, input: GetAssessmentInput): Promise<GetAssessmentOutput> {
  if (!input.assessmentId) return { error: "invalidAssessmentId" };
  const all = await scanAssessments(e, DEFAULT_MAX_SCAN);
  const found = all.find((a) => a.assessmentId === input.assessmentId);
  if (!found) return { error: "notFound" };
  return { assessment: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const indicatorsByType: Record<string, number> = {};
  let threatIndicatorCount = 0;
  let cursor: string | undefined;
  while (threatIndicatorCount < maxScan) {
    const page = await e.read<ThreatIndicatorRecord>({ collection: THREAT_INDICATOR_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      indicatorsByType[r.value.indicatorType] = (indicatorsByType[r.value.indicatorType] ?? 0) + 1;
      threatIndicatorCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const riskAssessmentCount = (await scanAssessments(e, maxScan)).length;
  return {
    threatIndicatorCount,
    riskAssessmentCount,
    indicatorsByType,
    truncated: threatIndicatorCount >= maxScan || riskAssessmentCount >= maxScan,
  };
}
