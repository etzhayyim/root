/**
 * hc kotoba — Human Computing Platform (gig + micro-task + Service-Provider
 * onboarding). Follows the intel E2E reference: plaintext public-meta + kotoba
 * E2E sensitive payload.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-back) + ADR-2605172400
 * (3-axis OR-test) + ADR-2605181100 (kotoba E2E encrypted-record envelope).
 * Founder directive 2026-06-03: PII / CUI / LE migrate to etzhayyim when made
 * E2E-safe.
 *
 * The concrete, fully-specified hc data surface is the contracts + SP-registration
 * domain (the shift/task lexicons are stub-only `in:[]`), so the split is built
 * from that real surface:
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records) — contract templates: the 4 published legal
 *   agreements (Worker / SP-Service / Task / Shift), each public reference
 *   metadata (type, locale, governingLaw, jurisdiction, effectiveDate, DID).
 *   Open, frontable catalog data — no PII.
 *
 *   SENSITIVE / PII+CUI (kotoba E2E, com.etzhayyim.encrypted.record) — Service-
 *   Provider KYC/KYB applications: legalName, contactEmail, LEI, documents
 *   (confidential business PII) folded together with the verification *result*
 *   fields (sanctionsClear / legalEntityVerified / verdict / findings = CUI).
 *   Written via sdk.encryptedWrite (read-cap = owner DID + explicit recipients),
 *   so KYC/KYB content lives on-substrate encrypted, never etzhayyim-resident.
 *
 *   STAYS etzhayyim (consumed via consent-capability) — fiat shift settlement (JPY
 *   銀行振込 / 即時払い), USDC/USDT escrow EXECUTION, sanctions-SCREENING execution
 *   (yabai), credential/secret custody. These are the regulated *acts*; the
 *   resulting result records (e.g. the sanctionsClear boolean) migrate E2E.
 *
 * AT-Lexicon: no float — counts/years are integers; no money fields here (fee
 * data stays in etzhayyim execution). Verdict is an enum string, not a score.
 */

// Plaintext public collection.
export const CONTRACT_TEMPLATE_COLLECTION = "com.etzhayyim.apps.hc.contractTemplate";
// E2E inner-type NSID (body shape inside the encrypted envelope).
export const SP_APPLICATION_INNER_TYPE = "com.etzhayyim.apps.hc.spApplication";

export const HC_DID_PREFIX = "did:web:hc.etzhayyim.com:" as const;

// ─── Contract template (PLAINTEXT, public catalog) ──────────────────

export interface ContractTemplateRecord {
  did: string;
  contractType: string;
  locale: string;
  governingLaw: string;
  jurisdiction: string;
  effectiveDate: string;
  rev: string;
  createdAt: string;
}
export interface ContractTemplateView extends ContractTemplateRecord {
  templateUri: string;
}
export interface RegisterContractInput {
  contractType: string;
  locale: string;
  governingLaw?: string;
  jurisdiction?: string;
  effectiveDate?: string;
  rev?: string;
}
export interface RegisterContractOutput {
  status: "registered" | "alreadyExists" | "rejected";
  templateUri?: string;
  did?: string;
  contractType?: string;
  locale?: string;
  error?: string;
}
export interface GetContractInput {
  contractType: string;
  locale: string;
}
export interface GetContractOutput {
  template?: ContractTemplateView;
  error?: string;
}
export interface ListContractsInput {
  contractType?: string;
  locale?: string;
  limit?: number;
  cursor?: string;
}
export interface ListContractsOutput {
  items: ContractTemplateView[];
  cursor?: string;
  total: number;
}

// ─── SP application (E2E-ENCRYPTED, PII + CUI) ──────────────────────

export type SpVerdict = "pending" | "approved" | "rejected" | "needsMoreInfo";

export interface SpApplicationBody {
  applicationId: string;
  /** PII: registered legal name of the manufacturer/factory. */
  legalName: string;
  tradeName?: string;
  /** PII: applicant contact email. */
  contactEmail: string;
  countryIso3: string;
  /** Legal Entity Identifier (confidential business ref). */
  lei?: string;
  category: string;
  factoryType?: string;
  /** Confidential supporting-document reference / blob pointer. */
  documents?: string;
  isicCodes: string[];
  // ── KYC/KYB verification result (CUI) folded into the same E2E body ──
  verdict: SpVerdict;
  sanctionsClear?: boolean;
  legalEntityVerified?: boolean;
  findings?: string;
  submittedAt: string;
}
export interface SpApplicationView extends SpApplicationBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RegisterSpApplicationInput {
  applicationId: string;
  legalName: string;
  contactEmail: string;
  countryIso3: string;
  category: string;
  isicCodes?: string[];
  tradeName?: string;
  lei?: string;
  factoryType?: string;
  documents?: string;
  verdict?: SpVerdict;
  sanctionsClear?: boolean;
  legalEntityVerified?: boolean;
  findings?: string;
  submittedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RegisterSpApplicationOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  applicationId?: string;
  error?: string;
}
export interface ListSpApplicationsInput {
  countryIso3?: string;
  verdict?: SpVerdict;
  limit?: number;
  cursor?: string;
}
export interface ListSpApplicationsOutput {
  items: SpApplicationView[];
  cursor?: string;
  total: number;
}
export interface GetSpApplicationInput {
  applicationId: string;
}
export interface GetSpApplicationOutput {
  application?: SpApplicationView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  contractTemplateCount?: number;
  spApplicationCount?: number;
  templatesByLocale?: Record<string, number>;
  applicationsByVerdict?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

const VERDICTS: ReadonlySet<string> = new Set<SpVerdict>([
  "pending",
  "approved",
  "rejected",
  "needsMoreInfo",
]);
export function isVerdict(v: unknown): v is SpVerdict {
  return typeof v === "string" && VERDICTS.has(v);
}
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export function isEmail(s: unknown): s is string {
  return typeof s === "string" && EMAIL_RE.test(s);
}
export function slug(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
export function contractDidFor(contractType: string, locale: string): string {
  return `${HC_DID_PREFIX}legal:${slug(contractType)}:${slug(locale)}`;
}
export function contractRkey(contractType: string, locale: string): string {
  return `ct-${slug(contractType)}-${slug(locale)}`;
}
export function spRkey(applicationId: string): string {
  return `sp-${slug(applicationId)}`;
}
