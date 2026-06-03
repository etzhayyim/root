/**
 * XRPC AppView unit tests for open-otology-uhl-r.
 *
 * Scope: the pure helpers in `handler.ts` (`validateMatchInput`,
 * `buildLangServerPayload`, `toLexiconOutput`, `callLangServer` with a
 * mock fetch, `handleMatchQuery` end-to-end with mock fetch).
 *
 * We don't spin up a real CF Worker — the `createWorkerExport` wrapper
 * in `app.ts` is exercised by `wrangler dev` / `etzhayyim deploy`. Here we
 * test the handler logic that lives behind it.
 */
import {describe, it, expect, vi} from "vitest";

import {
  InvalidInputError,
  KNOWN_SUBSTRATE_CLASSES,
  LANGSERVER_URL,
  RegistryUnavailableError,
  buildLangServerPayload,
  callLangServer,
  handleMatchQuery,
  toLexiconOutput,
  validateMatchInput,
  type LangServerMatchResult,
  type MatchInput,
} from "../src/handler.js";

// ── Fixtures ────────────────────────────────────────────────────────────────

const validInput: MatchInput = {
  substrateClass: "nerve_aplasia",
  localeCountry: "JP",
  dfnb9Confirmed: false,
  topN: 5,
};

const langServerResult: LangServerMatchResult = {
  substrate_class: "nerve_aplasia",
  candidates: Array.from({length: 8}).map((_, i) => ({
    institution_id: `jp-test-${i}`,
    name_ja: `テスト機関 ${i}`,
    name_en: `Test Inst ${i}`,
    country: "JP",
    matched_capabilities: ["ABI"],
    score: 1 - i * 0.05,
    score_breakdown: {capability_match: 1.0, locale_affinity: 1.0},
    referral_path_ids: ["abi-uk-nhs-paediatric"],
    is_stale: false,
    notes: [],
  })),
  requires_human_review: true,
  burden_summary_url: "https://etzhayyim.com/adr/2605181050",
  ethics_committee_required: true,
  data_export_requires_review: true,
};

function mockFetch(
  response: Partial<LangServerMatchResult> | null,
  init: {ok?: boolean; status?: number; text?: string} = {},
): typeof fetch {
  return vi.fn(async () => {
    return {
      ok: init.ok ?? true,
      status: init.status ?? 200,
      json: async () =>
        response === null ? {} : {institution_match: response},
      text: async () => init.text ?? "",
    } as Response;
  }) as unknown as typeof fetch;
}

// ── validateMatchInput ──────────────────────────────────────────────────────

describe("validateMatchInput", () => {
  it("accepts every Lexicon-declared substrateClass", () => {
    for (const sc of KNOWN_SUBSTRATE_CLASSES) {
      expect(() =>
        validateMatchInput({...validInput, substrateClass: sc}),
      ).not.toThrow();
    }
  });

  it("rejects an unknown substrateClass", () => {
    expect(() =>
      validateMatchInput({...validInput, substrateClass: "bogus"}),
    ).toThrowError(InvalidInputError);
  });

  it("rejects a non-ISO-3166-1-alpha-2 localeCountry", () => {
    expect(() =>
      validateMatchInput({...validInput, localeCountry: "Japan"}),
    ).toThrowError(InvalidInputError);
    expect(() =>
      validateMatchInput({...validInput, localeCountry: "jp"}),
    ).toThrowError(InvalidInputError);
  });

  it("defaults topN to 5 when omitted", () => {
    const out = validateMatchInput({
      substrateClass: "nerve_aplasia",
      localeCountry: "JP",
    });
    expect(out.topN).toBe(5);
  });

  it("clamps topN to [1, 20]", () => {
    expect(validateMatchInput({...validInput, topN: 0}).topN).toBe(1);
    expect(validateMatchInput({...validInput, topN: 999}).topN).toBe(20);
    expect(validateMatchInput({...validInput, topN: 8}).topN).toBe(8);
  });
});

// ── buildLangServerPayload ─────────────────────────────────────────────────

