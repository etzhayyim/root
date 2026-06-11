/**
 * salesforce CRM domain tests (coverage loop iteration 8).
 *
 * The Salesforce-shaped CRM domain (524 LoC: leads / conversion / pipeline /
 * forecast) had zero tests. Its standout invariant is PRIVACY: leads reject
 * raw PII and require an `sha256:`-hashed email. Shared in-memory state with
 * no reset hook → all tests are ORDER-INDEPENDENT (own freshly-created leads,
 * delta-based pipeline assertions).
 */
import { describe, it, expect } from "vitest";
import {
  createLead,
  convertLead,
  advanceStage,
  listPipeline,
  getOverview,
  listLeads,
} from "../src/salesforce-domain.js";

const TENANT = "did:web:demo-opensaas.etzhayyim.com";
const OWNER = "did:web:demo-opensaas.etzhayyim.com:seat:ae-01";

function freshLead(overrides: Record<string, unknown> = {}) {
  return createLead({
    tenantDid: TENANT,
    ownerDid: OWNER,
    emailHash: "sha256:" + "a".repeat(64),
    source: "web",
    companyLabel: "Acme KK",
    displayLabel: "A. Buyer",
    ...overrides,
  } as never);
}

// ── createLead: the PII-hash privacy invariant ───────────────────────────────

describe("createLead PII invariant", () => {
  it("rejects a raw (non-sha256:) email hash", () => {
    expect(() => freshLead({ emailHash: "buyer@acme.example" })).toThrow(/raw PII is rejected/);
    expect(() => freshLead({ emailHash: "md5:abc" })).toThrow(/sha256:/);
  });

  it("requires tenantDid, emailHash and source", () => {
    expect(() => freshLead({ tenantDid: "" })).toThrow(/required/);
    expect(() => freshLead({ source: "" })).toThrow(/required/);
  });

  it("creates a 'new' lead with an at:// uri scoped to the tenant", () => {
    const lead = freshLead();
    expect(lead.status).toBe("new");
    expect(lead.uri).toContain("/com.etzhayyim.apps.opensaas.salesforce.lead/");
    expect(lead.uri.startsWith("at://demo-opensaas.etzhayyim.com/")).toBe(true);
    expect(listLeads().some((l) => l.uri === lead.uri)).toBe(true);
  });
});

// ── convertLead: account + contact + opportunity, idempotency guard ──────────

describe("convertLead", () => {
  it("creates account, contact, opportunity and marks the lead converted", () => {
    const lead = freshLead();
    const r = convertLead({
      leadUri: lead.uri,
      createOpportunity: true,
      opportunityAmountJpy: 5_000_000,
      opportunityStage: "qualification",
    });
    expect(r.account.name).toBe("Acme KK");                 // from companyLabel
    expect(r.contact.emailHash).toBe(lead.emailHash);       // hash carried, not re-derived
    expect(r.opportunity).toBeDefined();
    expect(r.opportunity!.probability).toBe(20);            // qualification
    expect(r.opportunity!.forecastCategory).toBe("pipeline");
    expect(r.opportunity!.amountBand).toBe("u10m");         // 5M < 10M
    expect(r.lead.status).toBe("converted");
    expect(r.lead.convertedOpportunityDid).toBe(r.opportunity!.uri);
    expect(r.activity.kind).toBe("conversion");
  });

  it("can convert without creating an opportunity", () => {
    const lead = freshLead();
    const r = convertLead({ leadUri: lead.uri, createOpportunity: false });
    expect(r.opportunity).toBeUndefined();
    expect(r.lead.status).toBe("converted");
  });

  it("refuses to convert an unknown or already-converted lead", () => {
    expect(() => convertLead({ leadUri: "at://ghost" })).toThrow(/LeadNotFound/);
    const lead = freshLead();
    convertLead({ leadUri: lead.uri, createOpportunity: false });
    expect(() => convertLead({ leadUri: lead.uri })).toThrow(/LeadAlreadyConverted/);
  });

  it("reuses an existing account when existingAccountDid is supplied", () => {
    const first = convertLead({ leadUri: freshLead().uri, createOpportunity: false });
    const second = convertLead({
      leadUri: freshLead().uri,
      existingAccountDid: first.account.uri,
      createOpportunity: false,
    });
    expect(second.account.uri).toBe(first.account.uri);
  });
});

