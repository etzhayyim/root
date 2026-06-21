/**
 * itonami kotoba — aircraft-engine lifecycle simulation record types.
 *
 * Per ADR-2606011400. itonami SIMULATES + records the engine lifecycle (design →
 * procurement → assembly → testing → digital-twin operation), integrating UNSPSC
 * (procurement commodity) + ISIC (supplier industry). Registry on AT PDS records
 * (replaces RW). ADR-2605172000 kotoba.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — engineering SIMULATION / digital-twin
 * data (not an OEM's actual airworthiness-certification authority), analogous to
 * bim/cad. No PII, no real settlement (simulated procurement costs), no actual
 * regulatory liability (simulated certification/test records).
 *
 * AT-Lexicon: no float — the domain is already integerized:
 *   thrustRatingKn / thrustAchievedKn = kN × 100   (e.g. 12100 = 121.00 kN)
 *   progressPermille = 0..1000                       (per-mille)
 *   massKg / unitCostJpy / quantity / durationSeconds — whole units
 *
 * Identity hierarchy:
 *   did:web:itonami.etzhayyim.com                          — controller
 *   did:web:itonami.etzhayyim.com:engine:{engineId}        — an engine design
 *   did:web:itonami.etzhayyim.com:assembly:{assemblyId}    — an assembly record
 *   did:web:itonami.etzhayyim.com:procure:{itemId}         — a procurement item
 *   did:web:itonami.etzhayyim.com:test:{testId}            — a test result
 */

export const ITONAMI_DID_PREFIX = "did:web:itonami.etzhayyim.com:" as const;

export const ENGINE_COLLECTION = "com.etzhayyim.apps.itonami.engine";
export const ASSEMBLY_COLLECTION = "com.etzhayyim.apps.itonami.assembly";
export const PROCUREMENT_COLLECTION = "com.etzhayyim.apps.itonami.procurement";
export const TEST_COLLECTION = "com.etzhayyim.apps.itonami.test";

// ─── Engine design ──────────────────────────────────────────────────

export type EngineType = "turbofan" | "turboprop" | "piston" | "electric";
export type CertificationStatus = "uncertified" | "in_progress" | "certified" | "retired";

export interface EngineRecord {
  did: string;
  engineId: string;
  designCode: string;
  engineType: EngineType;
  /** Rated thrust, kN × 100. */
  thrustRatingKn: number;
  massKg: number;
  certificationStatus: CertificationStatus;
  createdAt: string;
}
export interface EngineView extends EngineRecord {
  engineUri: string;
}
export interface DefineEngineInput {
  engineId: string;
  designCode: string;
  engineType: EngineType;
  thrustRatingKn: number;
  massKg: number;
}
export interface DefineEngineOutput {
  status: "defined" | "alreadyExists" | "rejected";
  engineUri?: string;
  did?: string;
  engineId?: string;
  error?: string;
}
export interface SetCertificationInput {
  engineId: string;
  certificationStatus: CertificationStatus;
}
export interface SetCertificationOutput {
  status: "updated" | "notFound" | "rejected";
  engineId?: string;
  newStatus?: CertificationStatus;
  error?: string;
}
export interface GetEngineInput {
  engineId: string;
}
export interface GetEngineOutput {
  engine?: EngineView;
  error?: string;
}
export interface ListEnginesInput {
  engineType?: EngineType;
  certificationStatus?: CertificationStatus;
  limit?: number;
  cursor?: string;
}
export interface ListEnginesOutput {
  items: EngineView[];
  cursor?: string;
  total: number;
}

// ─── Assembly record ────────────────────────────────────────────────

export type PhaseCode = "design" | "procurement" | "assembly" | "testing" | "certified" | "in_service" | "retired";

export interface AssemblyRecord {
  did: string;
  assemblyId: string;
  /** FK → engine engineId. */
  engineId: string;
  phaseCode: PhaseCode;
  /** Progress, per-mille (0..1000). */
  progressPermille: number;
  notes?: string;
  createdAt: string;
}
export interface AssemblyView extends AssemblyRecord {
  assemblyUri: string;
}
export interface RecordAssemblyInput {
  assemblyId: string;
  engineId: string;
  phaseCode: PhaseCode;
  progressPermille: number;
  notes?: string;
}
export interface RecordAssemblyOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "engineNotFound";
  assemblyUri?: string;
  did?: string;
  assemblyId?: string;
  error?: string;
}
export interface ListAssembliesInput {
  engineId?: string;
  phaseCode?: PhaseCode;
  limit?: number;
  cursor?: string;
}
export interface ListAssembliesOutput {
  items: AssemblyView[];
  cursor?: string;
  total: number;
}

