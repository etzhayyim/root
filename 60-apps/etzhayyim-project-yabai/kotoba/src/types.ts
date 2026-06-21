/**
 * yabai kotoba — risk-intelligence product front, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-vendor) + ADR-2605172400
 * (3-axis liability/custody/settlement) + ADR-2605181100 (kotoba E2E encrypted
 * record envelope). Founder directive 2026-06-03: PII / CUI / LE may migrate to
 * etzhayyim when made safe via kotoba E2E.
 *
 * yabai = AML / sanctions / anti-social-forces risk scoring + cyber threat
 * intelligence (CTI). SPLIT:
 *
 *   PUBLIC (plaintext AT records) — threatIndicator: open CTI reference data
 *   (CVE / MITRE technique / ASN / IOC). Non-PII catalog/reference shared in the
 *   clear, plus aggregate coverage stats. Frontable open metadata.
 *
 *   SENSITIVE / CUI+LE (kotoba E2E, com.etzhayyim.apps.yabai.riskAssessment) —
 *   per-subject risk assessments (subjectDid + score + sanction / AML /
 *   anti-social-forces signals). Written via sdk.encryptedWrite (read-cap =
 *   owner DID + explicit recipients), so confidential per-person scoring lives
 *   on-substrate encrypted, never etzhayyim-resident or substrate-plaintext.
 *
 *   STAYS etzhayyim (consumed via consent-capability, NOT a collection) — WAF
 *   enforcement / blocking ACTIONS (Deny/Challenge), live sanctions-feed
 *   screening EXECUTION, and LLM analysis INFERENCE. These are regulated *acts*;
 *   only the EXECUTION stays etzhayyim. Resulting risk DATA records migrate (E2E).
 *
 * AT-Lexicon: no float. severity/confidence/riskScore are integers (0-100 where
 * a percentage); inherently-decimal CTI metrics (e.g. CVSS) are scaled to
 * integers (cvssX10 = cvss*10, 0-100). Money/decimals would be decimal STRINGS.
 */

// Plaintext public collection.
export const THREAT_INDICATOR_COLLECTION = "com.etzhayyim.apps.yabai.threatIndicator";
// E2E inner-type NSID (body shape inside the encrypted envelope).
export const RISK_ASSESSMENT_INNER_TYPE = "com.etzhayyim.apps.yabai.riskAssessment";

export const YABAI_DID_PREFIX = "did:web:yabai.etzhayyim.com:" as const;

export type IndicatorType = "cve" | "mitre" | "asn" | "ioc";
export type RiskBand = "monitor" | "challenge" | "deny" | "clear";

// ─── Threat indicator (PLAINTEXT, public CTI reference) ─────────────

export interface ThreatIndicatorRecord {
  did: string;
  indicatorId: string;
  /** cve | mitre | asn | ioc */
  indicatorType: IndicatorType;
  /** e.g. "CVE-2026-1234", "T1566", "AS135377", "1.2.3.4" */
  value: string;
  /** integer 0-100 severity (CVSS scaled ×10, EPSS×100, etc.). */
  severity: number;
  source: string;
  observedAt: string;
  createdAt: string;
}
export interface ThreatIndicatorView extends ThreatIndicatorRecord {
  indicatorUri: string;
}
export interface RegisterIndicatorInput {
  indicatorId: string;
  indicatorType: IndicatorType;
  value: string;
  severity: number;
  source: string;
  observedAt?: string;
}
export interface RegisterIndicatorOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  indicatorUri?: string;
  did?: string;
  indicatorId?: string;
  error?: string;
}
export interface ListIndicatorsInput {
  indicatorType?: IndicatorType;
  limit?: number;
  cursor?: string;
}
export interface ListIndicatorsOutput {
  items: ThreatIndicatorView[];
  cursor?: string;
  total: number;
}
export interface GetIndicatorInput {
  indicatorId: string;
}
export interface GetIndicatorOutput {
  indicator?: ThreatIndicatorView;
  error?: string;
}

// ─── Risk assessment (E2E-ENCRYPTED, CUI + LE per-subject scores) ────

export interface RiskAssessmentBody {
  assessmentId: string;
  /** Subject under assessment (person/org/IP DID). PII/LE — never plaintext. */
  subjectDid: string;
  /** integer 0-100 composite risk score. */
  riskScore: number;
  band: RiskBand;
  /** integer 0-100 analyst confidence. */
  confidence: number;
  /** CTI categories that drove the score, e.g. ["SanctionHit","AMLPattern"]. */
  signals: string[];
  assessedAt: string;
}
export interface RiskAssessmentView extends RiskAssessmentBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordAssessmentInput {
  assessmentId: string;
  subjectDid: string;
  riskScore: number;
  band: RiskBand;
  confidence: number;
  signals?: string[];
  assessedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RecordAssessmentOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  assessmentId?: string;
  error?: string;
}
export interface ListAssessmentsInput {
  band?: RiskBand;
  limit?: number;
  cursor?: string;
}
export interface ListAssessmentsOutput {
  items: RiskAssessmentView[];
  cursor?: string;
  total: number;
}
export interface GetAssessmentInput {
  assessmentId: string;
}
export interface GetAssessmentOutput {
  assessment?: RiskAssessmentView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  threatIndicatorCount?: number;
  riskAssessmentCount?: number;
  indicatorsByType?: Record<string, number>;
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
const INDICATOR_TYPES: ReadonlySet<string> = new Set(["cve", "mitre", "asn", "ioc"]);
const RISK_BANDS: ReadonlySet<string> = new Set(["monitor", "challenge", "deny", "clear"]);
export function isIndicatorType(s: unknown): s is IndicatorType {
  return typeof s === "string" && INDICATOR_TYPES.has(s);
}
export function isRiskBand(s: unknown): s is RiskBand {
  return typeof s === "string" && RISK_BANDS.has(s);
}
export function indicatorDidFor(id: string): string {
  return `${YABAI_DID_PREFIX}indicator:${id.toLowerCase()}`;
}
export function indicatorRkey(id: string): string {
  return `ind-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function assessmentRkey(id: string): string {
  return `risk-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
