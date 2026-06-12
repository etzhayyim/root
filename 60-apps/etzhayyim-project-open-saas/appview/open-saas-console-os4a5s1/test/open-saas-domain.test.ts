/**
 * open-saas console domain tests (coverage loop iteration 7).
 *
 * The operator console's tenancy / billing / usage / audit logic (585 LoC)
 * had zero tests. The module holds a shared in-memory `state` with no reset
 * hook, so every test here is written ORDER-INDEPENDENT: reads are keyed on
 * the stable seed tenants, and mutations assert deltas (before/after) or the
 * returned object rather than absolute collection counts.
 */
import { describe, it, expect } from "vitest";
import {
  listPlans,
  getUsageSummary,
  getTenantSnapshot,
  getOverview,
  listAudit,
  createTenant,
  addWorkspace,
  addMembership,
  recordUsage,
  transitionSubscription,
} from "../src/open-saas-domain.js";

// ── pure reads against the fixed seed ────────────────────────────────────────

describe("listPlans", () => {
  it("exposes the three seed plans with their billing parameters", () => {
    const ids = listPlans().map((p) => p.planId);
    expect(ids).toEqual(["starter", "growth", "enterprise"]);
    const growth = listPlans().find((p) => p.planId === "growth")!;
    expect(growth.priceJpyMonthly).toBe(240000);
    expect(growth.includedUsageUnits).toBe(5000);
  });
});

describe("getUsageSummary", () => {
  it("sums usage by metric and computes pct against the plan's included units", () => {
    // tn_azuma (growth, included 5000): 2200 + 1200 + 24 = 3424 → 68%
    const s = getUsageSummary("tn_azuma");
    expect(s.totalUnits).toBe(3424);
    expect(s.usagePct).toBe(68);
    expect(s.usageByMetric["automation-runs"]).toBe(2200);
    expect(s.usageByMetric["api-calls"]).toBe(1200);
  });

  it("returns zero usage for an unknown tenant without throwing", () => {
    const s = getUsageSummary("tn_does_not_exist");
    expect(s.totalUnits).toBe(0);
    expect(s.usageByMetric).toEqual({});
  });
});

describe("getTenantSnapshot risk classification + seat summary", () => {
  it("churn-risk status forces riskLevel=action regardless of usage", () => {
    // tn_kitahoshi usage 718/1000 = 72% but status churn-risk → action
    const snap = getTenantSnapshot("tn_kitahoshi")!;
    expect(snap.tenant.status).toBe("churn-risk");
    expect(snap.riskLevel).toBe("action");
  });

  it("a stable active tenant under 70% usage is riskLevel=stable", () => {
    // tn_yoroi 13487/25000 = 54% → stable
    const snap = getTenantSnapshot("tn_yoroi")!;
    expect(snap.usageSummary.usagePct).toBeLessThan(70);
    expect(snap.riskLevel).toBe("stable");
  });

  it("seat summary aggregates membership count and workspace seat limits", () => {
    // tn_azuma: 3 memberships; seatLimit 18 + 8 = 26
    const snap = getTenantSnapshot("tn_azuma")!;
    expect(snap.seatSummary.assignedSeats).toBe(3);
    expect(snap.seatSummary.seatLimit).toBe(26);
  });

  it("returns null for an unknown tenant", () => {
    expect(getTenantSnapshot("nope")).toBeNull();
  });
});

// ── billing invariant: MRR moves by exactly the new plan price ───────────────

describe("getOverview MRR", () => {
  it("adding a self-serve tenant raises totalMrrJpy by exactly that plan's price", () => {
    const before = getOverview().totalMrrJpy;
    createTenant({ name: "Delta Co", ownerEmail: "o@delta.example", planId: "starter" });
    const after = getOverview().totalMrrJpy;
    expect(after - before).toBe(78000); // starter priceJpyMonthly
  });
});

// ── mutations: validation + audit trail (delta-based) ────────────────────────

