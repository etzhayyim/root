/**
 * Mirrors the com.etzhayyim.apps.openUnispsc.segmentDef Lexicon record shape.
 * Source: 00-contracts/lexicons/com/etzhayyim/apps/openUnispsc/segmentDef.json
 */
export interface SegmentDef {
  /** UNSPSC 2-digit segment code (e.g. "10", "43"). */
  code: string;

  /** URL-safe slug (lowercase letters / digits / hyphens). */
  slug: string;

  /** Canonical English name. */
  name: string;

  /** Optional free-text description; absent in v1 (segments.csv has only code/slug/name). */
  description?: string;

  /**
   * Optional primary CPC concordance section. Populated only when the
   * segment-range → CPC-section mapping from the open-unispsc CLAUDE.md
   * is applied (see `cpcSectionFor()` below).
   */
  cpcSection?: string;

  /** ISO datetime when this segment entry was published. */
  publishedAt: string;
}

/** Default publishedAt — UNSPSC v25 baseline. Override via seed env. */
export const UNSPSC_PUBLISHED_AT_DEFAULT = "2023-08-15T00:00:00Z";

/** Lower-case alphanumeric + hyphen, 2–64 chars, no leading/trailing hyphens. */
const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$/;

/** UNSPSC segment code is exactly two ASCII digits. */
const CODE_RE = /^[0-9]{2}$/;

export function isValidCode(code: string): boolean {
  return CODE_RE.test(code);
}

export function isValidSlug(slug: string): boolean {
  return SLUG_RE.test(slug);
}

/**
 * Primary CPC concordance for a UNSPSC segment code, per the segment-range
 * mapping documented in `60-apps/etzhayyim-project-open-unispsc/CLAUDE.md`:
 *
 *   10–15  → "0–1"  (Agriculture, Ores)
 *   20–27  → "3–4"  (Transportable goods, Machinery)
 *   30–31  → "5"    (Construction)
 *   39–48  → "3–4"  (Goods, Machinery)
 *   50–53  → "2"    (Food, Textiles)
 *   55–60  → "8"    (Business services)
 *   70–86  → "6–9"  (Services)
 *   90–95  → "9"    (Community / public)
 *
 * Returns undefined for codes outside those ranges so the optional field
 * stays absent rather than mis-categorised.
 */
export function cpcSectionFor(code: string): string | undefined {
  if (!isValidCode(code)) return undefined;
  const n = Number(code);
  if (n >= 10 && n <= 15) return "0-1";
  if (n >= 20 && n <= 27) return "3-4";
  if (n >= 30 && n <= 31) return "5";
  if (n >= 39 && n <= 48) return "3-4";
  if (n >= 50 && n <= 53) return "2";
  if (n >= 55 && n <= 60) return "8";
  if (n >= 70 && n <= 86) return "6-9";
  if (n >= 90 && n <= 95) return "9";
  return undefined;
}
