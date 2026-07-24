/**
 * XRPC Policy Evaluation Tests
 * Tests for Issue #1509 - dual-gate policy enforcement
 */

import { describe, it, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));

let evaluateDispatchPolicy;
let evaluateArmsPolicy;
let evaluateXrpcPolicies;
let loadPolicyRoutingMap;
let findPolicyRoutingEntry;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `xrpc-policy-${hash}.mjs`);
  await esbuild.build({
    entryPoints: [join(HERE, "../src/xrpc-policy.ts")],
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
    external: ["node:crypto"],
  });
  const mod = await import(`${out}?t=${Date.now()}`);
  evaluateDispatchPolicy = mod.evaluateDispatchPolicy;
  evaluateArmsPolicy = mod.evaluateArmsPolicy;
  evaluateXrpcPolicies = mod.evaluateXrpcPolicies;
  loadPolicyRoutingMap = mod.loadPolicyRoutingMap;
  findPolicyRoutingEntry = mod.findPolicyRoutingEntry;
});

// ─── Test Helpers ───────────────────────────────────────────────────────────

function makePolicyInput(overrides = {}) {
  return {
    route: { nsid: "com.etzhayyim.apps.arms.checkOutFirearm", requiresAuth: true },
    auth: { method: "did-session", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.checkOutFirearm"], holderAuthSessionPassed: true },
    permission_sets: ["arms:holder"],
    params: {},
    ...overrides,
  };
}

function makeArmsTransferInput(overrides = {}) {
  return {
    route: { nsid: "com.etzhayyim.apps.arms.transferCustody", requiresAuth: true },
    auth: { method: "did-session", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.transferCustody"], holderAuthSessionPassed: true },
    permission_sets: ["arms:authority"],
    params: { destinationJurisdiction: "JP" },
    ...overrides,
  };
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("Policy Routing Map", () => {
  it("arms NSIDs require both dispatch and arms policies", async () => {
    const routingMap = await loadPolicyRoutingMap();
    const entry = findPolicyRoutingEntry("com.etzhayyim.apps.arms.checkOutFirearm", routingMap);
    assert.deepEqual(entry.policies, ["dispatch", "arms"]);
  });

  it("transferCustody requires both dispatch and arms policies", async () => {
    const routingMap = await loadPolicyRoutingMap();
    const entry = findPolicyRoutingEntry("com.etzhayyim.apps.arms.transferCustody", routingMap);
    assert.deepEqual(entry.policies, ["dispatch", "arms"]);
  });

  it("kotoba NSIDs require only dispatch", async () => {
    const routingMap = await loadPolicyRoutingMap();
    const entry = findPolicyRoutingEntry("com.etzhayyim.apps.kotoba.query", routingMap);
    assert.deepEqual(entry.policies, ["dispatch"]);
  });

  it("app.bsky NSIDs require only dispatch", async () => {
    const routingMap = await loadPolicyRoutingMap();
    const entry = findPolicyRoutingEntry("app.bsky.feed.getTimeline", routingMap);
    assert.deepEqual(entry.policies, ["dispatch"]);
  });

  it("more specific prefixes win over generic ones", async () => {
    const routingMap = await loadPolicyRoutingMap();
    const entry1 = findPolicyRoutingEntry("com.etzhayyim.apps.arms.checkOutFirearm", routingMap);
    assert.deepEqual(entry1.policies, ["dispatch", "arms"]);
    const entry2 = findPolicyRoutingEntry("com.etzhayyim.apps.arms.otherMethod", routingMap);
    assert.deepEqual(entry2.policies, ["dispatch", "arms"]);
  });
});

describe("Dispatch Policy Evaluation", () => {
  it("allows internal service (service-jwt) regardless of scopes — arms policy enforces scopes", async () => {
    const input = makePolicyInput({
      auth: { method: "service-jwt", scopes: ["rpc/lxm=anything"] },
    });
    const decision = await evaluateDispatchPolicy(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "internal-service");
  });

  it("allows atproto endpoint with correct atproto scope", async () => {
    const input = {
      route: { nsid: "app.bsky.feed.getTimeline", requiresAuth: true },
      auth: { method: "oauth", scopes: ["rpc/lxm=com.atproto.repo.createRecord"] },
      permission_sets: [],
      params: {},
    };
    const decision = await evaluateDispatchPolicy(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "scope-or-permission-set");
  });

  it("denies public (unauthenticated) access to auth-required endpoint", async () => {
    const input = makePolicyInput({
      auth: { method: "public", scopes: [] },
    });
    const decision = await evaluateDispatchPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "authentication-required");
    assert.ok(decision.deny_obligations.includes("return_401"));
  });
});

describe("Arms Policy Evaluation", () => {
  it("allows checkOutFirearm with holder auth session", async () => {
    const input = makePolicyInput({
      route: { nsid: "com.etzhayyim.apps.arms.checkOutFirearm", requiresAuth: true },
    });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "holder-auth-session-required");
  });

  it("denies checkOutFirearm without holder auth session", async () => {
    const input = makePolicyInput({
      route: { nsid: "com.etzhayyim.apps.arms.checkOutFirearm", requiresAuth: true },
      auth: { method: "did-session", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.checkOutFirearm"], holderAuthSessionPassed: false },
    });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "holder-auth-session-required");
    assert.ok(decision.deny_obligations.includes("return_403"));
  });

  it("allows transferCustody with holder auth session and valid jurisdiction", async () => {
    const input = makeArmsTransferInput();
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, true);
  });

  it("denies transferCustody to restricted jurisdiction (KP)", async () => {
    const input = makeArmsTransferInput({ params: { destinationJurisdiction: "KP" } });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "export-control-blocked");
    assert.ok(decision.deny_obligations.includes("return_451"));
    assert.ok(decision.deny_obligations.includes("audit_export_control"));
  });

  it("denies transferCustody with omitted destinationJurisdiction", async () => {
    const input = makeArmsTransferInput({ params: {} });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "export-control-blocked");
    assert.ok(decision.deny_obligations.includes("return_451"));
  });

  it("allows internal service for transferCustody with correct scope", async () => {
    const input = makeArmsTransferInput({
      auth: { method: "service-jwt", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.transferCustody"] },
    });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "internal-service");
  });

  it("denies internal service for issuePermit with wrong scope", async () => {
    const input = {
      route: { nsid: "com.etzhayyim.apps.arms.issuePermit", requiresAuth: true },
      auth: { method: "service-jwt", scopes: ["rpc/lxm=wrong"] },
      permission_sets: ["arms:authority"],
      params: {},
    };
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "insufficient-scope");
  });

  it("allows public-read for authenticateHolder", async () => {
    const input = {
      route: { nsid: "com.etzhayyim.apps.arms.authenticateHolder", requiresAuth: false },
      auth: { method: "public", scopes: [] },
      permission_sets: [],
      params: {},
    };
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "public-read");
  });

  it("denies public access to auth-required arms endpoint", async () => {
    const input = makePolicyInput({
      auth: { method: "public", scopes: [] },
    });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "authentication-required");
  });
});

