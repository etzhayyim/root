/**
 * open-cofog rw-free — record types + pure hierarchy helpers.
 *
 * Per ADR-2605203000 Option B. UN COFOG (Classification of the Functions of
 * Government) — a public 3-axis-clean taxonomy of government expenditure by
 * function. Registry on AT PDS records. ADR-2605172000 RW-free.
 *
 * COFOG is a strict numeric prefix hierarchy:
 *   Division 2 digits   01–10  (e.g. 07 = Health)
 *   Group    3 digits          (e.g. 073)
 *   Class    4 digits          (e.g. 0731)
 *
 * Identity hierarchy:
 *   did:web:open-cofog.etzhayyim.com                   — controller
 *   did:web:open-cofog.etzhayyim.com:entry:{code}      — a COFOG entry
 */

export const COFOG_DID_PREFIX = "did:web:open-cofog.etzhayyim.com:" as const;

export const ENTRY_COLLECTION = "com.etzhayyim.apps.openCofog.entry";

export type CofogLevel = "division" | "group" | "class";

export interface CofogEntry {
  did: string;
  /** COFOG code, 2–4 digits (canonical key). */
  code: string;
  titleEn: string;
  level: CofogLevel;
  /** 2-digit division (= code.slice(0, 2)). */
  division: string;
  /** Parent code (one digit shorter), or null for a division. */
  parent: string | null;
  description?: string;
  source?: string;
  publishedAt: string;
}

export interface CofogView extends CofogEntry {
  entryUri: string;
}

export interface RegisterEntryInput {
  code: string;
  titleEn: string;
  description?: string;
  source?: string;
  publishedAt?: string;
}

export interface RegisterEntryOutput {
  status: "registered" | "alreadyExists" | "rejected";
  entryUri?: string;
  did?: string;
  code?: string;
  error?: string;
}

export interface GetEntryInput {
  code: string;
}

export interface GetEntryOutput {
  entry?: CofogView;
  error?: string;
}

export interface ListEntriesInput {
  level?: CofogLevel;
  division?: string;
  limit?: number;
  cursor?: string;
}

export interface ListEntriesOutput {
  items: CofogView[];
  cursor?: string;
  total: number;
}

export interface CoverageInput {
  maxScan?: number;
}

export interface CoverageOutput {
  total?: number;
  byLevel?: Record<string, number>;
  byDivision?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + hierarchy helpers ─────────────────────────────────

const LEVELS: CofogLevel[] = ["division", "group", "class"];

/** Valid COFOG code: 2–4 digits whose 2-digit division is 01–10. */
export function isValidCofogCode(code: string): boolean {
  if (!/^\d{2,4}$/.test(code)) return false;
  const div = Number(code.slice(0, 2));
  return div >= 1 && div <= 10;
}

export function cofogLevel(code: string): CofogLevel {
  if (!isValidCofogCode(code)) throw new Error(`invalid COFOG code: ${code}`);
  return LEVELS[code.length - 2];
}

export function parentOf(code: string): string | null {
  if (!isValidCofogCode(code)) throw new Error(`invalid COFOG code: ${code}`);
  return code.length <= 2 ? null : code.slice(0, code.length - 1);
}

export function ancestorsOf(code: string): string[] {
  if (!isValidCofogCode(code)) throw new Error(`invalid COFOG code: ${code}`);
  const out: string[] = [];
  for (let len = 2; len < code.length; len++) out.push(code.slice(0, len));
  return out;
}

export function entryDid(code: string): string {
  return `${COFOG_DID_PREFIX}entry:${code}`;
}

export function entryRkey(code: string): string {
  return `entry-${code}`;
}
