// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim. Licensed under Apache 2.0 — see LICENSE at repo root.
//
// open-otology-uhl-r — XRPC AppView for the uhl-right-neural Pregel langserver.
//
// Single XRPC method:
//   jp.etzhayyim.med.uhl.institution.matchQuery (query)
//     in:  { substrateClass, localeCountry, dfnb9Confirmed?, topN? }
//     out: { substrateClass, candidates[], requiresHumanReview: true,
//            ethicsCommitteeRequired: true, dataExportRequiresReview: true }
//
// Wraps the langserver at lg-uhl-right-neural.mitama-udf.svc:8080.
// Lexicon contract: 00-contracts/lexicons/jp/etzhayyim/med/uhl/institution/matchQuery.json
//
// P0 MVP: this Worker only exposes the matchQuery surface. P1 will add the
// auditable at:// record emission for every match request (no PII, per
// ADR-2605181040 §PII zero).

import {
  createWorkerExport,
  nsid,
  parseLexiconInput,
  type LexiconOutput,
} from "@gftd/magatama-host-sdk";

const LANGSERVER_URL =
  "http://lg-uhl-right-neural.mitama-udf.svc:8080/threads/runs";

const NSID_MATCH = "jp.etzhayyim.med.uhl.institution.matchQuery" as const;

// Substrate class is the unit that branches the Pregel; we validate the
// caller-supplied value against the Lexicon's knownValues list before
// proxying so a bad input never reaches the langserver.
const KNOWN_SUBSTRATE_CLASSES = new Set([
  "sgn_present_hc_loss",
  "sgn_degenerating_nerve_present",
  "sgn_absent_nerve_present",
  "nerve_aplasia",
  "indeterminate",
]);

interface MatchInput {
  substrateClass: string;
  localeCountry: string;
  dfnb9Confirmed?: boolean;
  topN?: number;
}

interface LangServerCandidate {
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

interface LangServerMatchResult {
  substrate_class: string;
  candidates: LangServerCandidate[];
  requires_human_review: true;
  burden_summary_url: string;
  ethics_committee_required: true;
  data_export_requires_review: true;
}

// Minimal LangGraph CLI request shape — pulls the V16 output directly.
async function callLangServer(input: MatchInput): Promise<LangServerMatchResult> {
  // We invoke the uhl_pregel graph with only the V16-relevant fields so the
  // langserver short-circuits the upstream V01-V15 path. Callers that need
  // the full Pregel run use a separate (future) XRPC method.
  const payload = {
    assistant_id: "uhl_pregel",
    input: {
      phenotype: { locale_country: input.localeCountry },
      substrate_decision: { substrate_class: input.substrateClass },
      substrate_evidence: {
        biallelic_otof_pathogenic: input.dfnb9Confirmed ?? false,
      },
    },
  };

  const resp = await fetch(LANGSERVER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`langserver ${resp.status}: ${await resp.text()}`);
  }
  const result = (await resp.json()) as { institution_match?: LangServerMatchResult };
  if (!result.institution_match) {
    throw new Error("langserver: missing institution_match in output");
  }
  return result.institution_match;
}

function toLexiconOutput(
  result: LangServerMatchResult,
  topN: number,
): LexiconOutput<typeof NSID_MATCH> {
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
  } as LexiconOutput<typeof NSID_MATCH>;
}

export default createWorkerExport((sdk) => {
  sdk.app.query(nsid(NSID_MATCH), async (_ctx, body) => {
    const input = parseLexiconInput(NSID_MATCH, body) as unknown as MatchInput;

    if (!KNOWN_SUBSTRATE_CLASSES.has(input.substrateClass)) {
      throw new Error(
        `InvalidSubstrateClass: ${input.substrateClass} not in knownValues`,
      );
    }
    if (!/^[A-Z]{2}$/.test(input.localeCountry)) {
      throw new Error(
        `InvalidLocaleCountry: ${input.localeCountry} must be ISO 3166-1 alpha-2`,
      );
    }

    const topN = Math.max(1, Math.min(20, input.topN ?? 5));
    let result: LangServerMatchResult;
    try {
      result = await callLangServer(input);
    } catch (err) {
      throw new Error(
        `RegistryUnavailable: ${(err as Error).message ?? "unknown langserver error"}`,
      );
    }
    return JSON.stringify(toLexiconOutput(result, topN));
  });
});
