/**
 * Client-side feed/profile/search queries.
 *
 * Candidate C: $lib/atproto-agent connects to PDS (atproto.etzhayyim.com) with AT Protocol
 * standard NSIDs. PDS pipethroughs app.bsky.* reads to yoro AppView via service
 * binding. This wrapper adds timeline→discover fallback.
 */

import type { FeedItem, PostView } from "$lib/atproto-agent";
import * as api from "$lib/atproto-agent";
import * as store from "./kagami-store.svelte";

/** Optional accelerator warmup (non-blocking). */
export async function ensureLabelsLoaded(): Promise<void> {
  if (!store.isEnabled()) return;
  await Promise.all([
    store.loadLabel("Post", 10000),
    store.loadLabel("Profile", 5000),
    store.loadLabel("Follow", 10000),
  ]);
  store.setupPropertyGraph().catch((error) => {
    console.warn("[silent-fail] feed.ts: setupPropertyGraph failed", error);
  });
}

/** Get discover feed (app.bsky.feed.getDiscoverFeed → PDS → pipethrough → AppView). */
export async function getDiscoverFeed(opts: {
  limit?: number;
  cursor?: string;
}): Promise<{ feed: FeedItem[]; cursor?: string }> {
  return api.getDiscoverFeed({ limit: opts.limit ?? 30, cursor: opts.cursor, light: true });
}

/** Get personalized timeline (app.bsky.feed.getTimeline → PDS → pipethrough → AppView). */
export async function getTimeline(opts: {
  limit?: number;
  cursor?: string;
  userDid?: string;
}): Promise<{ feed: FeedItem[]; cursor?: string }> {
  try {
    return await api.getTimeline({ limit: opts.limit ?? 30, cursor: opts.cursor });
  } catch (e) {
    console.warn("[feed] timeline failed, falling back to discover:", e);
    return getDiscoverFeed(opts);
  }
}

/** Get author feed (app.bsky.feed.getAuthorFeed → PDS → pipethrough → AppView). */
export async function getAuthorFeed(
  did: string,
  opts: { limit?: number; cursor?: string },
): Promise<{ feed: FeedItem[]; cursor?: string }> {
  return api.getAuthorFeed(did, { limit: opts.limit ?? 30, cursor: opts.cursor });
}

/** Search posts (app.bsky.feed.searchPosts → PDS → pipethrough → AppView). */
export async function searchPosts(
  query: string,
  opts: { limit?: number },
): Promise<{ posts: PostView[] }> {
  const res = await api.searchPosts(query, { limit: opts.limit ?? 25 });
  return { posts: res.posts ?? [] };
}

/** Search actors (app.bsky.actor.searchActors → PDS → pipethrough → AppView). */
export async function searchActors(
  query: string,
  opts: { limit?: number },
): Promise<{ actors: any[]; totalActors?: number; cursor?: string }> {
  return api.searchActors(query, { limit: opts.limit ?? 25 }) as Promise<{ actors: any[]; totalActors?: number; cursor?: string }>;
}
