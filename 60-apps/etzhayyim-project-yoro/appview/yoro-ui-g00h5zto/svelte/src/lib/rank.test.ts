/**
 * Unit tests for rank.ts (P2 boundary).
 *
 * Invariants under test:
 *   1. PII `ζ>=0.5` is a hard drop (never softened).
 *   2. Cohort k<50 forces PPR=0 and Bayes-shrinkage.
 *   3. Night mode boosts serenity-weighted Joucho alignment.
 *   4. Datacenter ASN halves personalization (bot suppression).
 *   5. shannonRerank prefers diverse topic/author/emotion buckets.
 */
import { describe, expect, it } from "vitest";
import {
  applyHardGate,
  deriveGuardrails,
  scoreCandidate,
  shannonRerank,
  DEFAULT_WEIGHTS,
  type PosteriorLookup,
  type PprLookup,
  type RankCandidate,
  type ViewerContext,
  _internal,
} from "../../../src/appview/rank";

const basePrior = {
  country: "JP", timezone: "Asia/Tokyo", asnType: "residential" as const,
  locale: "ja-JP", deviceClass: "mobile" as const, coarseRegion: null,
  localHour: 14,
};

function makeViewer(overrides: Partial<ViewerContext> = {}): ViewerContext {
  return {
    did: "did:web:alice.etzhayyim.com",
    cohortSize: 100,
    consentIndividualScope: false,
    jouchoState: null,
    optInRanking: true,
    intent: basePrior,
    ...overrides,
  };
}

function makeCandidate(overrides: Partial<RankCandidate> = {}): RankCandidate {
  return {
    uri: "at://did:web:author.etzhayyim.com/app.bsky.feed.post/3xyz",
    repo: "did:web:author.etzhayyim.com",
    createdAt: "2026-04-17T00:00:00Z",
    topic: null, emotion: null,
    signalEncrypted: false, audienceDid: null,
    ...overrides,
  };
}

const unitPosterior: PosteriorLookup = () => 0.5;
const zeroPpr: PprLookup = () => 0;

describe("PII hard gate (ζ invariant)", () => {
  it("drops signal-encrypted posts not addressed to the viewer", () => {
    const viewer = makeViewer();
    const c = makeCandidate({ signalEncrypted: true, audienceDid: "did:web:bob.etzhayyim.com" });
    const score = scoreCandidate(c, viewer, unitPosterior, zeroPpr, deriveGuardrails(viewer));
    expect(score.piiLeakRisk).toBe(1.0);
    const gated = applyHardGate([score]);
    expect(gated).toHaveLength(0);
  });
  it("allows signal-encrypted posts addressed to the viewer", () => {
    const viewer = makeViewer();
    const c = makeCandidate({ signalEncrypted: true, audienceDid: viewer.did });
    const score = scoreCandidate(c, viewer, unitPosterior, zeroPpr, deriveGuardrails(viewer));
    expect(score.piiLeakRisk).toBe(0);
    expect(applyHardGate([score])).toHaveLength(1);
  });
  it("lets plaintext posts through regardless of audience", () => {
    const viewer = makeViewer();
    const c = makeCandidate();
    const score = scoreCandidate(c, viewer, unitPosterior, zeroPpr, deriveGuardrails(viewer));
    expect(score.piiLeakRisk).toBe(0);
  });
});

describe("Cohort k<50 guardrail (ADR-0018 cohort-first)", () => {
  it("forces PPR=0 and shrinks Bayes when cohort is below the threshold", () => {
    const viewer = makeViewer({ cohortSize: 10 });
    const guard = deriveGuardrails(viewer);
    expect(guard.personalizeOff).toBe(true);
    const ppr: PprLookup = () => 1.0;  // would score high if allowed
    const c = makeCandidate();
    const score = scoreCandidate(c, viewer, unitPosterior, ppr, guard);
    expect(score.pageRank).toBe(0);
    // Bayes shrunk 0.5 -> 0.15
    expect(score.bayesInterest).toBeCloseTo(0.15, 5);
  });
  it("allows full personalization at cohort >= 50", () => {
    const viewer = makeViewer({ cohortSize: 50 });
    const guard = deriveGuardrails(viewer);
    expect(guard.personalizeOff).toBe(false);
    const ppr: PprLookup = () => 0.8;
    const score = scoreCandidate(makeCandidate(), viewer, unitPosterior, ppr, guard);
    expect(score.pageRank).toBe(0.8);
    expect(score.bayesInterest).toBe(0.5);
  });
});

