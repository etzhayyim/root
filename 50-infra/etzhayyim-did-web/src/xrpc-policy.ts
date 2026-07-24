/**
 * XRPC Policy Evaluator
 *
 * Evaluates XRPC requests against OPA policies defined in 00-contracts/policies/.
 * Implements the dual-gate structure:
 *   - dispatch: outer routing-level gate (requiresAuth, scopes, permissions)
 *   - arms:   inner detail gate for arms NSIDs (requiresHolderAuthSession, export control)
 *
 * Policies are loaded from JSON data files and evaluated in TypeScript for
 * Cloudflare Workers compatibility (no WASM OPA dependency needed).
 *
 * The policy logic mirrors the Rego policies in:
 *   - 00-contracts/policies/etzhayyim/xrpc/dispatch/policy.rego
 *   - 00-contracts/policies/etzhayyim/xrpc/arms/policy.rego
 *
 * @module xrpc-policy
 */

// ─── Types ──────────────────────────────────────────────────────────────────

export interface AuthContext {
  method: "public" | "oauth" | "did-session" | "service-jwt" | string;
  scopes: string[];
  holderAuthSessionPassed?: boolean;
}

export interface PolicyInput {
  route: {
    nsid: string;
    requiresAuth?: boolean;
  };
  auth: AuthContext;
  permission_sets: string[];
  params: Record<string, unknown>;
  /** If true, dispatch policy will skip scope check (for NSIDs with detail policies like arms) */
  skipDispatchScopeCheck?: boolean;
}

export interface PolicyDecision {
  allow: boolean;
  reason: string;
  deny_obligations: string[];
}

// Dispatch policy data (from 00-contracts/policies/etzhayyim/xrpc/dispatch/data.json)
interface DispatchMethodPolicy {
  publicRead: boolean;
  allowedScopes: string[];
  allowedPermissionSets: string[];
}

interface DispatchData {
  method_policy: DispatchMethodPolicy;
}

// Arms policy data (from 00-contracts/policies/etzhayyim/xrpc/arms/data.json)
interface ArmsMethodPolicy {
  requiresAuth: boolean;
  allowedScopes: string[];
  allowedPermissionSets: string[];
  publicRead: boolean;
  requiresHolderAuthSession?: boolean;
}

interface ArmsData {
  method_policy: Record<string, ArmsMethodPolicy>;
  export_restricted_jurisdictions: string[];
}

// ─── Glob Match Utility ─────────────────────────────────────────────────────

/**
 * Simple glob matching for scope patterns like "rpc[?]lxm=com.etzhayyim.apps.arms.*"
 * The Rego glob.match uses [?] as single-char wildcard and * as multi-char.
 * We convert to regex for JS matching.
 */
function globMatch(pattern: string, input: string): boolean {
  // First, replace glob special patterns with placeholders to protect them from escaping
  let regexPattern = pattern
    .replace(/\[\?\]/g, "\x01")  // [?] -> placeholder (SOH char)
    .replace(/\*/g, "\x02")       // * -> placeholder (STX char)
    .replace(/[.+^${}()|[\]\\]/g, "\\$&"); // escape regex special chars

  // Now replace placeholders with actual regex
  regexPattern = regexPattern
    .replace(/\x01/g, ".")        // [?] -> any single char
    .replace(/\x02/g, ".*");      // * -> any chars

  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(input);
}

// ─── Policy Data Loaders ────────────────────────────────────────────────────

let dispatchDataCache: DispatchData | null = null;
let armsDataCache: ArmsData | null = null;

async function loadDispatchData(): Promise<DispatchData> {
  if (dispatchDataCache) return dispatchDataCache;
  const resp = await fetch(
    "https://raw.githubusercontent.com/etzhayyim/root/main/00-contracts/policies/etzhayyim/xrpc/dispatch/data.json",
  );
  if (!resp.ok) {
    throw new Error(`Failed to load dispatch policy data: ${resp.status}`);
  }
  dispatchDataCache = (await resp.json()) as DispatchData;
  return dispatchDataCache;
}