describe("buildLangServerPayload", () => {
  it("targets the uhl_pregel assistant and short-circuits to V06+V16", () => {
    const p = buildLangServerPayload(validInput) as {
      assistant_id: string;
      input: {
        phenotype: {locale_country: string};
        substrate_decision: {substrate_class: string};
        substrate_evidence: {biallelic_otof_pathogenic: boolean};
      };
    };
    expect(p.assistant_id).toBe("uhl_pregel");
    expect(p.input.phenotype.locale_country).toBe("JP");
    expect(p.input.substrate_decision.substrate_class).toBe("nerve_aplasia");
    expect(p.input.substrate_evidence.biallelic_otof_pathogenic).toBe(false);
  });

  it("propagates dfnb9Confirmed=true into the OTOF gate", () => {
    const p = buildLangServerPayload({
      ...validInput,
      dfnb9Confirmed: true,
    }) as {input: {substrate_evidence: {biallelic_otof_pathogenic: boolean}}};
    expect(p.input.substrate_evidence.biallelic_otof_pathogenic).toBe(true);
  });
});

// ── toLexiconOutput ────────────────────────────────────────────────────────

describe("toLexiconOutput", () => {
  it("converts snake_case to camelCase + trims to topN", () => {
    const out = toLexiconOutput(langServerResult, 3);
    expect(out.substrateClass).toBe("nerve_aplasia");
    expect(out.candidates).toHaveLength(3);
    expect(out.candidates[0].institutionId).toBe("jp-test-0");
    expect(out.candidates[0].nameJa).toBe("テスト機関 0");
    expect(out.candidates[0].scoreBreakdown).toEqual({
      capability_match: 1,
      locale_affinity: 1,
    });
    expect(out.candidates[0].referralPathIds).toEqual([
      "abi-uk-nhs-paediatric",
    ]);
  });

  it("constants always set per ADR-2605181040 §PII-zero / §human-review", () => {
    const out = toLexiconOutput(langServerResult, 5);
    expect(out.requiresHumanReview).toBe(true);
    expect(out.ethicsCommitteeRequired).toBe(true);
    expect(out.dataExportRequiresReview).toBe(true);
    expect(out.burdenSummaryUrl).toContain("2605181050");
  });
});

// ── callLangServer ─────────────────────────────────────────────────────────

describe("callLangServer", () => {
  it("posts to LANGSERVER_URL and parses institution_match", async () => {
    const fetchImpl = mockFetch(langServerResult);
    const out = await callLangServer(validInput, fetchImpl);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
    expect(fetchImpl).toHaveBeenCalledWith(
      LANGSERVER_URL,
      expect.objectContaining({method: "POST"}),
    );
    expect(out.substrate_class).toBe("nerve_aplasia");
    expect(out.candidates).toHaveLength(8);
  });

  it("uses a custom langServerUrl when given", async () => {
    const fetchImpl = mockFetch(langServerResult);
    await callLangServer(validInput, fetchImpl, "http://localhost:9999/x");
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://localhost:9999/x",
      expect.any(Object),
    );
  });

  it("throws RegistryUnavailableError on non-2xx response", async () => {
    const fetchImpl = mockFetch(null, {
      ok: false,
      status: 503,
      text: "Service Unavailable",
    });
    await expect(callLangServer(validInput, fetchImpl)).rejects.toThrowError(
      RegistryUnavailableError,
    );
  });

  it("throws RegistryUnavailableError when institution_match is missing", async () => {
    const fetchImpl = mockFetch(null);
    await expect(callLangServer(validInput, fetchImpl)).rejects.toThrowError(
      /missing institution_match/,
    );
  });
});

// ── handleMatchQuery — end-to-end ───────────────────────────────────────────

describe("handleMatchQuery", () => {
  it("round-trips a valid input → camelCase output", async () => {
    const fetchImpl = mockFetch(langServerResult);
    const out = await handleMatchQuery(
      {...validInput, topN: 4},
      fetchImpl,
      LANGSERVER_URL,
    );
    expect(out.candidates).toHaveLength(4);
    expect(out.candidates[0].institutionId).toBe("jp-test-0");
    expect(out.requiresHumanReview).toBe(true);
  });

  it("propagates InvalidInputError without hitting the langserver", async () => {
    const fetchImpl = vi.fn();
    await expect(
      handleMatchQuery(
        {...validInput, substrateClass: "bogus"},
        fetchImpl as unknown as typeof fetch,
      ),
    ).rejects.toThrowError(InvalidInputError);
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("propagates RegistryUnavailableError on langserver failure", async () => {
    const fetchImpl = mockFetch(null, {ok: false, status: 500});
    await expect(
      handleMatchQuery(validInput, fetchImpl),
    ).rejects.toThrowError(RegistryUnavailableError);
  });
});
