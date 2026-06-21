/**
 * shinkansen kotoba — line + timetable + fare + operation registries + coverage.
 * AT PDS records (no RW). Timetable & operation FK→line. Public rail reference
 * only; reservation/booking (Tier-3 PII + settlement) stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  FARE_COLLECTION,
  FARE_TYPES,
  LINE_COLLECTION,
  OPERATION_COLLECTION,
  OPERATION_STATUSES,
  PLATFORMS,
  SEAT_CLASSES,
  TIMETABLE_COLLECTION,
  fareDidFor,
  fareRkey,
  isHHMM,
  isUint,
  isUintString,
  lineDidFor,
  lineRkey,
  operationDidFor,
  operationRkey,
  timetableDidFor,
  timetableRkey,
  type AddFareInput,
  type AddFareOutput,
  type AddTimetableInput,
  type AddTimetableOutput,
  type CoverageInput,
  type CoverageOutput,
  type FareRecord,
  type FareView,
  type LineRecord,
  type LineView,
  type ListFaresInput,
  type ListFaresOutput,
  type ListLinesInput,
  type ListLinesOutput,
  type ListOperationsInput,
  type ListOperationsOutput,
  type ListTimetableInput,
  type ListTimetableOutput,
  type OperationRecord,
  type OperationView,
  type RecordOperationInput,
  type RecordOperationOutput,
  type RegisterLineInput,
  type RegisterLineOutput,
  type TimetableRecord,
  type TimetableView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Line ───────────────────────────────────────────────────────────

export async function registerLine(e: Etzhayyim, input: RegisterLineInput): Promise<RegisterLineOutput> {
  if (!input.lineId || !input.name || !input.operator) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = lineRkey(input.lineId);
  const existing = await e.read<LineRecord>({ collection: LINE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", lineUri: existing.records[0].uri, did: existing.records[0].value.did, lineId: input.lineId };
  }
  const did = lineDidFor(input.lineId);
  const record: LineRecord = {
    did,
    lineId: input.lineId,
    name: input.name,
    operator: input.operator,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: LINE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", lineUri: receipt.uri, did, lineId: input.lineId };
}

export async function listLines(e: Etzhayyim, input: ListLinesInput = {}): Promise<ListLinesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<LineRecord>({ collection: LINE_COLLECTION, cursor: input.cursor, limit });
  const items: LineView[] = resp.records
    .filter((r) => !input.operator || r.value.operator === input.operator)
    .map((r) => ({ ...r.value, lineUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Timetable ──────────────────────────────────────────────────────

export async function addTimetable(e: Etzhayyim, input: AddTimetableInput): Promise<AddTimetableOutput> {
  if (!input.entryId || !input.lineId || !input.trainNumber || !input.departureStation || !input.arrivalStation) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isHHMM(input.departTime) || !isHHMM(input.arriveTime)) return { status: "rejected", error: "timeMustBeHHMM" };
  if (!(await exists(e, LINE_COLLECTION, lineRkey(input.lineId)))) {
    return { status: "lineNotFound", error: `lineNotFound:${input.lineId}` };
  }
  const rkey = timetableRkey(input.entryId);
  const existing = await e.read<TimetableRecord>({ collection: TIMETABLE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", timetableUri: existing.records[0].uri, did: existing.records[0].value.did, entryId: input.entryId };
  }
  const did = timetableDidFor(input.entryId);
  const record: TimetableRecord = {
    did,
    entryId: input.entryId,
    lineId: input.lineId,
    trainNumber: input.trainNumber,
    trainType: input.trainType,
    departureStation: input.departureStation,
    arrivalStation: input.arrivalStation,
    departTime: input.departTime,
    arriveTime: input.arriveTime,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: TIMETABLE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", timetableUri: receipt.uri, did, entryId: input.entryId };
}

export async function listTimetable(e: Etzhayyim, input: ListTimetableInput = {}): Promise<ListTimetableOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TimetableRecord>({ collection: TIMETABLE_COLLECTION, cursor: input.cursor, limit });
  const items: TimetableView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.lineId && v.lineId !== input.lineId) return false;
      if (input.trainType && v.trainType !== input.trainType) return false;
      if (input.departureStation && v.departureStation !== input.departureStation) return false;
      if (input.arrivalStation && v.arrivalStation !== input.arrivalStation) return false;
      return true;
    })
    .map((r) => ({ ...r.value, timetableUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Fare ───────────────────────────────────────────────────────────

export async function addFare(e: Etzhayyim, input: AddFareInput): Promise<AddFareOutput> {
  if (!input.fareId || !input.fromStation || !input.toStation || !input.priceJpy) return { status: "rejected", error: "missingRequiredFields" };
  if (!FARE_TYPES.has(input.fareType)) return { status: "rejected", error: "invalidFareType" };
  if (!SEAT_CLASSES.has(input.seatClass)) return { status: "rejected", error: "invalidSeatClass" };
  if (!PLATFORMS.has(input.platform)) return { status: "rejected", error: "invalidPlatform" };
  if (!isUintString(input.priceJpy)) return { status: "rejected", error: "priceJpyMustBeUintString" };
  const rkey = fareRkey(input.fareId);
  const existing = await e.read<FareRecord>({ collection: FARE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", fareUri: existing.records[0].uri, did: existing.records[0].value.did, fareId: input.fareId };
  }
  const did = fareDidFor(input.fareId);
  const record: FareRecord = {
    did,
    fareId: input.fareId,
    fromStation: input.fromStation,
    toStation: input.toStation,
    fareType: input.fareType,
    seatClass: input.seatClass,
    priceJpy: input.priceJpy,
    discountName: input.discountName,
    validFrom: input.validFrom,
    validTo: input.validTo,
    platform: input.platform,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: FARE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", fareUri: receipt.uri, did, fareId: input.fareId };
}

export async function listFares(e: Etzhayyim, input: ListFaresInput = {}): Promise<ListFaresOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<FareRecord>({ collection: FARE_COLLECTION, cursor: input.cursor, limit });
  const items: FareView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.fromStation && v.fromStation !== input.fromStation) return false;
      if (input.toStation && v.toStation !== input.toStation) return false;
      if (input.seatClass && v.seatClass !== input.seatClass) return false;
      if (input.fareType && v.fareType !== input.fareType) return false;
      if (input.platform && v.platform !== input.platform) return false;
      return true;
    })
    .map((r) => ({ ...r.value, fareUri: r.uri }));
  const cheapest = items.reduce<FareView | undefined>((best, f) => {
    if (!best) return f;
    return BigInt(f.priceJpy) < BigInt(best.priceJpy) ? f : best;
  }, undefined);
  return { items, cheapest, cursor: resp.cursor, total: items.length };
}

// ─── Operation status ───────────────────────────────────────────────

export async function recordOperation(e: Etzhayyim, input: RecordOperationInput): Promise<RecordOperationOutput> {
  if (!input.operationId || !input.lineId || !input.observedAt) return { status: "rejected", error: "missingRequiredFields" };
  if (!OPERATION_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  if (input.delayMinutes != null && !isUint(input.delayMinutes)) return { status: "rejected", error: "delayMinutesMustBeUint" };
  if (!(await exists(e, LINE_COLLECTION, lineRkey(input.lineId)))) {
    return { status: "lineNotFound", error: `lineNotFound:${input.lineId}` };
  }
  const rkey = operationRkey(input.operationId);
  const existing = await e.read<OperationRecord>({ collection: OPERATION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", operationUri: existing.records[0].uri, did: existing.records[0].value.did, operationId: input.operationId };
  }
  const did = operationDidFor(input.operationId);
  const record: OperationRecord = {
    did,
    operationId: input.operationId,
    lineId: input.lineId,
    status: input.status,
    delayMinutes: input.delayMinutes,
    reason: input.reason,
    observedAt: input.observedAt,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: OPERATION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", operationUri: receipt.uri, did, operationId: input.operationId };
}

export async function listOperations(e: Etzhayyim, input: ListOperationsInput = {}): Promise<ListOperationsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<OperationRecord>({ collection: OPERATION_COLLECTION, cursor: input.cursor, limit });
  const items: OperationView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.lineId && v.lineId !== input.lineId) return false;
      if (input.status && v.status !== input.status) return false;
      return true;
    })
    .map((r) => ({ ...r.value, operationUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const faresBySeatClass: Record<string, number> = {};
  const lineCount = await scanAll<LineRecord>(e, LINE_COLLECTION, maxScan, () => {});
  const timetableCount = await scanAll<TimetableRecord>(e, TIMETABLE_COLLECTION, maxScan, () => {});
  const fareCount = await scanAll<FareRecord>(e, FARE_COLLECTION, maxScan, (v) => {
    faresBySeatClass[v.seatClass] = (faresBySeatClass[v.seatClass] ?? 0) + 1;
  });
  const operationCount = await scanAll<OperationRecord>(e, OPERATION_COLLECTION, maxScan, () => {});
  return {
    lineCount,
    timetableCount,
    fareCount,
    operationCount,
    faresBySeatClass,
    truncated: lineCount >= maxScan || timetableCount >= maxScan || fareCount >= maxScan || operationCount >= maxScan,
  };
}