async function loadArmsData(): Promise<ArmsData> {
  if (armsDataCache) return armsDataCache;
  const resp = await fetch(
    "https://raw.githubusercontent.com/etzhayyim/root/main/00-contracts/policies/etzhayyim/xrpc/arms/data.json",
  );
  if (!resp.ok) {
    throw new Error(`Failed to load arms policy data: ${resp.status}`);
  }
  armsDataCache = (await resp.json()) as ArmsData;
  return armsDataCache;
}

// For testing / local dev: allow loading from local file system
export async function loadDispatchDataLocal(): Promise<DispatchData> {
  if (dispatchDataCache) return dispatchDataCache;
  // In production, this would be bundled or fetched from KV
  // For now, we'll use the GitHub raw URL
  return loadDispatchData();
}

export async function loadArmsDataLocal(): Promise<ArmsData> {
  if (armsDataCache) return armsDataCache;
  return loadArmsData();
}

// ─── Dispatch Policy Evaluation ─────────────────────────────────────────────

/**
 * Evaluates the dispatch policy (outer routing gate).
 * Checks: requiresAuth, publicRead, scopes, permission sets.
 */
export async function evaluateDispatchPolicy(input: PolicyInput): Promise<PolicyDecision> {
  const data = await loadDispatchData();
  console.log("DEBUG dispatch data loaded:", JSON.stringify(data));
  const { route, auth, permission_sets, skipDispatchScopeCheck } = input;
  const nsid = route.nsid;

  const methodPolicy = data.method_policy;

  // internal_service if auth.method == "service-jwt"
  const internal_service = auth.method === "service-jwt";

  // public_read if route doesn't require auth AND policy allows public read
  const public_read = !route.requiresAuth && methodPolicy.publicRead;

  // scope_allowed: check if any auth scope matches allowed scopes (glob)
  // Skip scope check for NSIDs that have detail policies (e.g., arms)
  let scope_allowed = true;
  if (!skipDispatchScopeCheck) {
    scope_allowed = auth.scopes.some((scope) =>
      methodPolicy.allowedScopes.some((allowed) => globMatch(allowed, scope)),
    );
  }

  // permission_set_allowed: check if any permission set matches allowed
  const permission_set_allowed = permission_sets.some((ps) =>
    methodPolicy.allowedPermissionSets.includes(ps),
  );

  let allow = false;
  let reason = "";

  if (internal_service) {
    allow = true;
    reason = "internal-service";
  } else if (public_read) {
    allow = true;
    reason = "public-read";
  } else if (auth.method !== "public" && scope_allowed) {
    allow = true;
    reason = "scope-or-permission-set";
  } else if (auth.method !== "public" && permission_set_allowed) {
    allow = true;
    reason = "scope-or-permission-set";
  }

  // Deny reasons
  if (!allow) {
    if (auth.method === "public") {
      reason = "authentication-required";
    } else {
      reason = "insufficient-scope";
    }
  }

  const deny_obligations: string[] = [];
  if (!allow) {
    deny_obligations.push("audit_authz_denied");
    if (auth.method === "public") {
      deny_obligations.push("return_401");
    } else {
      deny_obligations.push("return_403");
    }
  }

  return { allow, reason, deny_obligations };
}

// ─── Arms Policy Evaluation ─────────────────────────────────────────────────

/**
 * Evaluates the arms policy (inner detail gate for arms NSIDs).
 * Checks: requiresAuth, scopes, permissions, requiresHolderAuthSession, export control.
 */