// ── advanceStage: probability + forecast remap, activity trail ───────────────

describe("advanceStage", () => {
  it("remaps probability + forecastCategory and logs a stage-change activity", () => {
    const conv = convertLead({
      leadUri: freshLead().uri, opportunityStage: "qualification", opportunityAmountJpy: 1,
    });
    const { opportunity, activity } = advanceStage({
      opportunityUri: conv.opportunity!.uri, stage: "negotiation", actorDid: OWNER,
    });
    expect(opportunity.stage).toBe("negotiation");
    expect(opportunity.probability).toBe(80);
    expect(opportunity.forecastCategory).toBe("commit");
    expect(activity.kind).toBe("stage-change");
    expect(activity.subject).toContain("qualification → negotiation");
  });

  it("closed-won → 100% / closed; closed-lost → 0% / omitted", () => {
    const won = advanceStage({
      opportunityUri: convertLead({ leadUri: freshLead().uri, opportunityAmountJpy: 1 }).opportunity!.uri,
      stage: "closed-won",
    });
    expect([won.opportunity.probability, won.opportunity.forecastCategory]).toEqual([100, "closed"]);
    const lost = advanceStage({
      opportunityUri: convertLead({ leadUri: freshLead().uri, opportunityAmountJpy: 1 }).opportunity!.uri,
      stage: "closed-lost",
    });
    expect([lost.opportunity.probability, lost.opportunity.forecastCategory]).toEqual([0, "omitted"]);
  });

  it("throws on an unknown opportunity", () => {
    expect(() => advanceStage({ opportunityUri: "at://ghost", stage: "proposal" })).toThrow(/OpportunityNotFound/);
  });
});

// ── pipeline + overview: weighted-amount math, delta-based ───────────────────

describe("listPipeline / getOverview", () => {
  it("weighted pipeline = Σ round(amount × probability / 100), open stages only", () => {
    const beforeOpen = getOverview().openPipelineJpy;
    const beforeWeighted = getOverview().weightedPipelineJpy;
    convertLead({
      leadUri: freshLead().uri, opportunityStage: "proposal", opportunityAmountJpy: 1_000_000,
    });
    // proposal probability = 60 → weighted delta = 600,000; open delta = 1,000,000
    expect(getOverview().openPipelineJpy - beforeOpen).toBe(1_000_000);
    expect(getOverview().weightedPipelineJpy - beforeWeighted).toBe(600_000);
  });

  it("closed opportunities drop out of open pipeline", () => {
    const conv = convertLead({
      leadUri: freshLead().uri, opportunityStage: "proposal", opportunityAmountJpy: 2_000_000,
    });
    const open1 = getOverview().openPipelineJpy;
    advanceStage({ opportunityUri: conv.opportunity!.uri, stage: "closed-lost" });
    expect(getOverview().openPipelineJpy).toBe(open1 - 2_000_000);
  });

  it("listPipeline filters by stage and reports a per-stage rollup", () => {
    convertLead({
      leadUri: freshLead().uri, opportunityStage: "negotiation", opportunityAmountJpy: 3_000_000,
    });
    const page = listPipeline({ tenantDid: TENANT, stage: "negotiation", limit: 100 });
    expect(page.items.every((i) => i.stage === "negotiation")).toBe(true);
    const roll = page.stageRollup.find((r) => r.stage === "negotiation")!;
    expect(roll.count).toBe(page.total);
    // weighted = Σ round(amount × 80/100)
    expect(roll.weightedAmountJpy).toBe(
      page.items.reduce((s, i) => s + Math.round((i.amountJpy * 80) / 100), 0),
    );
  });

  it("respects offset/limit paging", () => {
    const all = listPipeline({ tenantDid: TENANT, limit: 1000 });
    const paged = listPipeline({ tenantDid: TENANT, limit: 2, offset: 1 });
    expect(paged.items.length).toBeLessThanOrEqual(2);
    expect(paged.total).toBe(all.total);
    expect(paged.offset).toBe(1);
  });
});