describe("Night-mode Joucho alignment", () => {
  it("boosts serenity-weighted posts for stressed viewers", () => {
    const viewer = makeViewer({
      jouchoState: { vitality: 30, serenity: 30, connection: 30, growth: 30, resilience: 30, stressIdx: 85 },
    });
    const calmPost = makeCandidate({ emotion: { vitality: 20, serenity: 90, connection: 30, growth: 30, resilience: 30, stressIdx: 0 } });
    const hypePost = makeCandidate({ uri: "at://hype/1", emotion: { vitality: 95, serenity: 10, connection: 40, growth: 20, resilience: 20, stressIdx: 0 } });
    const guard = deriveGuardrails(viewer);
    const calmScore = scoreCandidate(calmPost, viewer, unitPosterior, zeroPpr, guard);
    const hypeScore = scoreCandidate(hypePost, viewer, unitPosterior, zeroPpr, guard);
    expect(calmScore.jouchoAlign).toBeGreaterThan(hypeScore.jouchoAlign);
  });
  it("night local-hour activates nightMode via intent.localHour", () => {
    const viewer = makeViewer({ intent: { ...basePrior, localHour: 2 } });
    expect(deriveGuardrails(viewer).nightMode).toBe(true);
  });
});

describe("Datacenter ASN bot suppression", () => {
  it("halves PPR and Bayes contributions when botSuspect is set", () => {
    const viewer = makeViewer({ intent: { ...basePrior, asnType: "datacenter" } });
    const vRes = makeViewer();  // residential control
    const ppr: PprLookup = () => 1.0;
    const guardBot = deriveGuardrails(viewer);
    const guardRes = deriveGuardrails(vRes);
    expect(guardBot.botSuspect).toBe(true);
    expect(guardRes.botSuspect).toBe(false);
    const botScore = scoreCandidate(makeCandidate(), viewer, unitPosterior, ppr, guardBot);
    const resScore = scoreCandidate(makeCandidate(), vRes, unitPosterior, ppr, guardRes);
    // α·bayes·0.5 + β·ppr·0.5 vs α·bayes + β·ppr
    expect(botScore.final).toBeLessThan(resScore.final);
  });
});

describe("shannonRerank entropy maximization", () => {
  it("prefers candidates that diversify topic and author buckets", () => {
    const mk = (uri: string, repo: string, topic: string | null, final: number) => ({
      score: {
        uri, repo,
        bayesInterest: 0, pageRank: 0, shannonNovelty: 0, tdaEchoPenalty: 0,
        jouchoAlign: 0, piiLeakRisk: 0, final,
      },
      candidate: makeCandidate({ uri, repo, topic }),
    });
    // Three posts by A about "cat" (scored 0.9, 0.8, 0.7) and one by B about "dog" (0.6).
    // A greedy top-k by `final` alone would pick the three A/cat posts; the
    // entropy-aware rerank should diversify by including B/dog earlier.
    const pool = [
      mk("a1", "did:A", "cat", 0.9),
      mk("a2", "did:A", "cat", 0.8),
      mk("a3", "did:A", "cat", 0.7),
      mk("b1", "did:B", "dog", 0.6),
    ];
    const top3 = shannonRerank(pool, 3);
    const selectedAuthors = new Set(top3.map((s) => s.repo));
    expect(selectedAuthors.has("did:B")).toBe(true);
  });
});

describe("emotion bucket dominant-axis classification", () => {
  it("picks the highest-scoring joucho axis", () => {
    expect(_internal.emotionBucket(null)).toBe("_");
    expect(_internal.emotionBucket({ vitality: 80, serenity: 10, connection: 20, growth: 30, resilience: 40, stressIdx: 0 })).toBe("vit");
    expect(_internal.emotionBucket({ vitality: 10, serenity: 90, connection: 20, growth: 30, resilience: 40, stressIdx: 0 })).toBe("ser");
  });
});

