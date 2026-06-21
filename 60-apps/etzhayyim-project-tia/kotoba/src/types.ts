/**
 * tia kotoba — Internet Account Protection (TIA) front, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys) + ADR-2605172400 (3-axis) + ADR-2605181100
 * (kotoba E2E encrypted-record envelope). Founder directive 2026-06-03: PII /
 * CUI / LE may migrate to etzhayyim when made safe via kotoba E2E.
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records) — protectedPlatform: the platform catalog
 *   (Facebook / LinkedIn / X / LINE / Instagram) = reference data, seek URLs,
 *   display labels. Non-sensitive open metadata, frontable.
 *
 *   SENSITIVE / PII (kotoba E2E, com.etzhayyim.encrypted.record) —
 *     protectedAccount: the account a person registers for protection
 *     (accountName / userId / accountUrl + owner DID) — personal identity data.
 *     detectionResult: per-account impersonation findings (similarity score,
 *     suspect URL, evidence) — per-person threat intelligence.
 *   Both sealed via sdk.encryptedWrite (read-cap = owner DID auto + explicit
 *   recipients). The substrate never sees the PII / findings in plaintext.
 *
 *   STAYS etzhayyim (consumed via consent-capability, NOT a collection) — Gemini 2.5
 *   Flash similarity-evaluation INFERENCE execution + automated platform
 *   notification / takedown-reporting ACTIONS (the regulated *acts*). The
 *   resulting detectionResult DATA records migrate here as E2E; only the
 *   inference + enforcement execution stays etzhayyim.
 *
 * AT-Lexicon: no float. similarityScore is an integer 0-100 (percent), not the
 * legacy 0.0-1.0 double; counts are non-negative integers.
 */

// Plaintext public collection (platform catalog).
export const PLATFORM_COLLECTION = "com.etzhayyim.apps.tia.protectedPlatform";
// E2E inner-type NSIDs (body shapes inside the encrypted envelope).
export const ACCOUNT_INNER_TYPE = "com.etzhayyim.apps.tia.protectedAccount";
export const DETECTION_INNER_TYPE = "com.etzhayyim.apps.tia.detectionResult";

export const TIA_DID_PREFIX = "did:web:tia.etzhayyim.com:" as const;

// ─── Protected platform (PLAINTEXT, public catalog) ─────────────────

export interface ProtectedPlatformRecord {
  did: string;
  platformType: string;
  displayName: string;
  seekUrl: string;
  createdAt: string;
}
export interface ProtectedPlatformView extends ProtectedPlatformRecord {
  platformUri: string;
}
export interface RegisterPlatformInput {
  platformType: string;
  displayName: string;
  seekUrl: string;
}
export interface RegisterPlatformOutput {
  status: "registered" | "alreadyExists" | "rejected";
  platformUri?: string;
  did?: string;
  platformType?: string;
  error?: string;
}
export interface GetPlatformInput {
  platformType: string;
}
export interface GetPlatformOutput {
  platform?: ProtectedPlatformView;
  error?: string;
}
export interface ListPlatformsInput {
  platformType?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPlatformsOutput {
  items: ProtectedPlatformView[];
  cursor?: string;
  total: number;
}

// ─── Protected account (E2E-ENCRYPTED, PII) ─────────────────────────

export interface ProtectedAccountBody {
  accountId: string;
  ownerDid: string;
  platformType: string;
  accountName: string;
  userId: string;
  accountUrl?: string;
  registeredAt: string;
}
export interface ProtectedAccountView extends ProtectedAccountBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RegisterAccountInput {
  accountId: string;
  ownerDid: string;
  platformType: string;
  accountName: string;
  userId: string;
  accountUrl?: string;
  registeredAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RegisterAccountOutput {
  status: "registered" | "rejected";
  uri?: string;
  keyId?: string;
  accountId?: string;
  error?: string;
}
export interface ListAccountsInput {
  platformType?: string;
  limit?: number;
  cursor?: string;
}
export interface ListAccountsOutput {
  items: ProtectedAccountView[];
  cursor?: string;
  total: number;
}
export interface GetAccountInput {
  accountId: string;
}
export interface GetAccountOutput {
  account?: ProtectedAccountView;
  error?: string;
}

// ─── Detection result (E2E-ENCRYPTED, per-person threat intel) ──────

export interface DetectionResultBody {
  detectionId: string;
  /** FK → ProtectedAccountBody.accountId. */
  internetAccountId: string;
  platformType: string;
  /** integer 0-100 (percent). Legacy 0.0-1.0 double rescaled to integer. */
  similarityScore: number;
  suspectUrl?: string;
  detectedAt: string;
}
export interface DetectionResultView extends DetectionResultBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordDetectionInput {
  detectionId: string;
  internetAccountId: string;
  platformType: string;
  similarityScore: number;
  suspectUrl?: string;
  detectedAt?: string;
  recipients?: string[];
}
export interface RecordDetectionOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  detectionId?: string;
  error?: string;
}
export interface ListDetectionsInput {
  internetAccountId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListDetectionsOutput {
  items: DetectionResultView[];
  cursor?: string;
  total: number;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  protectedPlatformCount?: number;
  protectedAccountCount?: number;
  detectionResultCount?: number;
  accountsByPlatform?: Record<string, number>;
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
export function isHttpUrl(s: unknown): s is string {
  return typeof s === "string" && /^https?:\/\//.test(s);
}
export function platformDidFor(id: string): string {
  return `${TIA_DID_PREFIX}plat:${id.toLowerCase()}`;
}
export function slug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
export function platformRkey(id: string): string {
  return `plat-${slug(id)}`;
}
export function accountRkey(id: string): string {
  return `acct-${slug(id)}`;
}
export function detectionRkey(id: string): string {
  return `det-${slug(id)}`;
}
