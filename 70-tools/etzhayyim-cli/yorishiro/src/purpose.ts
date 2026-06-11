// purpose.ts — Charter purpose validation (ADR-2605192115 §4 / ADR-2605211900 D2).
//
// External (substrate-crossing) yorishiro ops carry an x-charter-purpose array
// whose values are restricted to non-profit categories. Internal SBT↔SBT
// carveout values exist but are not the concern of yorishiro — the internal
// carveout flows stay as ordinary kotodama actors.

export const VALID_EXTERNAL_PURPOSES = [
  "donation",
  "kisha",
  "grant",
  "tithe",
  "escrow-refund",
] as const;

export type ExternalPurpose = (typeof VALID_EXTERNAL_PURPOSES)[number];

// Values that look like Charter purposes but are explicitly forbidden for
// any x-yorishiro-external: true lexicon. The lefthook hook
// no-external-purchase-purpose enforces the same denylist at pre-commit.
export const FORBIDDEN_EXTERNAL_PURPOSES = [
  "subscription",
  "purchase",
  "tip",
  // Internal-only values — illegal for external yorishiro lexicons. They
  // belong to SBT↔SBT carveout actors, not yorishiri.
  "internal-purchase",
  "internal-subscription",
  "internal-promo",
] as const;

export interface PurposeCheck {
  ok: boolean;
  invalid: string[];
  forbidden: string[];
}

export function validateExternalPurposes(purposes: readonly string[]): PurposeCheck {
  const invalid: string[] = [];
  const forbidden: string[] = [];
  for (const p of purposes) {
    if ((FORBIDDEN_EXTERNAL_PURPOSES as readonly string[]).includes(p)) {
      forbidden.push(p);
      continue;
    }
    if (!(VALID_EXTERNAL_PURPOSES as readonly string[]).includes(p)) {
      invalid.push(p);
    }
  }
  return { ok: invalid.length === 0 && forbidden.length === 0, invalid, forbidden };
}

export function parsePurposeCsv(csv: string): string[] {
  return csv
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}