describe("Combined Policy Evaluation (dual-gate)", () => {
  it("allows arms endpoint when both dispatch and arms allow", async () => {
    const input = makePolicyInput();
    const decision = await evaluateXrpcPolicies(input);
    assert.equal(decision.allow, true);
    assert.ok(["holder-auth-session-required", "scope-allowed", "permission-set-allowed"].includes(decision.reason));
  });

  it("denies arms endpoint when arms policy denies (even if dispatch allows)", async () => {
    const input = makePolicyInput({
      auth: { method: "did-session", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.checkOutFirearm"], holderAuthSessionPassed: false },
    });
    const decision = await evaluateXrpcPolicies(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "holder-auth-session-required");
    assert.ok(decision.deny_obligations.includes("return_403"));
  });

  it("denies arms endpoint when dispatch policy denies (even if arms would allow)", async () => {
    const input = makePolicyInput({
      auth: { method: "public", scopes: [] },
    });
    const decision = await evaluateXrpcPolicies(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "authentication-required");
    assert.ok(decision.deny_obligations.includes("return_401"));
  });

  it("allows non-arms endpoint with only dispatch policy", async () => {
    const input = makePolicyInput({
      route: { nsid: "app.bsky.feed.getTimeline", requiresAuth: true },
      auth: { method: "oauth", scopes: ["rpc/lxm=com.atproto.repo.createRecord"] },
    });
    const decision = await evaluateXrpcPolicies(input);
    assert.equal(decision.allow, true);
    assert.equal(decision.reason, "scope-or-permission-set");
  });

  it("denies non-arms endpoint when dispatch denies", async () => {
    const input = makePolicyInput({
      route: { nsid: "app.bsky.feed.getTimeline", requiresAuth: true },
      auth: { method: "public", scopes: [] },
    });
    const decision = await evaluateXrpcPolicies(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "authentication-required");
  });
});

describe("Export Control (Issue #1504)", () => {
  it("blocks transferCustody to restricted jurisdiction", async () => {
    const input = makeArmsTransferInput({ params: { destinationJurisdiction: "IR" } });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "export-control-blocked");
  });

  it("blocks transferCustody with omitted jurisdiction", async () => {
    const input = makeArmsTransferInput({ params: {} });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "export-control-blocked");
  });

  it("allows transferCustody to allowed jurisdiction", async () => {
    const input = makeArmsTransferInput({ params: { destinationJurisdiction: "JP" } });
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, true);
  });

  it("blocks reportIncident to restricted jurisdiction", async () => {
    const input = {
      route: { nsid: "com.etzhayyim.apps.arms.reportIncident", requiresAuth: true },
      auth: { method: "did-session", scopes: ["rpc/lxm=com.etzhayyim.apps.arms.reportIncident"], holderAuthSessionPassed: true },
      permission_sets: ["arms:authority"],
      params: { destinationJurisdiction: "KP" },
    };
    const decision = await evaluateArmsPolicy(input);
    assert.equal(decision.allow, false);
    assert.equal(decision.reason, "export-control-blocked");
  });
});

console.log("All tests loaded - run with: node --experimental-vm-modules --test scripts/xrpc-policy.test.mjs");