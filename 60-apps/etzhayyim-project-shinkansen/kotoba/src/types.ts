/**
 * shinkansen (新幹線) kotoba — public rail reference: lines + timetables +
 * fares + operation status.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test) +
 * ADR-0014 (PII Tier-3 + cohort-first).
 *
 * SPLIT (this app is (c) mixed; the split is already in the app's design —
 * "AT Repo: anonymized fare comparison のみ; Preferences Tier-3: reservation"):
 *   PUBLIC (THIS PACKAGE) — timetable, fare comparison, operation status. These
 *   are public rail reference data: no PII, no settlement, no liability.
 *     → migrated to etzhayyim front (AT PDS records, replaces RW).
 *
 *   REGULATED (STAYS etzhayyim, NOT in this package) — `reserveSeat` +
 *   `searchAvailability` + the reservation collection (reservation_id, user_did,
 *   name, payment, seat_number) are **Tier-3 PII custody** (Custody axis) plus
 *   live SmartEX / ekinet booking proxies that move fare money (Settlement axis).
 *   Remain an etzhayyim regulated function consumed via consent-capability.
 *
 * AT-Lexicon: no float. Times are "HH:MM" strings; fares are decimal JPY
 * STRINGS; delayMinutes is an integer.
 *
 * Identity hierarchy:
 *   did:web:shinkansen.etzhayyim.com                      — controller
 *   did:web:shinkansen.etzhayyim.com:line:{lineId}        — a rail line
 *   did:web:shinkansen.etzhayyim.com:tt:{entryId}         — a timetable entry
 *   did:web:shinkansen.etzhayyim.com:fare:{fareId}        — a fare row
 *   did:web:shinkansen.etzhayyim.com:op:{operationId}     — an operation-status row
 */

export const SHINKANSEN_DID_PREFIX = "did:web:shinkansen.etzhayyim.com:" as const;

export const LINE_COLLECTION = "com.etzhayyim.apps.shinkansen.line";
export const TIMETABLE_COLLECTION = "com.etzhayyim.apps.shinkansen.timetable";
export const FARE_COLLECTION = "com.etzhayyim.apps.shinkansen.fare";
export const OPERATION_COLLECTION = "com.etzhayyim.apps.shinkansen.operation";

// ─── Enums ──────────────────────────────────────────────────────────

export type SeatClass = "ordinary" | "green" | "granclass" | "unreserved";
export type FareType = "regular" | "early-bird" | "round-trip" | "ic-discount" | "other";
export type Platform = "smartex" | "ekinet" | "jr" | "other";
export type OperationStatus = "normal" | "delayed" | "suspended" | "partial";

export const SEAT_CLASSES: ReadonlySet<string> = new Set(["ordinary", "green", "granclass", "unreserved"]);
export const FARE_TYPES: ReadonlySet<string> = new Set(["regular", "early-bird", "round-trip", "ic-discount", "other"]);
export const PLATFORMS: ReadonlySet<string> = new Set(["smartex", "ekinet", "jr", "other"]);
export const OPERATION_STATUSES: ReadonlySet<string> = new Set(["normal", "delayed", "suspended", "partial"]);

// ─── Line ───────────────────────────────────────────────────────────

