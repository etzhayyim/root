// XRPC NSID → upstream routing (extracted from worker.ts so it is unit-testable).
//
// Every `/xrpc/{NSID}` request is routed by NSID *prefix* to the upstream origin
// declared in env. `findXrpcRoute` returns the FIRST matching prefix, so more
// specific prefixes must precede the families they refine.
//
// **Method A cutover (independent etzhayyim PDS, gftd.ai dependency drop):**
// `com.atproto.repo.*` (record read/write) and `com.atproto.sync.*` (repo CAR /
// federation) move to the independent etzhayyim PDS (`XRPC_PDS_UPSTREAM`). Until
// that env is provisioned they FALL BACK to the current `XRPC_ATPROTO_UPSTREAM`
// (gftd alias), so the route is INERT — prod behaviour is byte-identical until an
// operator sets `XRPC_PDS_UPSTREAM` to the deployed PDS at the actual cutover.
// `app.bsky.*` (AppView feed/profile) stays on the AppView upstream for now; its
// move to local kotoba rendering is a later slice (feed-curation.ts untouched).

export interface NsidRoute {
  prefix: string;
  /** primary env key holding the upstream origin (e.g. "XRPC_ATPROTO_UPSTREAM"). */
  upstream: string;
  /** optional env key used when `upstream` is empty/unset — lets a cutover route
   *  stay inert (fall back to the prior upstream) until ops provisions the new one. */
  fallback?: string;
  /** match the NSID EXACTLY (not by prefix). Used for single-method cutover routes
   *  so e.g. `app.bsky.feed.getAuthorFeed` does not also capture `…getAuthorFeeds`. */
  exact?: boolean;
}

// ─── XRPC Policy Routing Map (Issue #1509) ────────────────────────────────────
//
// Defines which OPA policies MUST be evaluated for each NSID pattern.
// Dual-gate: arms NSIDs require BOTH dispatch (outer) + arms (inner detail gate).
// Other NSIDs require only dispatch.
//
// Format: { nsidPrefix: { policies: ["dispatch" | "arms"] } }
// More specific prefixes win (longer prefix matched first).
const POLICY_ROUTING_MAP: Record<string, { policies: ("dispatch" | "arms")[] }> = {
  "com.etzhayyim.apps.arms.":           { policies: ["dispatch", "arms"] },
  "com.etzhayyim.apps.arms.transferCustody": { policies: ["dispatch", "arms"] },
  "com.etzhayyim.apps.arms.checkOutFirearm":  { policies: ["dispatch", "arms"] },
  "com.etzhayyim.apps.kotoba.":         { policies: ["dispatch"] },
  "com.etzhayyim.apps.kotobase.":       { policies: ["dispatch"] },
  "com.etzhayyim.":                     { policies: ["dispatch"] },
  "com.etzhayyim.apps.unispsc.":        { policies: ["dispatch"] },
  "app.bsky.":                          { policies: ["dispatch"] },
  "com.atproto.":                       { policies: ["dispatch"] },
  "chat.bsky.":                         { policies: ["dispatch"] },
  // default fallback
  "default":                            { policies: ["dispatch"] },
};

export interface NsidRoute {
  prefix: string;
  /** primary env key holding the upstream origin (e.g. "XRPC_ATPROTO_UPSTREAM"). */
  upstream: string;
  /** optional env key used when `upstream` is empty/unset — lets a cutover route
   *  stay inert (fall back to the prior upstream) until ops provisions the new one. */
  fallback?: string;
  /** match the NSID EXACTLY (not by prefix). Used for single-method cutover routes
   *  so e.g. `app.bsky.feed.getAuthorFeed` does not also capture `…getAuthorFeeds`. */
  exact?: boolean;
}

