/**
 * itonami rw-free — engine + assembly + procurement + test registries + coverage.
 * AT PDS records (no RW). Assembly / procurement / test FK-reference an existing
 * engine. Engineering simulation data; all values integerized.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ASSEMBLY_COLLECTION,
  CERT_STATUSES,
  ENGINE_COLLECTION,
  ENGINE_TYPES,
  OUTCOME_CODES,
  PHASE_CODES,
  PROCUREMENT_COLLECTION,
  TEST_COLLECTION,
  TEST_TYPES,
  assemblyDidFor,
  assemblyRkey,
  engineDidFor,
  engineRkey,
  isNonNegInt,
  isPermille,
  isPosInt,
  procurementDidFor,
  procurementRkey,
  testDidFor,
  testRkey,
  type AddProcurementInput,
  type AddProcurementOutput,
  type AssemblyRecord,
  type AssemblyView,
  type CoverageInput,
  type CoverageOutput,
  type DefineEngineInput,
  type DefineEngineOutput,
  type EngineRecord,
  type EngineView,
  type GetEngineInput,
  type GetEngineOutput,
  type ListAssembliesInput,
  type ListAssembliesOutput,
  type ListEnginesInput,
  type ListEnginesOutput,
  type ListProcurementInput,
  type ListProcurementOutput,
  type ListTestsInput,
  type ListTestsOutput,
  type ProcurementRecord,
  type ProcurementView,
  type RecordAssemblyInput,
  type RecordAssemblyOutput,
  type RecordTestInput,
  type RecordTestOutput,
  type SetCertificationInput,
  type SetCertificationOutput,
  type TestRecord,
  type TestView,
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

// ─── Engine ─────────────────────────────────────────────────────────

export async function defineEngine(e: Etzhayyim, input: DefineEngineInput): Promise<DefineEngineOutput> {
  if (!input.engineId || !input.designCode) return { status: "rejected", error: "missingRequiredFields" };
  if (!ENGINE_TYPES.has(input.engineType)) return { status: "rejected", error: "invalidEngineType" };
  if (!isPosInt(input.thrustRatingKn)) return { status: "rejected", error: "thrustRatingKnMustBePosInt" };
  if (!isPosInt(input.massKg)) return { status: "rejected", error: "massKgMustBePosInt" };
  const rkey = engineRkey(input.engineId);
  const existing = await e.read<EngineRecord>({ collection: ENGINE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", engineUri: existing.records[0].uri, did: existing.records[0].value.did, engineId: input.engineId };
  }
  const did = engineDidFor(input.engineId);
  const record: EngineRecord = {
    did,
    engineId: input.engineId,
    designCode: input.designCode,
    engineType: input.engineType,
    thrustRatingKn: input.thrustRatingKn,
    massKg: input.massKg,
    certificationStatus: "uncertified",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ENGINE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "defined", engineUri: receipt.uri, did, engineId: input.engineId };
}

export async function setCertification(e: Etzhayyim, input: SetCertificationInput): Promise<SetCertificationOutput> {
  if (!input.engineId || !CERT_STATUSES.has(input.certificationStatus)) return { status: "rejected", error: "invalidStatus" };
  const rkey = engineRkey(input.engineId);
  const resp = await e.read<EngineRecord>({ collection: ENGINE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const engine = resp.records[0]?.value;
  if (!engine) return { status: "notFound", error: "engineNotFound" };
  if (engine.certificationStatus === "retired") return { status: "rejected", error: "engineRetired" };
  await e.write({ collection: ENGINE_COLLECTION, record: { ...engine, certificationStatus: input.certificationStatus } as unknown as Record<string, unknown>, rkey });
  return { status: "updated", engineId: input.engineId, newStatus: input.certificationStatus };
}

export async function getEngine(e: Etzhayyim, input: GetEngineInput): Promise<GetEngineOutput> {
  if (!input.engineId) return { error: "invalidEngineId" };
  const resp = await e.read<EngineRecord>({ collection: ENGINE_COLLECTION, rkey: engineRkey(input.engineId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { engine: { ...r.value, engineUri: r.uri } };
}

export async function listEngines(e: Etzhayyim, input: ListEnginesInput = {}): Promise<ListEnginesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<EngineRecord>({ collection: ENGINE_COLLECTION, cursor: input.cursor, limit });
  const items: EngineView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.engineType && v.engineType !== input.engineType) return false;
      if (input.certificationStatus && v.certificationStatus !== input.certificationStatus) return false;
      return true;
    })
    .map((r) => ({ ...r.value, engineUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Assembly ───────────────────────────────────────────────────────

export async function recordAssembly(e: Etzhayyim, input: RecordAssemblyInput): Promise<RecordAssemblyOutput> {
  if (!input.assemblyId || !input.engineId) return { status: "rejected", error: "missingRequiredFields" };
  if (!PHASE_CODES.has(input.phaseCode)) return { status: "rejected", error: "invalidPhaseCode" };
  if (!isPermille(input.progressPermille)) return { status: "rejected", error: "progressPermilleMustBe0to1000" };
  if (!(await exists(e, ENGINE_COLLECTION, engineRkey(input.engineId)))) {
    return { status: "engineNotFound", error: `engineNotFound:${input.engineId}` };
  }
  const rkey = assemblyRkey(input.assemblyId);
  const existing = await e.read<AssemblyRecord>({ collection: ASSEMBLY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", assemblyUri: existing.records[0].uri, did: existing.records[0].value.did, assemblyId: input.assemblyId };
  }
  const did = assemblyDidFor(input.assemblyId);
  const record: AssemblyRecord = {
    did,
    assemblyId: input.assemblyId,
    engineId: input.engineId,
    phaseCode: input.phaseCode,
    progressPermille: input.progressPermille,
    notes: input.notes,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ASSEMBLY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", assemblyUri: receipt.uri, did, assemblyId: input.assemblyId };
}

export async function listAssemblies(e: Etzhayyim, input: ListAssembliesInput = {}): Promise<ListAssembliesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AssemblyRecord>({ collection: ASSEMBLY_COLLECTION, cursor: input.cursor, limit });
  const items: AssemblyView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.engineId && v.engineId !== input.engineId) return false;
      if (input.phaseCode && v.phaseCode !== input.phaseCode) return false;
      return true;
    })
    .map((r) => ({ ...r.value, assemblyUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Procurement ────────────────────────────────────────────────────

export async function addProcurement(e: Etzhayyim, input: AddProcurementInput): Promise<AddProcurementOutput> {
  if (!input.itemId || !input.engineId) return { status: "rejected", error: "missingRequiredFields" };
  if (!/^\d{8}$/.test(input.unspscCode)) return { status: "rejected", error: "invalidUnspscCode" };
  if (!/^\d{4}$/.test(input.supplierIsicCode)) return { status: "rejected", error: "invalidSupplierIsicCode" };
  if (!isPosInt(input.quantity)) return { status: "rejected", error: "quantityMustBePosInt" };
  if (!isNonNegInt(input.unitCostJpy)) return { status: "rejected", error: "unitCostJpyMustBeNonNegInt" };
  if (!(await exists(e, ENGINE_COLLECTION, engineRkey(input.engineId)))) {
    return { status: "engineNotFound", error: `engineNotFound:${input.engineId}` };
  }
  const rkey = procurementRkey(input.itemId);
  const existing = await e.read<ProcurementRecord>({ collection: PROCUREMENT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", procurementUri: existing.records[0].uri, did: existing.records[0].value.did, itemId: input.itemId };
  }
  const did = procurementDidFor(input.itemId);
  const record: ProcurementRecord = {
    did,
    itemId: input.itemId,
    engineId: input.engineId,
    unspscCode: input.unspscCode,
    supplierIsicCode: input.supplierIsicCode,
    quantity: input.quantity,
    unitCostJpy: input.unitCostJpy,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PROCUREMENT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", procurementUri: receipt.uri, did, itemId: input.itemId };
}

export async function listProcurement(e: Etzhayyim, input: ListProcurementInput = {}): Promise<ListProcurementOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ProcurementRecord>({ collection: PROCUREMENT_COLLECTION, cursor: input.cursor, limit });
  const items: ProcurementView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.engineId && v.engineId !== input.engineId) return false;
      if (input.unspscCode && v.unspscCode !== input.unspscCode) return false;
      if (input.supplierIsicCode && v.supplierIsicCode !== input.supplierIsicCode) return false;
      return true;
    })
    .map((r) => ({ ...r.value, procurementUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Test ───────────────────────────────────────────────────────────

export async function recordTest(e: Etzhayyim, input: RecordTestInput): Promise<RecordTestOutput> {
  if (!input.testId || !input.engineId) return { status: "rejected", error: "missingRequiredFields" };
  if (!TEST_TYPES.has(input.testType)) return { status: "rejected", error: "invalidTestType" };
  if (!OUTCOME_CODES.has(input.outcomeCode)) return { status: "rejected", error: "invalidOutcomeCode" };
  if (!isNonNegInt(input.thrustAchievedKn)) return { status: "rejected", error: "thrustAchievedKnMustBeNonNegInt" };
  if (!isNonNegInt(input.durationSeconds)) return { status: "rejected", error: "durationSecondsMustBeNonNegInt" };
  if (!(await exists(e, ENGINE_COLLECTION, engineRkey(input.engineId)))) {
    return { status: "engineNotFound", error: `engineNotFound:${input.engineId}` };
  }
  const rkey = testRkey(input.testId);
  const existing = await e.read<TestRecord>({ collection: TEST_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", testUri: existing.records[0].uri, did: existing.records[0].value.did, testId: input.testId };
  }
  const did = testDidFor(input.testId);
  const record: TestRecord = {
    did,
    testId: input.testId,
    engineId: input.engineId,
    testType: input.testType,
    outcomeCode: input.outcomeCode,
    thrustAchievedKn: input.thrustAchievedKn,
    durationSeconds: input.durationSeconds,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: TEST_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", testUri: receipt.uri, did, testId: input.testId };
}

export async function listTests(e: Etzhayyim, input: ListTestsInput = {}): Promise<ListTestsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TestRecord>({ collection: TEST_COLLECTION, cursor: input.cursor, limit });
  const items: TestView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.engineId && v.engineId !== input.engineId) return false;
      if (input.testType && v.testType !== input.testType) return false;
      if (input.outcomeCode && v.outcomeCode !== input.outcomeCode) return false;
      return true;
    })
    .map((r) => ({ ...r.value, testUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const enginesByCertStatus: Record<string, number> = {};
  const engineCount = await scanAll<EngineRecord>(e, ENGINE_COLLECTION, maxScan, (v) => {
    enginesByCertStatus[v.certificationStatus] = (enginesByCertStatus[v.certificationStatus] ?? 0) + 1;
  });
  const assemblyCount = await scanAll<AssemblyRecord>(e, ASSEMBLY_COLLECTION, maxScan, () => {});
  let totalProcurementJpy = 0;
  const procurementCount = await scanAll<ProcurementRecord>(e, PROCUREMENT_COLLECTION, maxScan, (v) => {
    totalProcurementJpy += v.unitCostJpy * v.quantity;
  });
  const testsByOutcome: Record<string, number> = {};
  const testCount = await scanAll<TestRecord>(e, TEST_COLLECTION, maxScan, (v) => {
    testsByOutcome[v.outcomeCode] = (testsByOutcome[v.outcomeCode] ?? 0) + 1;
  });
  return {
    engineCount,
    assemblyCount,
    procurementCount,
    testCount,
    enginesByCertStatus,
    testsByOutcome,
    totalProcurementJpy,
    truncated: engineCount >= maxScan || assemblyCount >= maxScan || procurementCount >= maxScan || testCount >= maxScan,
  };
}
