// Apex discover/home feed curation (ADR-2606232130).
//
// The apex `etzhayyim.com` home feed (app.bsky.feed.getTimeline / getDiscoverFeed)
// is the standard recency-ordered AppView feed. Left raw it is dominated by the
// single highest-cadence poster — the external `shinshi` pipeline
// (did:web:shinshi.etzhayyim.com), which is EXCLUDE-classified for etzhayyim
// governance (ADR-2605212245). This module applies a TRANSPARENT, RULE-BASED,
// DETERMINISTIC curation over the feed page the apex returns:
//
//   1. QUARANTINE — drop items authored by an EXCLUDE'd external poster from the
//      AGGREGATE feed only. Their own author feed / profile is untouched (viewing
//      shinshi directly still shows shinshi).
//   2. BOOST-OWN — stable-partition etzhayyim's own actors (root + agents +
//      kagami mirrors) to the front, preserving recency order WITHIN each group.
//
// This is NOT engagement optimization / addictive ranking (Charter §1.13 / Rider
// §2(h)): no per-user personalization, no retention/affinity signal, no infinite
// scroll — a fixed, auditable rule any member can verify. The whole transform is
// pure and unit-tested.

export interface FeedAuthor {
  did?: string;
  handle?: string;
}
export interface FeedPost {
  author?: FeedAuthor;
  [k: string]: unknown;
}
export interface FeedItem {
  post?: FeedPost;
  [k: string]: unknown;
}
export interface FeedBody {
  feed?: FeedItem[];
  cursor?: string;
  [k: string]: unknown;
}

// Aggregate feeds the apex home view uses — curated. Author-scoped feeds
// (getAuthorFeed) and threads (getPostThread) are intentionally NOT curated:
// asking for one actor's posts must return exactly that actor's posts.
export const CURATED_FEED_NSIDS: ReadonlySet<string> = new Set([
  "app.bsky.feed.getTimeline",
  "app.bsky.feed.getDiscoverFeed",
]);

// External posters EXCLUDE'd from etzhayyim governance (ADR-2605212245). Matched
// as a substring of the author DID or handle (covers did:web + handle families).
//
/** Method A discover-feed cutover. When XRPC_PDS_UPSTREAM is provisioned, the
 *  aggregate home/discover feeds (CURATED_FEED_NSIDS) render from the independent
 *  PDS's LOCAL kotoba discover feed (`com.etzhayyim.feed.getDiscover`) — only
 *  etzhayyim actors write to that PDS, so the gftd shinshi flood structurally
 *  cannot appear (the source-side fix the quarantine below approximated).
 *  Returns null when XRPC_PDS_UPSTREAM is empty/unset → INERT: keep curating the
 *  gftd feed exactly as today (prod byte-identical until ops flips the env). */
export function discoverFeedTarget(
  pdsUpstream: string | undefined | null,
): { upstream: string; nsid: string } | null {
  const u = (pdsUpstream ?? "").trim();
  return u ? { upstream: u, nsid: "com.etzhayyim.feed.getDiscover" } : null;
}

// The LIVE shinshi pipeline actually posts as `did:web:sh1n5h1x.gftd.ai` — it runs
// on gftd.ai infrastructure, NOT under *.etzhayyim.com, so the original markers
// below (the ADR-2605212245 mental model) never matched it and the apex aggregate
// feed stayed flooded by gftd's shinshi. Per the founder directive "drop the gftd.ai
// dependency" we quarantine the gftd.ai shinshi domain family too: etzhayyim's
// aggregate home/discover feed must not be dominated by a poster on gftd.ai infra.
export const QUARANTINED_AUTHOR_MARKERS: readonly string[] = [
  "shinshi.etzhayyim.com",
  "sh1n5h1x.etzhayyim.com",
  "sh1n5h1x.gftd.ai",
  "shinshi.gftd.ai",
];

function authorId(a?: FeedAuthor | null): string {
  if (!a) return "";
  return `${a.did ?? ""} ${a.handle ?? ""}`.toLowerCase();
}

/** Is this author an EXCLUDE'd external poster quarantined from aggregate feeds? */
export function isQuarantinedAuthor(a?: FeedAuthor | null): boolean {
  const id = authorId(a);
  return id !== "" && QUARANTINED_AUTHOR_MARKERS.some((m) => id.includes(m));
}

/** Is this author one of etzhayyim's OWN actors (root / agent / mirror)?
 *  did:web:etzhayyim.com[...] or a *.etzhayyim.com handle, excluding quarantined
 *  externals (which are also on a *.etzhayyim.com subdomain). */
export function isOwnActor(a?: FeedAuthor | null): boolean {
  if (isQuarantinedAuthor(a)) return false;
  const did = (a?.did ?? "").toLowerCase();
  const handle = (a?.handle ?? "").toLowerCase();
  return (
    did.startsWith("did:web:etzhayyim.com") ||
    handle === "etzhayyim.com" ||
    handle.endsWith(".etzhayyim.com")
  );
}

export interface CurateOpts {
  quarantine?: boolean;
  boostOwn?: boolean;
}

/** Pure feed-page curation: quarantine EXCLUDE'd externals, then stable-boost
 *  etzhayyim's own actors to the front (recency preserved within each group).
 *  Returns the body unchanged when it has no `feed` array. */
export function curateFeed(body: FeedBody, opts: CurateOpts = {}): FeedBody {
  const { quarantine = true, boostOwn = true } = opts;
  if (!body || !Array.isArray(body.feed)) return body;

  let feed = body.feed;
  if (quarantine) {
    feed = feed.filter((it) => !isQuarantinedAuthor(it?.post?.author));
  }
  if (boostOwn) {
    const own: FeedItem[] = [];
    const rest: FeedItem[] = [];
    for (const it of feed) {
      (isOwnActor(it?.post?.author) ? own : rest).push(it);
    }
    feed = [...own, ...rest];
  }
  return { ...body, feed };
}