export const XRPC_ROUTES: NsidRoute[] = [
  { prefix: "com.etzhayyim.apps.unispsc.", upstream: "XRPC_UNISPSC_UPSTREAM" },
  // Method A: repo/record/sync cut over to the independent PDS, fall back to the
  // AppView upstream until XRPC_PDS_UPSTREAM is provisioned (so this is inert).
  // These MUST precede the generic `com.atproto.` below (first-match wins).
  { prefix: "com.atproto.repo.", upstream: "XRPC_PDS_UPSTREAM", fallback: "XRPC_ATPROTO_UPSTREAM" },
  { prefix: "com.atproto.sync.", upstream: "XRPC_PDS_UPSTREAM", fallback: "XRPC_ATPROTO_UPSTREAM" },
  // Method A (feed rendering): an actor's OWN feed renders from the independent
  // PDS's local kotoba log (the records it holds are authoritative). EXACT match,
  // ahead of the generic `app.bsky.` so it wins. Inert until XRPC_PDS_UPSTREAM is
  // set. getProfile stays on the AppView for now (richer displayName/avatar);
  // the aggregate home/discover feeds (getTimeline/getFeed) are NOT moved here.
  { prefix: "app.bsky.feed.getAuthorFeed", upstream: "XRPC_PDS_UPSTREAM", fallback: "XRPC_ATPROTO_UPSTREAM", exact: true },
  // AT Protocol / Bluesky read+write. app.bsky.* = AppView reads (feed/profile);
  // the remaining com.atproto.* (server/identity/admin) stay on the AppView host.
  { prefix: "app.bsky.",             upstream: "XRPC_ATPROTO_UPSTREAM" },
  { prefix: "com.atproto.",          upstream: "XRPC_ATPROTO_UPSTREAM" },
  { prefix: "chat.bsky.",            upstream: "XRPC_CHAT_UPSTREAM" },
  // kotoba graph query / SPARQL / MaterializedView surface → the kotoba node
  // (more specific than the com.etzhayyim. catch-all below, so it comes first).
  { prefix: "com.etzhayyim.apps.kotoba.",   upstream: "XRPC_KOTOBA_UPSTREAM" },
  { prefix: "com.etzhayyim.apps.kotobase.", upstream: "XRPC_KOTOBA_UPSTREAM" },
  // etzhayyim platform extensions (convo, signal, kagami, projector, mcp, rtc).
  { prefix: "com.etzhayyim.",              upstream: "XRPC_etzhayyim_UPSTREAM" },
];

export function findXrpcRoute(nsid: string): NsidRoute | null {
  for (const r of XRPC_ROUTES) {
    if (r.exact ? nsid === r.prefix : nsid.startsWith(r.prefix)) return r;
  }
  return null;
}

/** Resolve a route to its upstream origin string, honoring `fallback`. Returns
 *  undefined when neither the primary nor the fallback env is set (caller → 503). */
export function resolveUpstream(
  route: NsidRoute,
  env: Record<string, string | undefined>,
): string | undefined {
  const primary = env[route.upstream];
  if (primary) return primary;
  if (route.fallback) {
    const fb = env[route.fallback];
    if (fb) return fb;
  }
  return undefined;
}

// ─── XRPC Policy Evaluation (Issue #1509) ─────────────────────────────────────
//
// Dual-gate policy evaluation:
//   - dispatch: outer routing gate (auth, scopes, permissions)
//   - arms:   inner detail gate for arms NSIDs (holderAuthSession, export control)
// Both MUST allow for the request to proceed.

export interface AuthContext {
  method: "public" | "oauth" | "did-session" | "service-jwt" | string;
  scopes: string[];
  holderAuthSessionPassed?: boolean;
}

export interface PolicyInput {
  route: { nsid: string; requiresAuth?: boolean };
  auth: AuthContext;
  permission_sets: string[];
  params: Record<string, unknown>;
  skipDispatchScopeCheck?: boolean;
}

export interface PolicyDecision {
  allow: boolean;
  reason: string;
  deny_obligations: string[];
}

// Glob match utility for scope patterns like "rpc[?]lxm=com.etzhayyim.apps.arms.*"
function globMatch(pattern: string, input: string): boolean {
  let regexPattern = pattern
    .replace(/\[\?\]/g, "\x01")   // [?] -> placeholder (SOH)
    .replace(/\*/g, "\x02")       // * -> placeholder (STX)
    .replace(/[.+^${}()|[\]\\]/g, "\\$&"); // escape regex special chars
  regexPattern = regexPattern
    .replace(/\x01/g, ".")        // [?] -> any single char
    .replace(/\x02/g, ".*");      // * -> any chars
  return new RegExp(`^${regexPattern}$`).test(input);
}

// Find policy routing entry for NSID (prefix match, longest first)
export function findPolicyRoutingEntry(
  nsid: string,
): { policies: ("dispatch" | "arms")[] } {
  const keys = Object.keys(POLICY_ROUTING_MAP)
    .filter((k) => k !== "default")
    .sort((a, b) => b.length - a.length);
  for (const key of keys) {
    if (nsid.startsWith(key)) return POLICY_ROUTING_MAP[key];
  }
  return POLICY_ROUTING_MAP.default;
}

