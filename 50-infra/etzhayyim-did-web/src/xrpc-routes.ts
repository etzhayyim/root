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
}

export const XRPC_ROUTES: NsidRoute[] = [
  { prefix: "com.etzhayyim.apps.unispsc.", upstream: "XRPC_UNISPSC_UPSTREAM" },
  // Method A: repo/record/sync cut over to the independent PDS, fall back to the
  // AppView upstream until XRPC_PDS_UPSTREAM is provisioned (so this is inert).
  // These MUST precede the generic `com.atproto.` below (first-match wins).
  { prefix: "com.atproto.repo.", upstream: "XRPC_PDS_UPSTREAM", fallback: "XRPC_ATPROTO_UPSTREAM" },
  { prefix: "com.atproto.sync.", upstream: "XRPC_PDS_UPSTREAM", fallback: "XRPC_ATPROTO_UPSTREAM" },
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
    if (nsid.startsWith(r.prefix)) return r;
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
