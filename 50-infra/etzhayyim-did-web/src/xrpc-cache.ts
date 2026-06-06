// ─── Read-path edge caching policy ───────────────────────────────────────
//
// The apex landing ("vibes") renders client-side: the SvelteKit shell paints
// in <100ms, then the SPA must await several app.bsky.* read queries before any
// post appears. Measured (2026-06-06) those AppView queries cost 2.8–5.2s EACH,
// warm or cold (getFeed ~2.8s / getTimeline ~5.2s / getProfile ~3.2s), so a
// logged-out visitor stares at a blank feed for seconds. The proxy hop itself
// adds only ~70ms — the latency is the AppView backend (atproto.etzhayyim.com).
//
// Until that backend is sped up, the Worker absorbs the repeat cost at the CF
// edge for ANONYMOUS read requests only. An authenticated request (Authorization
// / dpop header present) is NEVER cached — getTimeline et al. are personalized,
// and caching one user's view for another would be a privacy defect. The cache
// key is the full GET URL (NSID + query), so each feed/profile/cursor is a
// distinct entry, shared only across logged-out visitors who by definition see
// the same public data.
//
// Pure + dependency-free so it is unit-testable without loading the Worker
// entry module (which JSON-imports did.json and binds a Durable Object).

export const CACHEABLE_READ_NSIDS = new Set<string>([
  "app.bsky.feed.getFeed",
  "app.bsky.feed.getDiscoverFeed",
  "app.bsky.feed.getAuthorFeed",
  "app.bsky.feed.getPostThread",
  "app.bsky.feed.getTimeline",
  "app.bsky.feed.getFeedGenerator",
  "app.bsky.feed.getFeedGenerators",
  "app.bsky.actor.getProfile",
  "app.bsky.actor.getProfiles",
]);

// Browser-visible freshness vs edge-shared freshness. s-maxage governs the CF
// edge; stale-while-revalidate lets the edge serve a slightly-stale feed
// instantly while it refreshes in the background — so only the first visitor in
// each window eats the multi-second backend cost.
export const XRPC_EDGE_MAXAGE = 15;
export const XRPC_EDGE_SMAXAGE = 30;
export const XRPC_EDGE_SWR = 300;
export const XRPC_CACHE_CONTROL = `public, max-age=${XRPC_EDGE_MAXAGE}, s-maxage=${XRPC_EDGE_SMAXAGE}, stale-while-revalidate=${XRPC_EDGE_SWR}`;

// A request is edge-cacheable iff: it is an anonymous (no-auth) GET for a known
// public read NSID. HEAD is excluded (no body to cache); any auth/dpop header
// disqualifies it.
export function isAnonymousReadXrpc(request: Request, nsid: string): boolean {
  if (request.method !== "GET") return false;
  if (!CACHEABLE_READ_NSIDS.has(nsid)) return false;
  if (request.headers.has("authorization")) return false;
  if (request.headers.has("dpop")) return false;
  return true;
}

// Stable cache key: a bare GET on the same URL, no client headers (so cookies /
// user-agent / accept-encoding never fragment or poison the shared entry).
export function xrpcCacheKey(request: Request): Request {
  const u = new URL(request.url);
  return new Request(u.toString(), { method: "GET" });
}