// Dispatch policy: outer routing gate (requiresAuth, scopes, permissions)
export async function evaluateDispatchPolicy(
  input: PolicyInput,
): Promise<PolicyDecision> {
  // Dispatch policy is generic: only allows atproto scopes
  const allowedScopes = ["rpc[?]lxm=com.atproto.repo.createRecord"];
  const allowedPermissionSets: string[] = [];
  const publicRead = false; // generic dispatch has no publicRead

  const { route, auth, permission_sets, skipDispatchScopeCheck } = input;
  const internal_service = auth.method === "service-jwt";

  // Skip scope check for NSIDs with detail policies (e.g., arms)
  let scope_allowed = true;
  if (!skipDispatchScopeCheck) {
    scope_allowed = auth.scopes.some((scope) =>
      allowedScopes.some((allowed) => globMatch(allowed, scope)),
    );
  }

  const permission_set_allowed = permission_sets.some((ps) =>
    allowedPermissionSets.includes(ps),
  );

  let allow = false;
  let reason = "";

  if (internal_service) {
    allow = true;
    reason = "internal-service";
  } else if (auth.method !== "public" && scope_allowed) {
    allow = true;
    reason = "scope-or-permission-set";
  } else if (auth.method !== "public" && permission_set_allowed) {
    allow = true;
    reason = "scope-or-permission-set";
  }

  if (!allow) {
    if (auth.method === "public") reason = "authentication-required";
    else reason = "insufficient-scope";
  }

  const deny_obligations: string[] = [];
  if (!allow) {
    deny_obligations.push("audit_authz_denied");
    if (auth.method === "public") deny_obligations.push("return_401");
    else deny_obligations.push("return_403");
  }

  return { allow, reason, deny_obligations };
}