export interface LineRecord {
  did: string;
  lineId: string;
  name: string;
  operator: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface LineView extends LineRecord {
  lineUri: string;
}
export interface RegisterLineInput {
  lineId: string;
  name: string;
  operator: string;
  sourceUrl?: string;
}
export interface RegisterLineOutput {
  status: "registered" | "alreadyExists" | "rejected";
  lineUri?: string;
  did?: string;
  lineId?: string;
  error?: string;
}
export interface ListLinesInput {
  operator?: string;
  limit?: number;
  cursor?: string;
}
export interface ListLinesOutput {
  items: LineView[];
  cursor?: string;
  total: number;
}

// ─── Timetable ──────────────────────────────────────────────────────

export interface TimetableRecord {
  did: string;
  entryId: string;
  /** FK → line. */
  lineId: string;
  trainNumber: string;
  trainType: string;
  departureStation: string;
  arrivalStation: string;
  /** "HH:MM" 24h. */
  departTime: string;
  arriveTime: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface TimetableView extends TimetableRecord {
  timetableUri: string;
}
export interface AddTimetableInput {
  entryId: string;
  lineId: string;
  trainNumber: string;
  trainType: string;
  departureStation: string;
  arrivalStation: string;
  departTime: string;
  arriveTime: string;
  sourceUrl?: string;
}
export interface AddTimetableOutput {
  status: "added" | "alreadyExists" | "rejected" | "lineNotFound";
  timetableUri?: string;
  did?: string;
  entryId?: string;
  error?: string;
}
export interface ListTimetableInput {
  lineId?: string;
  trainType?: string;
  departureStation?: string;
  arrivalStation?: string;
  limit?: number;
  cursor?: string;
}
export interface ListTimetableOutput {
  items: TimetableView[];
  cursor?: string;
  total: number;
}

// ─── Fare ───────────────────────────────────────────────────────────

export interface FareRecord {
  did: string;
  fareId: string;
  fromStation: string;
  toStation: string;
  fareType: FareType;
  seatClass: SeatClass;
  /** Fare in JPY (decimal string). */
  priceJpy: string;
  discountName?: string;
  validFrom?: string;
  validTo?: string;
  platform: Platform;
  sourceUrl?: string;
  createdAt: string;
}
export interface FareView extends FareRecord {
  fareUri: string;
}
export interface AddFareInput {
  fareId: string;
  fromStation: string;
  toStation: string;
  fareType: FareType;
  seatClass: SeatClass;
  priceJpy: string;
  platform: Platform;
  discountName?: string;
  validFrom?: string;
  validTo?: string;
  sourceUrl?: string;
}
export interface AddFareOutput {
  status: "added" | "alreadyExists" | "rejected";
  fareUri?: string;
  did?: string;
  fareId?: string;
  error?: string;
}
export interface ListFaresInput {
  fromStation?: string;
  toStation?: string;
  seatClass?: SeatClass;
  fareType?: FareType;
  platform?: Platform;
  limit?: number;
  cursor?: string;
}
export interface ListFaresOutput {
  items: FareView[];
  /** Cheapest fare in the returned page, if any. */
  cheapest?: FareView;
  cursor?: string;
  total: number;
}

// ─── Operation status ───────────────────────────────────────────────

export interface OperationRecord {
  did: string;
  operationId: string;
  /** FK → line. */
  lineId: string;
  status: OperationStatus;
  delayMinutes?: number;
  reason?: string;
  observedAt: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface OperationView extends OperationRecord {
  operationUri: string;
}
export interface RecordOperationInput {
  operationId: string;
  lineId: string;
  status: OperationStatus;
  observedAt: string;
  delayMinutes?: number;
  reason?: string;
  sourceUrl?: string;
}
export interface RecordOperationOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "lineNotFound";
  operationUri?: string;
  did?: string;
  operationId?: string;
  error?: string;
}
export interface ListOperationsInput {
  lineId?: string;
  status?: OperationStatus;
  limit?: number;
  cursor?: string;
}
export interface ListOperationsOutput {
  items: OperationView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  lineCount?: number;
  timetableCount?: number;
  fareCount?: number;
  operationCount?: number;
  faresBySeatClass?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUintString(s: string): boolean {
  return /^\d+$/.test(s);
}
export function isHHMM(s: string): boolean {
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(s);
}
export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}

export function lineDidFor(id: string): string {
  return `${SHINKANSEN_DID_PREFIX}line:${id.toLowerCase()}`;
}
export function lineRkey(id: string): string {
  return `line-${id.toLowerCase()}`;
}
export function timetableDidFor(id: string): string {
  return `${SHINKANSEN_DID_PREFIX}tt:${id.toLowerCase()}`;
}
export function timetableRkey(id: string): string {
  return `tt-${id.toLowerCase()}`;
}
export function fareDidFor(id: string): string {
  return `${SHINKANSEN_DID_PREFIX}fare:${id.toLowerCase()}`;
}
export function fareRkey(id: string): string {
  return `fare-${id.toLowerCase()}`;
}
export function operationDidFor(id: string): string {
  return `${SHINKANSEN_DID_PREFIX}op:${id.toLowerCase()}`;
}
export function operationRkey(id: string): string {
  return `op-${id.toLowerCase()}`;
}
