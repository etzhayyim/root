/**
 * open-ossekai kotoba — kotoba-E2E split (plaintext public-good catalog +
 * kotoba-E2E consent-gated PII Tier-3 payload).
 *
 * Per ADR-2606011400 (Consensys) + ADR-2605172400 (3-axis) + ADR-2605181100
 * (kotoba E2E encrypted-record envelope) + ADR-0018 (PII Tier-3 + consent-gate)
 * + ADR-2605264000 (ossekai information-arbitrage actor). Founder directive
 * 2026-06-03: PII / CUI / LE may migrate to etzhayyim when E2E-safe.
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records) — L2 arbitrage opportunities: per-detection
 *   public-good information-asymmetry gaps (topic category, scope, severity,
 *   order-of-magnitude affected-population estimate). No subject PII; these are
 *   community-benefit intel pockets meant to be broadly surfaced. Frontable
 *   open catalog (com.etzhayyim.ossekai.arbitrageGapReport shape).
 *
 *   SENSITIVE / PII Tier-3 (kotoba E2E, com.etzhayyim.encrypted.record) — L3
 *   per-person jocho (情緒) assessments: subjectDid + 5-axis Well-Becoming
 *   scores + kyu/dan target. ADR-0018 Tier-3: requires prior actor consent and
 *   MUST NOT be substrate-visible in plaintext. Written via sdk.encryptedWrite
 *   (read-cap = subject/owner DID auto + explicit consented recipients), read
 *   via sdk.encryptedRead. The substrate never sees a person's jocho scores.
 *
 *   STAYS etzhayyim (consumed via consent-capability) — L1 LLM intel-brief
 *   generation (Murakumo inference), jocho-scoring INFERENCE execution,
 *   framing-audit inference, and fiat sales-lead propagation
 *   (vertex_open_sales_lead). These are regulated *acts* (GPU/LLM inference +
 *   downstream commercial settlement), not the resulting data records. The
 *   jocho DATA migrates E2E; only the scoring/inference EXECUTION stays etzhayyim.
 *
 * AT-Lexicon: no float — affected-population + axis scores + confidence are
 * integers; scores/confidence are 0-100.
 */

// Plaintext public collection (L2 arbitrage gap catalog).
export const ARBITRAGE_COLLECTION = "com.etzhayyim.apps.openOssekai.arbitrageOpportunity";
// E2E inner-type NSID (body shape inside the encrypted envelope; L3 jocho PII).
export const JOCHO_INNER_TYPE = "com.etzhayyim.apps.openOssekai.jochoAssessment";

export const OSSEKAI_DID_PREFIX = "did:web:open-ossekai.etzhayyim.com:" as const;

export type AsymmetrySeverity = "low" | "mid" | "high" | "critical";
export type ScopeKind = "global" | "jurisdiction" | "community-site" | "cross-jurisdictional";

// ─── Arbitrage opportunity (PLAINTEXT, public-good catalog) ──────────

export interface ArbitrageOpportunityRecord {
  did: string;
  arbId: string;
  topicCategory: string;
  scopeKind: ScopeKind;
  severity: AsymmetrySeverity;
  /** integer ≥ 0: order-of-magnitude estimate of people the gap matters to. */
  estimatedAffectedPopulation: number;
  status: string;
  generatedAt: string;
  createdAt: string;
}
export interface ArbitrageOpportunityView extends ArbitrageOpportunityRecord {
  arbUri: string;
}
export interface RegisterArbitrageInput {
  arbId: string;
  topicCategory: string;
  scopeKind: ScopeKind;
  severity: AsymmetrySeverity;
  estimatedAffectedPopulation: number;
  status?: string;
  generatedAt?: string;
}
export interface RegisterArbitrageOutput {
  status: "registered" | "alreadyExists" | "rejected";
  arbUri?: string;
  did?: string;
  arbId?: string;
  error?: string;
}
export interface GetArbitrageInput {
  arbId: string;
}
export interface GetArbitrageOutput {
  opportunity?: ArbitrageOpportunityView;
  error?: string;
}
export interface ListArbitrageInput {
  topicCategory?: string;
  severity?: AsymmetrySeverity;
  limit?: number;
  cursor?: string;
}
export interface ListArbitrageOutput {
  items: ArbitrageOpportunityView[];
  cursor?: string;
  total: number;
}

// ─── Jocho assessment (E2E-ENCRYPTED, PII Tier-3 / consent-gated) ────

export interface JochoAssessmentBody {
  assessmentId: string;
  subjectDid: string;
  /** integer 0-100. */
  engagement: number;
  /** integer 0-100. */
  competence: number;
  /** integer 0-100. */
  contribution: number;
  /** integer 0-100. */
  growth: number;
  /** integer 0-100. */
  resilience: number;
  /** kyu/dan ladder target, e.g. "3-kyu" / "1-dan". */
  targetKyuDan: string;
  /** DID that granted consent (ADR-0018 Tier-3 gate). */
  consentDid: string;
  assessedAt: string;
}
export interface JochoAssessmentView extends JochoAssessmentBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordJochoInput {
  assessmentId: string;
  subjectDid: string;
  engagement: number;
  competence: number;
  contribution: number;
  growth: number;
  resilience: number;
  targetKyuDan: string;
  consentDid: string;
  assessedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RecordJochoOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  assessmentId?: string;
  error?: string;
}
export interface ListJochoInput {
  subjectDid?: string;
  limit?: number;
  cursor?: string;
}
export interface ListJochoOutput {
  items: JochoAssessmentView[];
  cursor?: string;
  total: number;
}
export interface GetJochoInput {
  assessmentId: string;
}
export interface GetJochoOutput {
  assessment?: JochoAssessmentView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  arbitrageOpportunityCount?: number;
  jochoAssessmentCount?: number;
  opportunitiesByCategory?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPct(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 100;
}
export function isSeverity(s: unknown): s is AsymmetrySeverity {
  return s === "low" || s === "mid" || s === "high" || s === "critical";
}
export function isScopeKind(s: unknown): s is ScopeKind {
  return s === "global" || s === "jurisdiction" || s === "community-site" || s === "cross-jurisdictional";
}
export function arbitrageDidFor(id: string): string {
  return `${OSSEKAI_DID_PREFIX}arb:${id.toLowerCase()}`;
}
export function arbitrageRkey(id: string): string {
  return `arb-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function jochoRkey(id: string): string {
  return `jocho-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