describe("DEFAULT_WEIGHTS sanity", () => {
  it("has the expected α,β,γ,δ,ε,ζ ordering", () => {
    expect(DEFAULT_WEIGHTS.alpha).toBeGreaterThan(0);
    expect(DEFAULT_WEIGHTS.zeta).toBeGreaterThanOrEqual(DEFAULT_WEIGHTS.delta);
  });
});

describe("P4 SessionTopology + doom-scroll guardrail", () => {
  it("adds echo penalty from sessionTopology.echoPersistence", () => {
    const viewer = makeViewer({
      sessionTopology: { echoPersistence: 0.7, dwellMs: 60_000, distinctTopics: 3 },
    });
    const guard = deriveGuardrails(viewer);
    expect(guard.doomScroll).toBe(false);
    const hot: PprLookup = () => 1.0;
    const score = scoreCandidate(makeCandidate({ topic: "tag:cat" }), viewer, unitPosterior, hot, guard);
    // echo = 0.7 -> δ·0.7 subtracted
    expect(score.tdaEchoPenalty).toBeCloseTo(0.7, 5);
    expect(score.final).toBeLessThan(DEFAULT_WEIGHTS.alpha * 0.5 + DEFAULT_WEIGHTS.beta * 1.0);
  });

  it("fires doom-scroll when dwell > 45min AND stress>70 (daytime)", () => {
    const viewer = makeViewer({
      jouchoState: { vitality: 20, serenity: 20, connection: 20, growth: 20, resilience: 20, stressIdx: 85 },
      sessionTopology: { echoPersistence: 0.5, dwellMs: 46 * 60 * 1000, distinctTopics: 4 },
    });
    const guard = deriveGuardrails(viewer);
    expect(guard.doomScroll).toBe(true);
  });

  it("tightens doom threshold to 20min at night regardless of stress", () => {
    const viewer = makeViewer({
      intent: { ...basePrior, localHour: 2 },
      sessionTopology: { echoPersistence: 0, dwellMs: 21 * 60 * 1000, distinctTopics: 10 },
    });
    const guard = deriveGuardrails(viewer);
    expect(guard.nightMode).toBe(true);
    expect(guard.doomScroll).toBe(true);
  });

  it("does NOT fire doom-scroll at 25min during the day with low stress", () => {
    const viewer = makeViewer({
      sessionTopology: { echoPersistence: 0, dwellMs: 25 * 60 * 1000, distinctTopics: 10 },
      jouchoState: { vitality: 60, serenity: 60, connection: 60, growth: 60, resilience: 60, stressIdx: 40 },
    });
    const guard = deriveGuardrails(viewer);
    expect(guard.doomScroll).toBe(false);
  });

  it("doom-scroll doubles the echo penalty weight on the final score", () => {
    const calm = makeViewer({
      sessionTopology: { echoPersistence: 0.5, dwellMs: 10 * 60 * 1000, distinctTopics: 5 },
      jouchoState: { vitality: 50, serenity: 50, connection: 50, growth: 50, resilience: 50, stressIdx: 30 },
    });
    const doom = makeViewer({
      sessionTopology: { echoPersistence: 0.5, dwellMs: 60 * 60 * 1000, distinctTopics: 5 },
      jouchoState: { vitality: 20, serenity: 20, connection: 20, growth: 20, resilience: 20, stressIdx: 90 },
    });
    const ppr: PprLookup = () => 0;
    const calmScore = scoreCandidate(makeCandidate(), calm, unitPosterior, ppr, deriveGuardrails(calm));
    const doomScore = scoreCandidate(makeCandidate(), doom, unitPosterior, ppr, deriveGuardrails(doom));
    // Both have same bayes & align contribution; doom double-weights δ so final is lower.
    expect(doomScore.final).toBeLessThan(calmScore.final);
  });
});
