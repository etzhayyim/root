/**
 * Mirrors the com.etzhayyim.apqc.processCategory Lexicon record shape.
 * Source: orgs/etzhayyim/com-etzhayyim-apqc/lex/processCategory.json
 */
export interface ProcessCategory {
  /** APQC PCF L1 identifier (e.g. "1.0", "7.0", "13.0"). */
  code: string;

  /** Canonical English name. */
  name: string;

  /** Hierarchy depth — always 1 for L1 records. Future lexicons hold 2..5. */
  level: 1 | 2 | 3 | 4 | 5;

  /** APQC PCF version, e.g. "7.4.0". */
  version: string;

  /** Optional free-text scope description. */
  description?: string;

  /** Optional cross-cutting themes — reserved for future enrichment. */
  themes?: string[];

  /** ISO datetime when this record was published. */
  publishedAt: string;
}

/** Default publishedAt — APQC PCF v7.4 baseline. */
export const APQC_PUBLISHED_AT_DEFAULT = "2023-11-01T00:00:00Z";

/** Current PCF version this Phase-1 seed targets. */
export const APQC_PCF_VERSION = "7.4.0";

/**
 * L1 code format: one or two digits followed by ".0" (the v7.4 cross-industry
 * framework numbers categories 1.0 through 13.0).
 *
 *   /^([1-9]|1[0-3])\.0$/
 *
 * Codes outside 1.0–13.0 are rejected even if syntactically well-formed —
 * v7.4 has exactly 13 L1 categories. If a future PCF revision extends the
 * count, bump the upper bound and update the seed in the same PR.
 */
const L1_CODE_RE = /^([1-9]|1[0-3])\.0$/;

export function isValidL1Code(code: string): boolean {
  return L1_CODE_RE.test(code);
}

/**
 * Pure helper: given an L1 code, return the numeric position (1–13).
 * Useful for sorted output. Returns NaN for invalid codes.
 */
export function l1Ordinal(code: string): number {
  if (!isValidL1Code(code)) return Number.NaN;
  return Number(code.slice(0, code.indexOf(".")));
}
