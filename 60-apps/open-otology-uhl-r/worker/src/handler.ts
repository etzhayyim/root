/**
 * Pure XRPC handler logic for open-otology-uhl-r.
 *
 * Extracted from app.ts so the unit tests can exercise it without
 * pulling in @etzhayyim/magatama-host-sdk (which the workspace resolves
 * via `etzhayyim deploy` at deploy time, not via vitest).
 *
 * The default-export Worker in app.ts plugs `handleMatchQuery` into
 * `sdk.app.query(nsid(...), ...)`.
 */

export const LANGSERVER_URL =
  "http://lg-uhl-right-neural.mitama-udf.svc:8080/threads/runs";

export const NSID_MATCH =
  "jp.etzhayyim.med.uhl.institution.matchQuery" as const;
export const NSID_AUDIT =
  "jp.etzhayyim.med.uhl.institution.matchAudit" as const;

// Substrate class is the unit that branches the Pregel; we validate the
// caller-supplied value against the Lexicon's knownValues list before
// proxying so a bad input never reaches the langserver.
export const KNOWN_SUBSTRATE_CLASSES = new Set([
  "sgn_present_hc_loss",
  "sgn_degenerating_nerve_present",
  "sgn_absent_nerve_present",
  "nerve_aplasia",
  "indeterminate",
]);

export interface MatchInput {
  substrateClass: string;
  localeCountry: string;
  dfnb9Confirmed?: boolean;
  topN?: number;
}

export interface LangServerCandidate {
  institution_id: string;
  name_ja: string;
  name_en: string;
  country: string;
  matched_capabilities: string[];
  score: number;
  score_breakdown: Record<string, number>;
  referral_path_ids: string[];
  is_stale: boolean;
  notes: string[];
}

export interface LangServerMatchResult {
  substrate_class: string;
  candidates: LangServerCandidate[];
  requires_human_review: true;
  burden_summary_url: string;
  ethics_committee_required: true;
  data_export_requires_review: true;
}

export interface MatchOutputCandidate {
  institutionId: string;
  nameJa: string;
  nameEn: string;
  country: string;
  matchedCapabilities: string[];
  score: number;
  scoreBreakdown: Record<string, number>;
  referralPathIds: string[];
  isStale: boolean;
  notes: string[];
}

export interface MatchOutput {
  substrateClass: string;
  candidates: MatchOutputCandidate[];
  requiresHumanReview: true;
  burdenSummaryUrl: string;
  ethicsCommitteeRequired: true;
  dataExportRequiresReview: true;
}

export class InvalidInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidInputError";
  }
}

export class RegistryUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RegistryUnavailableError";
  }
}

/**
 * Validate an XRPC input against the Lexicon. Throws InvalidInputError on
 * a bad substrateClass / localeCountry. Returns the same shape with topN
 * clamped to [1, 20].
 */
export function validateMatchInput(input: MatchInput): MatchInput {
  if (!KNOWN_SUBSTRATE_CLASSES.has(input.substrateClass)) {
    throw new InvalidInputError(
      `InvalidSubstrateClass: ${input.substrateClass} not in knownValues`,
    );
  }
  if (!/^[A-Z]{2}$/.test(input.localeCountry)) {
    throw new InvalidInputError(
      `InvalidLocaleCountry: ${input.localeCountry} must be ISO 3166-1 alpha-2`,
    );
  }
  return {
    ...input,
    topN: Math.max(1, Math.min(20, input.topN ?? 5)),
  };
}

/**
 * Build the LangGraph CLI POST body. Extracted for testability — the
 * payload shape is part of the contract between the AppView and the
 * langserver Pod.
 */
export function buildLangServerPayload(input: MatchInput): unknown {
  return {
    assistant_id: "uhl_pregel",
    input: {
      phenotype: { locale_country: input.localeCountry },
      substrate_decision: { substrate_class: input.substrateClass },
      substrate_evidence: {
        biallelic_otof_pathogenic: input.dfnb9Confirmed ?? false,
      },
    },
  };
}

// Minimal LangGraph CLI request shape — pulls the V16 output directly.
export async function callLangServer(
  input: MatchInput,
  fetchImpl: typeof fetch = fetch,
  langServerUrl: string = LANGSERVER_URL,
): Promise<LangServerMatchResult> {
  const resp = await fetchImpl(langServerUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildLangServerPayload(input)),
  });
  if (!resp.ok) {
    throw new RegistryUnavailableError(
      `langserver ${resp.status}: ${await resp.text()}`,
    );
  }
  const result = (await resp.json()) as {
    institution_match?: LangServerMatchResult;
  };
  if (!result.institution_match) {
    throw new RegistryUnavailableError(
      "langserver: missing institution_match in output",
    );
  }
  return result.institution_match;
}

export function toLexiconOutput(
  result: LangServerMatchResult,
  topN: number,
): MatchOutput {
  // snake_case → camelCase + topN trim.
  return {
    substrateClass: result.substrate_class,
    candidates: result.candidates.slice(0, topN).map((c) => ({
      institutionId: c.institution_id,
      nameJa: c.name_ja,
      nameEn: c.name_en,
      country: c.country,
      matchedCapabilities: c.matched_capabilities,
      score: c.score,
      scoreBreakdown: c.score_breakdown,
      referralPathIds: c.referral_path_ids,
      isStale: c.is_stale,
      notes: c.notes,
    })),
    requiresHumanReview: true,
    burdenSummaryUrl: result.burden_summary_url,
    ethicsCommitteeRequired: true,
    dataExportRequiresReview: true,
  };
}

/**
 * End-to-end handler logic, decoupled from the XRPC framing. The
 * default-export Worker in app.ts plugs this into `sdk.app.query`.
 */
export async function handleMatchQuery(
  input: MatchInput,
  fetchImpl: typeof fetch = fetch,
  langServerUrl: string = LANGSERVER_URL,
): Promise<MatchOutput> {
  const validated = validateMatchInput(input);
  const result = await callLangServer(validated, fetchImpl, langServerUrl);
  return toLexiconOutput(result, validated.topN ?? 5);
}