export async function evaluateArmsPolicy(input: PolicyInput): Promise<PolicyDecision> {
  const data = await loadArmsData();
  const { route, auth, permission_sets, params } = input;
  const nsid = route.nsid;

  const methodPolicy = data.method_policy[nsid];
  if (!methodPolicy) {
    // No policy defined for this NSID - deny by default
    return {
      allow: false,
      reason: "no-policy-defined",
      deny_obligations: ["return_403", "audit_authz_denied"],
    };
  }

  const internal_service = auth.method === "service-jwt";
  const public_read = methodPolicy.publicRead;

  // scope_allowed
  const scope_allowed = auth.scopes.some((scope) =>
    methodPolicy.allowedScopes.some((allowed) => globMatch(allowed, scope)),
  );

  // permission_set_allowed
  const permission_set_allowed = permission_sets.some((ps) =>
    methodPolicy.allowedPermissionSets.includes(ps),
  );

  // holder_auth_session_valid
  const holder_auth_session_valid = auth.holderAuthSessionPassed === true;

  // requires_holder_session
  const requires_holder_session = methodPolicy.requiresHolderAuthSession === true;

  // export_restricted check
  let export_restricted = false;
  if (
    (nsid === "com.etzhayyim.apps.arms.transferCustody" ||
      nsid === "com.etzhayyim.apps.arms.reportIncident") &&
    !is_string(params.destinationJurisdiction)
  ) {
    export_restricted = true;
  }
  if (
    (nsid === "com.etzhayyim.apps.arms.transferCustody" ||
      nsid === "com.etzhayyim.apps.arms.reportIncident") &&
    is_string(params.destinationJurisdiction) &&
    data.export_restricted_jurisdictions.includes(params.destinationJurisdiction as string)
  ) {
    export_restricted = true;
  }

  let allow = false;
  let reason = "";

  // Allow rules (mirroring arms/policy.rego)
  if (internal_service && scope_allowed && !export_restricted) {
    allow = true;
    reason = "internal-service";
  } else if (!methodPolicy.requiresAuth && public_read && !export_restricted) {
    allow = true;
    reason = "public-read";
  } else if (
    !internal_service &&
    !public_read &&
    auth.method !== "public" &&
    scope_allowed &&
    !requires_holder_session &&
    !export_restricted
  ) {
    allow = true;
    reason = "scope-allowed";
  } else if (
    !internal_service &&
    !public_read &&
    auth.method !== "public" &&
    permission_set_allowed &&
    !requires_holder_session &&
    !export_restricted
  ) {
    allow = true;
    reason = "permission-set-allowed";
  } else if (
    !internal_service &&
    !public_read &&
    auth.method !== "public" &&
    scope_allowed &&
    requires_holder_session &&
    holder_auth_session_valid &&
    !export_restricted
  ) {
    allow = true;
    reason = "holder-auth-session-required";
  } else if (
    !internal_service &&
    !public_read &&
    auth.method !== "public" &&
    permission_set_allowed &&
    requires_holder_session &&
    holder_auth_session_valid &&
    !export_restricted
  ) {
    allow = true;
    reason = "holder-auth-session-required";
  }

  // Deny reasons
  if (!allow) {
    if (export_restricted) {
      reason = "export-control-blocked";
    } else if (requires_holder_session && !holder_auth_session_valid && auth.method !== "public") {
      reason = "holder-auth-session-required";
    } else if (auth.method === "public" && !export_restricted) {
      reason = "authentication-required";
    } else if (!requires_holder_session && !export_restricted) {
      reason = "insufficient-scope";
    } else {
      reason = "insufficient-scope";
    }
  }

  const deny_obligations: string[] = [];
  if (!allow) {
    deny_obligations.push("audit_authz_denied");
    if (export_restricted) {
      deny_obligations.push("return_451");
      deny_obligations.push("audit_export_control");
    } else if (auth.method === "public") {
      deny_obligations.push("return_401");
    } else {
      deny_obligations.push("return_403");
    }
  }

  return { allow, reason, deny_obligations };
}

// ─── Combined Policy Evaluation ─────────────────────────────────────────────