describe("createTenant", () => {
  it("provisions tenant+workspace+owner+trial subscription and an audit event", () => {
    const auditBefore = listAudit(undefined, 1000).length;
    const snap = createTenant({
      name: "Hello World!!", ownerEmail: "OWNER@Example.com", planId: "growth",
    })!;
    expect(snap.tenant.slug).toBe("hello-world");           // slugify
    expect(snap.tenant.primaryOwnerEmail).toBe("owner@example.com"); // lowercased
    expect(snap.tenant.status).toBe("trial");
    expect(snap.workspaces).toHaveLength(1);
    expect(snap.memberships[0].role).toBe("owner");
    expect(snap.subscription?.status).toBe("trial");
    // seatLimit = max(plan.includedSeats=30, 5)
    expect(snap.workspaces[0].seatLimit).toBe(30);
    expect(listAudit(snap.tenant.tenantId).map((a) => a.action)).toContain("tenant.created");
    expect(listAudit(undefined, 1000).length).toBeGreaterThan(auditBefore);
  });

  it("rejects blank name, bad email, and unknown plan", () => {
    expect(() => createTenant({ name: "  ", ownerEmail: "a@b.c", planId: "growth" })).toThrow(/name/);
    expect(() => createTenant({ name: "X", ownerEmail: "no-at", planId: "growth" })).toThrow(/email/);
    expect(() => createTenant({ name: "X", ownerEmail: "a@b.c", planId: "ghost" })).toThrow(/plan/);
  });
});

describe("addWorkspace / addMembership", () => {
  it("adds a workspace then a membership into it, with validation", () => {
    const t = createTenant({ name: "Org A", ownerEmail: "a@orga.example", planId: "starter" })!;
    const tid = t.tenant.tenantId;

    const ws = addWorkspace(tid, {
      name: "Lab", region: "japan", environment: "staging", seatLimit: 4,
    });
    expect(ws.environment).toBe("staging");
    expect(() => addWorkspace(tid, { name: " ", region: "x", environment: "production", seatLimit: 1 }))
      .toThrow(/name/);
    expect(() => addWorkspace("ghost", { name: "Y", region: "x", environment: "production", seatLimit: 1 }))
      .toThrow(/tenant/);

    const m = addMembership(tid, { workspaceId: ws.workspaceId, email: "Dev@OrgA.example", role: "operator" });
    expect(m.email).toBe("dev@orga.example");
    expect(m.role).toBe("operator");
    expect(() => addMembership(tid, { workspaceId: ws.workspaceId, email: "bad", role: "member" }))
      .toThrow(/email/);
    expect(() => addMembership(tid, { workspaceId: "ghost", email: "a@b.c", role: "member" }))
      .toThrow(/workspace/);
  });
});

describe("recordUsage", () => {
  it("records usage that flows into the tenant's summary, and rejects non-positive quantity", () => {
    const t = createTenant({ name: "Usage Co", ownerEmail: "u@usage.example", planId: "starter" })!;
    const tid = t.tenant.tenantId;
    const ws = t.workspaces[0].workspaceId;

    const before = getUsageSummary(tid).totalUnits;
    recordUsage({ tenantId: tid, workspaceId: ws, metric: "api-calls", quantity: 150 });
    expect(getUsageSummary(tid).totalUnits).toBe(before + 150);

    for (const bad of [0, -5, NaN, Infinity]) {
      expect(() => recordUsage({ tenantId: tid, workspaceId: ws, metric: "api-calls", quantity: bad }))
        .toThrow(/quantity/);
    }
    expect(() => recordUsage({ tenantId: tid, workspaceId: "ghost", metric: "seats", quantity: 1 }))
      .toThrow(/workspace/);
  });
});

describe("transitionSubscription", () => {
  it("activates the subscription and flips the tenant to active, with audit", () => {
    const t = createTenant({ name: "Trial Co", ownerEmail: "t@trial.example", planId: "growth" })!;
    expect(t.tenant.status).toBe("trial");
    const subId = t.subscription!.subscriptionId;

    const updated = transitionSubscription({
      subscriptionId: subId, status: "active", actor: "ops", reason: "paid",
    });
    expect(updated.status).toBe("active");
    expect(getTenantSnapshot(t.tenant.tenantId)!.tenant.status).toBe("active");
    expect(listAudit(t.tenant.tenantId).map((a) => a.action)).toContain("subscription.transitioned");
  });

  it("throws on an unknown subscription id", () => {
    expect(() => transitionSubscription({
      subscriptionId: "ghost", status: "paused", actor: "ops", reason: "n/a",
    })).toThrow(/subscription not found/);
  });
});