// ─── Procurement item ───────────────────────────────────────────────

export interface ProcurementRecord {
  did: string;
  itemId: string;
  /** FK → engine engineId. */
  engineId: string;
  /** 8-digit UNSPSC commodity code. */
  unspscCode: string;
  /** 4-digit ISIC Rev.4 supplier industry class. */
  supplierIsicCode: string;
  quantity: number;
  /** Simulated unit cost, whole JPY. */
  unitCostJpy: number;
  createdAt: string;
}
export interface ProcurementView extends ProcurementRecord {
  procurementUri: string;
}
export interface AddProcurementInput {
  itemId: string;
  engineId: string;
  unspscCode: string;
  supplierIsicCode: string;
  quantity: number;
  unitCostJpy: number;
}
export interface AddProcurementOutput {
  status: "added" | "alreadyExists" | "rejected" | "engineNotFound";
  procurementUri?: string;
  did?: string;
  itemId?: string;
  error?: string;
}
export interface ListProcurementInput {
  engineId?: string;
  unspscCode?: string;
  supplierIsicCode?: string;
  limit?: number;
  cursor?: string;
}
export interface ListProcurementOutput {
  items: ProcurementView[];
  cursor?: string;
  total: number;
}

// ─── Test result ────────────────────────────────────────────────────

export type TestType = "bench" | "ground" | "flight";
export type OutcomeCode = "pass" | "fail" | "conditional";

export interface TestRecord {
  did: string;
  testId: string;
  /** FK → engine engineId. */
  engineId: string;
  testType: TestType;
  outcomeCode: OutcomeCode;
  /** Achieved thrust, kN × 100. */
  thrustAchievedKn: number;
  durationSeconds: number;
  createdAt: string;
}
export interface TestView extends TestRecord {
  testUri: string;
}
export interface RecordTestInput {
  testId: string;
  engineId: string;
  testType: TestType;
  outcomeCode: OutcomeCode;
  thrustAchievedKn: number;
  durationSeconds: number;
}
export interface RecordTestOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "engineNotFound";
  testUri?: string;
  did?: string;
  testId?: string;
  error?: string;
}
export interface ListTestsInput {
  engineId?: string;
  testType?: TestType;
  outcomeCode?: OutcomeCode;
  limit?: number;
  cursor?: string;
}
export interface ListTestsOutput {
  items: TestView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  engineCount?: number;
  assemblyCount?: number;
  procurementCount?: number;
  testCount?: number;
  enginesByCertStatus?: Record<string, number>;
  testsByOutcome?: Record<string, number>;
  totalProcurementJpy?: number;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const ENGINE_TYPES: ReadonlySet<string> = new Set(["turbofan", "turboprop", "piston", "electric"]);
export const CERT_STATUSES: ReadonlySet<string> = new Set(["uncertified", "in_progress", "certified", "retired"]);
export const PHASE_CODES: ReadonlySet<string> = new Set(["design", "procurement", "assembly", "testing", "certified", "in_service", "retired"]);
export const TEST_TYPES: ReadonlySet<string> = new Set(["bench", "ground", "flight"]);
export const OUTCOME_CODES: ReadonlySet<string> = new Set(["pass", "fail", "conditional"]);

export function isNonNegInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPosInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n > 0;
}
export function isPermille(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 1000;
}

export function engineDidFor(id: string): string {
  return `${ITONAMI_DID_PREFIX}engine:${id.toLowerCase()}`;
}
export function engineRkey(id: string): string {
  return `engine-${id.toLowerCase()}`;
}
export function assemblyDidFor(id: string): string {
  return `${ITONAMI_DID_PREFIX}assembly:${id.toLowerCase()}`;
}
export function assemblyRkey(id: string): string {
  return `assembly-${id.toLowerCase()}`;
}
export function procurementDidFor(id: string): string {
  return `${ITONAMI_DID_PREFIX}procure:${id.toLowerCase()}`;
}
export function procurementRkey(id: string): string {
  return `procure-${id.toLowerCase()}`;
}
export function testDidFor(id: string): string {
  return `${ITONAMI_DID_PREFIX}test:${id.toLowerCase()}`;
}
export function testRkey(id: string): string {
  return `test-${id.toLowerCase()}`;
}
