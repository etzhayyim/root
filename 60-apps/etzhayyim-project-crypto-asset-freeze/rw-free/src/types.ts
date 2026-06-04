/**
 * crypto-asset-freeze rw-free — kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-back) + ADR-2605172400
 * (3-axis OR-test) + ADR-2605181100 (kotoba E2E encrypted-record envelope).
 * Founder directive 2026-06-03: PII / CUI / LE may migrate to etzhayyim when
 * made E2E-safe.
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records) — aggregate incident projections by
 *   chain × status (counts only, no wallet addresses, no case IDs, no subject
 *   PII). Frontable open metadata for dashboards / coverage stats.
 *
 *   SENSITIVE / CUI / LE (kotoba E2E, com.etzhayyim.encrypted.record) —
 *     • freezeIncident: LE-restricted incident bodies (sourceCaseId, court-order
 *       CID, wallet addresses under investigation, priority). Sealed via
 *       sdk.encryptedWrite, read-cap = owner DID (+ explicit LE-agency
 *       recipients). The substrate never sees the wallet set in plaintext.
 *     • freezeRequest: per-exchange / per-issuer freeze-request bodies
 *       (incidentId back-reference + target walletAddress + exchange). Also CUI.
 *
 *   STAYS etzhayyim (consumed via consent-capability — NOT a collection):
 *     • Freeze / unfreeze EXECUTION at exchange/issuer (Tether/Circle/CEX) —
 *       a regulated blocking ACTION. (Also fiat-adjacent: see
 *       00-contracts/bpmn/com/etzhayyim/stripe/{freeze,unfreeze}Card.bpmn.)
 *     • Recursive wallet-trace EXECUTION (Pregel, ADR-2605171200) — INFERENCE
 *       compute over the chain graph.
 *   The resulting DATA records (incident / request) migrate here as E2E; only
 *   the execution acts stay etzhayyim.
 *
 * AT-Lexicon: no float — all counts / hops / priority are integers; chain ids
 * and wallet addresses are strings.
 */

// Plaintext public aggregate collection.
export const PROJECTION_COLLECTION = "com.etzhayyim.apps.cryptoAssetFreeze.incidentProjection";
// E2E inner-type NSIDs (body shapes inside the encrypted envelope).
export const INCIDENT_INNER_TYPE = "com.etzhayyim.apps.cryptoAssetFreeze.freezeIncident";
export const REQUEST_INNER_TYPE = "com.etzhayyim.apps.cryptoAssetFreeze.freezeRequest";

export const FREEZE_DID_PREFIX = "did:web:crypto-asset-freeze.etzhayyim.com:" as const;

// ─── Incident projection (PLAINTEXT, public aggregate) ──────────────

export interface IncidentProjectionRecord {
  did: string;
  projectionId: string;
  chain: string;
  status: string;
  incidentCount: number;
  generatedAt: string;
  createdAt: string;
}
export interface IncidentProjectionView extends IncidentProjectionRecord {
  projectionUri: string;
}
export interface RecordProjectionInput {
  projectionId: string;
  chain: string;
  status: string;
  incidentCount: number;
  generatedAt?: string;
}
export interface RecordProjectionOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  projectionUri?: string;
  did?: string;
  projectionId?: string;
  error?: string;
}
export interface ListProjectionsInput {
  chain?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}
export interface ListProjectionsOutput {
  items: IncidentProjectionView[];
  cursor?: string;
  total: number;
}

// ─── Freeze incident (E2E-ENCRYPTED, CUI / LE) ──────────────────────

export interface FreezeIncidentBody {
  incidentId: string;
  /** Originating case id (e.g. yabai / sanctions case). LE-restricted. */
  sourceCaseId: string;
  sourceApp: string;
  chain: string;
  /** integer 0-100 (0 = lowest, 100 = highest). */
  priority: number;
  /** Wallet addresses under investigation. Never plaintext on-substrate. */
  walletAddresses: string[];
  /** Court-order content-id authorizing the freeze (cryptographic audit chain). */
  courtOrderCid?: string;
  status: string;
  openedAt: string;
}
export interface FreezeIncidentView extends FreezeIncidentBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface CreateIncidentInput {
  incidentId: string;
  sourceCaseId: string;
  sourceApp: string;
  chain: string;
  priority: number;
  walletAddresses: string[];
  courtOrderCid?: string;
  status?: string;
  openedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface CreateIncidentOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  incidentId?: string;
  walletCount?: number;
  error?: string;
}
export interface ListIncidentsInput {
  chain?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}
export interface ListIncidentsOutput {
  items: FreezeIncidentView[];
  cursor?: string;
  total: number;
}
export interface GetIncidentInput {
  incidentId: string;
}
export interface GetIncidentOutput {
  incident?: FreezeIncidentView;
  error?: string;
}

// ─── Freeze request (E2E-ENCRYPTED, CUI / LE) ───────────────────────

export interface FreezeRequestBody {
  requestId: string;
  /** Back-reference to the freezeIncident body field (E2E = not FK-indexable). */
  incidentId: string;
  exchange: string;
  walletAddress: string;
  chain: string;
  status: string;
  requestedAt: string;
}
export interface FreezeRequestView extends FreezeRequestBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RequestFreezeInput {
  requestId: string;
  incidentId: string;
  exchange: string;
  walletAddress: string;
  chain?: string;
  status?: string;
  requestedAt?: string;
  recipients?: string[];
}
export interface RequestFreezeOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  requestId?: string;
  error?: string;
}
export interface ListRequestsInput {
  incidentId?: string;
  exchange?: string;
  limit?: number;
  cursor?: string;
}
export interface ListRequestsOutput {
  items: FreezeRequestView[];
  cursor?: string;
  total: number;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  incidentProjectionCount?: number;
  freezeIncidentCount?: number;
  freezeRequestCount?: number;
  projectionsByChain?: Record<string, number>;
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
/** Plain string check — no viem/ethers; just shape, not checksum. */
export function isWalletAddress(s: unknown): s is string {
  return typeof s === "string" && s.trim().length > 0;
}
export function projectionDidFor(id: string): string {
  return `${FREEZE_DID_PREFIX}proj:${id.toLowerCase()}`;
}
export function projectionRkey(id: string): string {
  return `proj-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function incidentRkey(id: string): string {
  return `incident-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function requestRkey(id: string): string {
  return `request-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
