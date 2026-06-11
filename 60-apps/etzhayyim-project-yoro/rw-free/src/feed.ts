import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  getKotobaCfg,
  scanYoro,
  type PostRow,
  type ProfileRow,
} from "./kotoba.js";

// Substrate-only feed reads. Per ADR-2605172000, these traverse the AT MST
// via @etzhayyim/sdk `read()` instead of RisingWave MVs. The scaffold is
// single-actor: each yoro adapter instance reads from its own configured
// repo (`config.did`). Cross-DID discovery is a Relay / mst-projector index
// concern, tracked in ADR-2605191358 — until that lands, "Discover" =
// posts published into the operator's own MST.

function didFromUri(uri: string): string {
  // at://<did>/<collection>/<rkey> — second `/` boundary holds the did
  const m = uri.match(/^at:\/\/([^/]+)\//);
  return m ? m[1] : "did:web:unknown";
}

function profileFromDid(did: string): ProfileViewDetailed {
  // Minimal projection. Full profile resolution would read
  // `app.bsky.actor.profile` from the same repo — out-of-scope; the UI
  // hydrates from getProfile separately.
  const handle = did.startsWith("did:web:")
    ? did.slice("did:web:".length).replace(/:/g, ".")
    : did;
  return { did, handle };
}

interface MstRecord {
  uri: string;
  cid?: string;
  value: unknown;
}

function recordToFeedItem(rec: MstRecord): FeedViewPost {
  const value = (rec.value ?? {}) as Record<string, unknown>;
  return {
    post: {
      uri: rec.uri,
      cid: rec.cid ?? "",
      author: profileFromDid(didFromUri(rec.uri)),
      record: value,
      indexedAt:
        (typeof value.createdAt === "string" ? value.createdAt : undefined) ??
        new Date().toISOString(),
    },
  };
}

// ─── kotoba Datom-log read path (ADR-2606013200) ────────────────────────
//
// When the SDK is configured with `kotobaUrl`, feed/graph/actor reads project
// from the kotoba canonical state (the `yoro-social` graph) instead of the
// single-actor PDS MST / superseded kotoba-datomic-projection. Each helper returns
// `null` when kotoba is unconfigured or unreachable, so callers degrade to the
// legacy PDS path and a kotoba outage never 500s the feed.

function profileRowToView(
  did: string,
  profiles: Map<string, ProfileRow>,
): ProfileViewDetailed {
  const base = profileFromDid(did);
  const p = profiles.get(did);
  if (!p) return base;
  return {
    ...base,
    handle: p.handle ?? base.handle,
    displayName: p.displayName,
    description: p.description,
    avatar: p.avatar,
  };
}

function postRowToFeedViewPost(
  row: PostRow,
  profiles: Map<string, ProfileRow>,
): FeedViewPost {
  return {
    post: {
      uri: row.uri,
      cid: row.cid,
      author: profileRowToView(row.author, profiles),
      record:
        row.record ?? {
          $type: "app.bsky.feed.post",
          text: row.text,
          createdAt: row.createdAt,
        },
      indexedAt: row.createdAt || new Date().toISOString(),
    },
  };
}

async function kotobaFeed(
  e: Etzhayyim,
  opts: { authorDid?: string; limit: number },
): Promise<FeedViewPost[] | null> {
  const cfg = getKotobaCfg(e);
  if (!cfg) return null;
  try {
    const scan = await scanYoro(cfg);
    let posts = scan.posts;
    if (opts.authorDid) posts = posts.filter((p) => p.author === opts.authorDid);
    return posts
      .slice(0, opts.limit)
      .map((p) => postRowToFeedViewPost(p, scan.profiles));
  } catch {
    return null;
  }
}

async function collectFeed(
  e: Etzhayyim,
  cursor: string | undefined,
  wantedLimit: number,
): Promise<{ feed: FeedViewPost[]; cursor?: string }> {
  // `e.read` is implemented by both @etzhayyim/sdk and @etzhayyim/sdk-mock;
  // mock returns `{records: [{uri, value}], cursor?}`, real adds `cid`.
  // Pre-seed: when the configured actor repo doesn't exist on the PDS yet,
  // surface an empty feed instead of 500 so the UI shows "no posts".
  let res: { records: MstRecord[]; cursor?: string };
  try {
    res = await (e as unknown as {
      read: (opts: {
        collection: string;
        cursor?: string;
        limit?: number;
      }) => Promise<{ records: MstRecord[]; cursor?: string }>;
    }).read({
      collection: "app.bsky.feed.post",
      cursor,
      limit: Math.min(wantedLimit, 100),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (/Could not find repo|RepoNotFound|repo not found/i.test(message)) {
      return { feed: [], cursor: undefined };
    }
    throw err;
  }

  const feed = res.records.map(recordToFeedItem);
  // Newest-first ordering. MST is TID-keyed (timestamp-prefixed) so insertion
  // order ≈ chronological; explicit sort guards against out-of-order rkeys.
  feed.sort((a, b) =>
    (b.post.indexedAt ?? "").localeCompare(a.post.indexedAt ?? ""),
  );
  return { feed, cursor: res.cursor };
}

export interface ProfileViewDetailed {
  did: string;
  handle: string;
  displayName?: string;
  description?: string;
  avatar?: string;
  banner?: string;
  followersCount?: number;
  followsCount?: number;
  postsCount?: number;
  indexedAt?: string;
  labels?: string[];
  sensitivity?: string;
  viewerFollowing?: boolean;
  performerType?: string;
  contentMode?: string;
  nanoid?: string;
  uiType?: string;
  embedUrl?: string;
  service?: object;
  system?: object;
}

export interface PostView {
  uri: string;
  cid: string;
  author: ProfileViewDetailed;
  record: unknown;
  indexedAt: string;
  likeCount?: number;
  repostCount?: number;
  replyCount?: number;
  viewCount?: number;
}

export interface FeedViewPost {
  post: PostView;
}

export interface GetTimelineInput {
  limit?: number;
  cursor?: string;
}

export interface GetTimelineOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetAuthorFeedInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetAuthorFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetPostThreadInput {
  uri: string;
  depth?: number;
  parentHeight?: number;
}

export interface GetPostThreadOutput {
  thread: unknown;
}

export interface GetRankedFeedInput {
  limit?: number;
  cursor?: string;
  debug?: boolean;
  echoPersistence?: number;
  sessionDwellMs?: number;
  sessionDistinctTopics?: number;
}

export interface RankedFeedDebug {
  eta?: number;
  candidateCount?: number;
  hardGateDropped?: number;
  personalizeOff?: boolean;
  nightMode?: boolean;
  botSuspect?: boolean;
}

export interface GetRankedFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
  debug?: RankedFeedDebug;
}

export interface GetDiscoverFeedInput {
  limit?: number;
  cursor?: string;
}

export interface GetDiscoverFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetFollowersInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetFollowersOutput {
  subject?: ProfileViewDetailed;
  followers: ProfileViewDetailed[];
  cursor?: string;
}

export interface GetFollowsInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetFollowsOutput {
  subject?: ProfileViewDetailed;
  follows: ProfileViewDetailed[];
  cursor?: string;
}

export interface GetProfileInput {
  actor: string;
}

export interface GetProfileOutput {
  profile?: ProfileViewDetailed;
  error?: string;
}

export interface SearchActorsInput {
  q?: string;
  limit?: number;
  cursor?: string;
}

export interface SearchActorsOutput {
  actors: ProfileViewDetailed[];
  cursor?: string;
}

// kotoba-datomic-projection: feed-discover read.
//
// Per ADR-2605231500. When the caller configures a `FEED_DISCOVER_DID`
// pointing to a mst-projector instance emitting
// `com.etzhayyim.projection.feedDiscover` snapshots, getTimeline /
// getDiscoverFeed read the latest snapshot instead of the single-actor
// `collectFeed`. Falls back to single-actor on miss so existing behaviour
// is preserved when no projector is configured. The projection daemon
// + manifest live at `50-infra/mst-projector/projection/`.
async function tryProjectionRead(
  e: Etzhayyim,
  limit: number,
): Promise<FeedViewPost[] | null> {
  const projectorDid = (e as unknown as {
    config?: { projectionDiscoverDid?: string };
  }).config?.projectionDiscoverDid;
  if (!projectorDid) return null;
  try {
    // Use the underlying agent directly so we can read a different repo
    // than the SDK's bound DID. The SDK only ever queries its own DID.
    const agent = await (e as unknown as { pds: () => Promise<{
      com: { atproto: { repo: { listRecords: (input: {
        repo: string; collection: string; limit: number; reverse?: boolean;
      }) => Promise<{
        data: { records: { uri: string; cid: string; value: unknown }[] };
      }> } } };
    }> }).pds();
    const res = await agent.com.atproto.repo.listRecords({
      repo: projectorDid,
      collection: "com.etzhayyim.projection.feedDiscover",
      limit: 1,
      reverse: true,
    });
    const latest = res.data.records[0]?.value as
      | { items?: ProjectionFeedItem[] }
      | undefined;
    if (!latest?.items?.length) return null;
    return latest.items
      .filter((it) => it.verdict !== "reject")  // belt-and-braces; projector
                                                // already drops rejected
      .slice(0, limit)
      .map(projectionItemToFeedViewPost);
  } catch {
    // Projection unavailable — fall through to single-actor feed.
    return null;
  }
}

interface ProjectionFeedItem {
  uri: string;
  cid: string;
  did: string;
  indexedAt: string;
  textPreview?: string;
  verdict?: "approve" | "escalate" | "unverdicted" | "reject";
}

function projectionItemToFeedViewPost(item: ProjectionFeedItem): FeedViewPost {
  return {
    post: {
      uri: item.uri,
      cid: item.cid,
      author: profileFromDid(item.did),
      record: {
        $type: "app.bsky.feed.post",
        text: item.textPreview ?? "",
        createdAt: item.indexedAt,
      },
      indexedAt: item.indexedAt,
    },
  };
}

export async function getTimeline(
  e: Etzhayyim,
  input?: GetTimelineInput
): Promise<GetTimelineOutput> {
  // Following-graph-aware timeline is out of scope for the scaffold: it
  // requires reading `app.bsky.graph.follow` from the caller's repo and
  // joining against per-followed-DID `app.bsky.feed.post` records. Until
  // wired, prefer the feed-discover projection (cross-DID, hot path);
  // fall back to single-actor on projector miss.
  const limit = Math.min(input?.limit ?? 50, 100);
  const fromKotoba = await kotobaFeed(e, { limit });
  if (fromKotoba) return { feed: fromKotoba, cursor: undefined };
  const projected = await tryProjectionRead(e, limit);
  if (projected) return { feed: projected, cursor: undefined };
  return collectFeed(e, input?.cursor, limit);
}

export async function getAuthorFeed(
  e: Etzhayyim,
  input: GetAuthorFeedInput
): Promise<GetAuthorFeedOutput> {
  // Cross-actor read requires the real SDK (`agent.com.atproto.repo.listRecords`
  // against `input.actor`). The mock can't model arbitrary-DID reads, so
  // when the caller is asking for a DID other than this actor's own repo,
  // we delegate to the higher-level read — which on real SDK paths to the
  // configured PDS, on mock returns the in-memory store for the mock's DID
  // (treating the actor arg as a hint, not a filter). Tests that supply
  // `input.actor` against an empty mock will correctly get `feed: []`.
  const limit = Math.min(input.limit ?? 50, 100);
  const fromKotoba = await kotobaFeed(e, { authorDid: input.actor, limit });
  if (fromKotoba) return { feed: fromKotoba, cursor: undefined };
  return collectFeed(e, input.cursor, limit);
}

export async function getPostThread(
  e: Etzhayyim,
  input: GetPostThreadInput
): Promise<GetPostThreadOutput> {
  const cfg = getKotobaCfg(e);
  if (cfg) {
    try {
      const scan = await scanYoro(cfg);
      const root = scan.posts.find((p) => p.uri === input.uri);
      if (root) {
        const replies = scan.posts
          .filter((p) => p.replyParent === input.uri)
          .map((p) => ({
            $type: "app.bsky.feed.defs#threadViewPost",
            post: postRowToFeedViewPost(p, scan.profiles).post,
          }));
        return {
          thread: {
            $type: "app.bsky.feed.defs#threadViewPost",
            post: postRowToFeedViewPost(root, scan.profiles).post,
            replies,
          },
        };
      }
    } catch {
      // fall through to empty thread
    }
  }
  return {
    thread: {},
  };
}

export async function getRankedFeed(
  e: Etzhayyim,
  input?: GetRankedFeedInput
): Promise<GetRankedFeedOutput> {
  const limit = Math.min(input?.limit ?? 50, 100);
  const fromKotoba = await kotobaFeed(e, { limit });
  const { feed, cursor } = fromKotoba
    ? { feed: fromKotoba, cursor: undefined as string | undefined }
    : await collectFeed(e, input?.cursor, limit);
  const result: GetRankedFeedOutput = { feed, cursor };
  if (input?.debug) {
    result.debug = {
      eta: 0,
      candidateCount: feed.length,
      hardGateDropped: 0,
      personalizeOff: true, // ranking model not yet wired
      nightMode: false,
      botSuspect: false,
    };
  }
  return result;
}

export async function getDiscoverFeed(
  e: Etzhayyim,
  input?: GetDiscoverFeedInput
): Promise<GetDiscoverFeedOutput> {
  const limit = Math.min(input?.limit ?? 50, 100);
  const fromKotoba = await kotobaFeed(e, { limit });
  if (fromKotoba) return { feed: fromKotoba, cursor: undefined };
  const projected = await tryProjectionRead(e, limit);
  if (projected) return { feed: projected, cursor: undefined };
  return collectFeed(e, input?.cursor, limit);
}

export async function getFollowers(
  e: Etzhayyim,
  input: GetFollowersInput
): Promise<GetFollowersOutput> {
  const cfg = getKotobaCfg(e);
  if (cfg) {
    try {
      const scan = await scanYoro(cfg);
      const limit = Math.min(input.limit ?? 50, 100);
      const followers = scan.follows
        .filter((f) => f.subject === input.actor)
        .slice(0, limit)
        .map((f) => profileRowToView(f.follower, scan.profiles));
      return {
        subject: profileRowToView(input.actor, scan.profiles),
        followers,
        cursor: undefined,
      };
    } catch {
      // fall through to empty
    }
  }
  return {
    followers: [],
    cursor: undefined,
  };
}

export async function getFollows(
  e: Etzhayyim,
  input: GetFollowsInput
): Promise<GetFollowsOutput> {
  const cfg = getKotobaCfg(e);
  if (cfg) {
    try {
      const scan = await scanYoro(cfg);
      const limit = Math.min(input.limit ?? 50, 100);
      const follows = scan.follows
        .filter((f) => f.follower === input.actor)
        .slice(0, limit)
        .map((f) => profileRowToView(f.subject, scan.profiles));
      return {
        subject: profileRowToView(input.actor, scan.profiles),
        follows,
        cursor: undefined,
      };
    } catch {
      // fall through to empty
    }
  }
  return {
    follows: [],
    cursor: undefined,
  };
}

export async function getProfile(
  e: Etzhayyim,
  input: GetProfileInput
): Promise<GetProfileOutput> {
  const cfg = getKotobaCfg(e);
  if (cfg) {
    try {
      const scan = await scanYoro(cfg);
      if (scan.profiles.has(input.actor) || scan.posts.length) {
        const profile = profileRowToView(input.actor, scan.profiles);
        // Derive postsCount for the actor from the feed.
        profile.postsCount = scan.posts.filter(
          (p) => p.author === input.actor,
        ).length;
        profile.followsCount = scan.follows.filter(
          (f) => f.follower === input.actor,
        ).length;
        profile.followersCount = scan.follows.filter(
          (f) => f.subject === input.actor,
        ).length;
        return { profile };
      }
    } catch {
      // fall through to not-found
    }
  }
  return {
    profile: undefined,
    error: "not found",
  };
}

export async function searchActors(
  e: Etzhayyim,
  input?: SearchActorsInput
): Promise<SearchActorsOutput> {
  const cfg = getKotobaCfg(e);
  if (cfg) {
    try {
      const scan = await scanYoro(cfg);
      const q = (input?.q ?? "").toLowerCase().trim();
      const limit = Math.min(input?.limit ?? 25, 100);
      let actors = [...scan.profiles.values()];
      if (q) {
        actors = actors.filter(
          (p) =>
            p.did.toLowerCase().includes(q) ||
            (p.handle ?? "").toLowerCase().includes(q) ||
            (p.displayName ?? "").toLowerCase().includes(q) ||
            (p.description ?? "").toLowerCase().includes(q),
        );
      }
      return {
        actors: actors
          .slice(0, limit)
          .map((p) => profileRowToView(p.did, scan.profiles)),
        cursor: undefined,
      };
    } catch {
      // fall through to empty
    }
  }
  return {
    actors: [],
    cursor: undefined,
  };
}