export interface PolicyRoutingEntry {
  policies: ("dispatch" | "arms")[];
}

/**
 * Loads the policy routing map from the EDN file.
 * In production, this would be bundled or loaded from KV.
 */
export async function loadPolicyRoutingMap(): Promise<Record<string, PolicyRoutingEntry>> {
  // For now, return a hardcoded map matching the EDN file
  // In production, this should be loaded from the EDN file or bundled
  return {
    "com.etzhayyim.apps.arms.": { policies: ["dispatch", "arms"] },
    "com.etzhayyim.apps.arms.transferCustody": { policies: ["dispatch", "arms"] },
    "com.etzhayyim.apps.arms.checkOutFirearm": { policies: ["dispatch", "arms"] },
    "com.etzhayyim.apps.kotoba.": { policies: ["dispatch"] },
    "com.etzhayyim.apps.kotobase.": { policies: ["dispatch"] },
    "com.etzhayyim.": { policies: ["dispatch"] },
    "com.etzhayyim.apps.unispsc.": { policies: ["dispatch"] },
    "app.bsky.": { policies: ["dispatch"] },
    "com.atproto.": { policies: ["dispatch"] },
    "chat.bsky.": { policies: ["dispatch"] },
    // default
    "default": { policies: ["dispatch"] },
  };
}

/**
 * Finds the policy routing entry for a given NSID.
 * Uses prefix matching (first match wins, more specific first).
 */
export function findPolicyRoutingEntry(
  nsid: string,
  routingMap: Record<string, PolicyRoutingEntry>,
): PolicyRoutingEntry {
  // Sort keys by length descending (more specific first)
  const keys = Object.keys(routingMap)
    .filter((k) => k !== "default")
    .sort((a, b) => b.length - a.length);

  for (const key of keys) {
    if (nsid.startsWith(key)) {
      return routingMap[key];
    }
  }
  return routingMap.default ?? { policies: ["dispatch"] };
}

/**
 * Evaluates all required policies for an XRPC request.
 * Returns the combined decision (all policies must allow).
 */
export async function evaluateXrpcPolicies(input: PolicyInput): Promise<PolicyDecision> {
  const routingMap = await loadPolicyRoutingMap();
  const entry = findPolicyRoutingEntry(input.route.nsid, routingMap);

  const decisions: PolicyDecision[] = [];

  // Determine if this NSID has a detail policy (arms) that handles scopes
  const hasDetailPolicy = entry.policies.includes("arms");

  for (const policyName of entry.policies) {
    let decision: PolicyDecision;
    if (policyName === "dispatch") {
      // Skip dispatch scope check for NSIDs with detail policies (arms)
      // The detail policy will handle scope validation
      const dispatchInput = hasDetailPolicy
        ? { ...input, skipDispatchScopeCheck: true }
        : input;
      decision = await evaluateDispatchPolicy(dispatchInput);
    } else if (policyName === "arms") {
      decision = await evaluateArmsPolicy(input);
    } else {
      throw new Error(`Unknown policy: ${policyName}`);
    }
    decisions.push(decision);

    // Short-circuit: if any policy denies, the whole request is denied
    if (!decision.allow) {
      return decision;
    }
  }

  // All policies allowed - combine results
  // The most specific reason wins (arms reason > dispatch reason)
  const armsDecision = decisions.find((d) => d.reason !== "internal-service" && d.reason !== "public-read" && d.reason !== "scope-or-permission-set");
  const finalReason = armsDecision?.reason ?? decisions[0]?.reason ?? "allowed";

  // Combine deny obligations (should be empty if all allowed)
  const allDenyObligations = decisions.flatMap((d) => d.deny_obligations);

  return {
    allow: true,
    reason: finalReason,
    deny_obligations: allDenyObligations,
  };
}

// ─── Helper ─────────────────────────────────────────────────────────────────

function is_string(val: unknown): val is string {
  return typeof val === "string";
}