// Arms policy: inner detail gate (holderAuthSession, export control)
export async function evaluateArmsPolicy(
  input: PolicyInput,
): Promise<PolicyDecision> {
  const { route, auth, permission_sets, params } = input;
  const nsid = route.nsid;

  const methodPolicies: Record<string, {
    allowedScopes: string[];
    allowedPermissionSets: string[];
    requiresHolderAuthSession?: boolean;
    publicRead?: boolean;
  }> = {
    "com.etzhayyim.apps.arms.registerFirearm": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.registerFirearm"],
      allowedPermissionSets: ["arms:authority", "arms:system"],
    },
    "com.etzhayyim.apps.arms.authenticateHolder": {
      allowedScopes: ["rpc[?]lxm=*"],
      allowedPermissionSets: [],
      publicRead: true,
    },
    "com.etzhayyim.apps.arms.verifyAuthChallenge": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.verifyAuthChallenge", "rpc[?]lxm=*"],
      allowedPermissionSets: [],
    },
    "com.etzhayyim.apps.arms.issuePermit": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.issuePermit"],
      allowedPermissionSets: ["arms:authority"],
    },
    "com.etzhayyim.apps.arms.transferCustody": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.transferCustody"],
      allowedPermissionSets: ["arms:holder", "arms:authority"],
      requiresHolderAuthSession: true,
    },
    "com.etzhayyim.apps.arms.checkOutFirearm": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.checkOutFirearm", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority"],
      requiresHolderAuthSession: true,
    },
    "com.etzhayyim.apps.arms.checkInFirearm": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.checkInFirearm", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority"],
    },
    "com.etzhayyim.apps.arms.reportIncident": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.reportIncident", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority", "arms:law-enforcement"],
    },
    "com.etzhayyim.apps.arms.getFirearm": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.getFirearm", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority", "arms:law-enforcement"],
    },
    "com.etzhayyim.apps.arms.listFirearms": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.listFirearms", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority", "arms:law-enforcement"],
    },
    "com.etzhayyim.apps.arms.listPermits": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.listPermits", "rpc[?]lxm=*"],
      allowedPermissionSets: ["arms:holder", "arms:authority", "arms:law-enforcement"],
    },
    "com.etzhayyim.apps.arms.getAuditLog": {
      allowedScopes: ["rpc[?]lxm=com.etzhayyim.apps.arms.getAuditLog"],
      allowedPermissionSets: ["arms:authority", "arms:law-enforcement"],
    },
  };

  const methodPolicy = methodPolicies[nsid];
  if (!methodPolicy) {
    return { allow: false, reason: "no-policy-defined", deny_obligations: ["return_403", "audit_authz_denied"] };
  }

  const internal_service = auth.method === "service-jwt";
  const public_read = methodPolicy.publicRead === true;

  const scope_allowed = auth.scopes.some((scope) =>
    methodPolicy.allowedScopes.some((allowed) => globMatch(allowed, scope)),
  );
  const permission_set_allowed = permission_sets.some((ps) =>
    methodPolicy.allowedPermissionSets.includes(ps),
  );
  const holder_auth_session_valid = auth.holderAuthSessionPassed === true;
  const requires_holder_session = methodPolicy.requiresHolderAuthSession === true;

  const restrictedJurisdictions = ["KP", "IR", "SY", "RU", "BY", "MM", "SD", "CF", "LY", "SO", "YE", "SS"];
  let export_restricted = false;
  if (
    (nsid === "com.etzhayyim.apps.arms.transferCustody" || nsid === "com.etzhayyim.apps.arms.reportIncident") &&
    !is_string(params.destinationJurisdiction)
  ) export_restricted = true;
  if (
    (nsid === "com.etzhayyim.apps.arms.transferCustody" || nsid === "com.etzhayyim.apps.arms.reportIncident") &&
    is_string(params.destinationJurisdiction) &&
    restrictedJurisdictions.includes(params.destinationJurisdiction as string)
  ) export_restricted = true;

  let allow = false;
  let reason = "";

  if (internal_service && scope_allowed && !export_restricted) { allow = true; reason = "internal-service"; }
  else if (!methodPolicy.allowedScopes && public_read && !export_restricted) { allow = true; reason = "public-read"; }
  else if (!internal_service && !public_read && auth.method !== "public" && scope_allowed && !requires_holder_session && !export_restricted) { allow = true; reason = "scope-allowed"; }
  else if (!internal_service && !public_read && auth.method !== "public" && permission_set_allowed && !requires_holder_session && !export_restricted) { allow = true; reason = "permission-set-allowed"; }
  else if (!internal_service && !public_read && auth.method !== "public" && scope_allowed && requires_holder_session && holder_auth_session_valid && !export_restricted) { allow = true; reason = "holder-auth-session-required"; }
  else if (!internal_service && !public_read && auth.method !== "public" && permission_set_allowed && requires_holder_session && holder_auth_session_valid && !export_restricted) { allow = true; reason = "holder-auth-session-required"; }

  if (!allow) {
    if (export_restricted) reason = "export-control-blocked";
    else if (requires_holder_session && !holder_auth_session_valid && auth.method !== "public") reason = "holder-auth-session-required";
    else if (auth.method === "public" && !export_restricted) reason = "authentication-required";
    else reason = "insufficient-scope";
  }

  const deny_obligations: string[] = [];
  if (!allow) {
    deny_obligations.push("audit_authz_denied");
    if (export_restricted) { deny_obligations.push("return_451"); deny_obligations.push("audit_export_control"); }
    else if (auth.method === "public") deny_obligations.push("return_401");
    else deny_obligations.push("return_403");
  }

  return { allow, reason, deny_obligations };
}

function is_string(val: unknown): val is string { return typeof val === "string"; }

// Combined policy evaluation for an XRPC request
export async function evaluateXrpcPolicies(input: PolicyInput): Promise<PolicyDecision> {
  const entry = findPolicyRoutingEntry(input.route.nsid);
  const hasDetailPolicy = entry.policies.includes("arms");

  for (const policyName of entry.policies) {
    let decision: PolicyDecision;
    if (policyName === "dispatch") {
      const dispatchInput = hasDetailPolicy ? { ...input, skipDispatchScopeCheck: true } : input;
      decision = await evaluateDispatchPolicy(dispatchInput);
    } else if (policyName === "arms") {
      decision = await evaluateArmsPolicy(input);
    } else { throw new Error(`Unknown policy: ${policyName}`); }

    if (!decision.allow) return decision;
  }

  const armsDecision = entry.policies.includes("arms") ? "arms" : "dispatch";
  return { allow: true, reason: armsDecision, deny_obligations: [] };
}
