// Node test for src/xrpc-cache.ts — the anonymous read-path edge-cache policy
// added to fix the multi-second "vibes" feed render (AppView reads cost
// 2.8–5.2s; we cache anonymous public reads at the CF edge). Verifies WHAT gets
// cached (only anonymous public-read GETs) and that the cache key is shared
// across visitors but split per query.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  isAnonymousReadXrpc,
  xrpcCacheKey,
  CACHEABLE_READ_NSIDS,
  XRPC_CACHE_CONTROL,
} from '../src/xrpc-cache.ts';

const req = (url, { method = 'GET', headers = {} } = {}) =>
  new Request(url, { method, headers });

test('anonymous GET for a public read NSID is cacheable', () => {
  const r = req('https://etzhayyim.com/xrpc/app.bsky.feed.getFeed?limit=30');
  assert.equal(isAnonymousReadXrpc(r, 'app.bsky.feed.getFeed'), true);
  assert.equal(isAnonymousReadXrpc(r, 'app.bsky.actor.getProfile'), true);
});

test('authenticated requests are NEVER cached (privacy — personalized views)', () => {
  const auth = req('https://etzhayyim.com/xrpc/app.bsky.feed.getTimeline', {
    headers: { authorization: 'Bearer x' },
  });
  assert.equal(isAnonymousReadXrpc(auth, 'app.bsky.feed.getTimeline'), false);
  const dpop = req('https://etzhayyim.com/xrpc/app.bsky.feed.getTimeline', {
    headers: { dpop: 'eyJ...' },
  });
  assert.equal(isAnonymousReadXrpc(dpop, 'app.bsky.feed.getTimeline'), false);
});

test('non-GET (writes, HEAD) are not cached', () => {
  for (const method of ['POST', 'HEAD', 'PUT', 'DELETE']) {
    const r = req('https://etzhayyim.com/xrpc/app.bsky.feed.getFeed', { method });
    assert.equal(isAnonymousReadXrpc(r, 'app.bsky.feed.getFeed'), false, method);
  }
});

test('unknown / write / non-public NSIDs are not cached', () => {
  const r = req('https://etzhayyim.com/xrpc/app.bsky.feed.post');
  assert.equal(isAnonymousReadXrpc(r, 'app.bsky.feed.post'), false);
  assert.equal(isAnonymousReadXrpc(r, 'com.atproto.repo.createRecord'), false);
  assert.equal(isAnonymousReadXrpc(r, 'app.bsky.graph.getFollows'), false);
});

test('cache key is shared across clients but split per URL/query', () => {
  // Two anonymous visitors hitting the same feed → identical key (shared entry).
  const a = xrpcCacheKey(
    req('https://etzhayyim.com/xrpc/app.bsky.feed.getFeed?limit=30', {
      headers: { 'user-agent': 'A', cookie: 'x=1' },
    }),
  );
  const b = xrpcCacheKey(
    req('https://etzhayyim.com/xrpc/app.bsky.feed.getFeed?limit=30', {
      headers: { 'user-agent': 'B' },
    }),
  );
  assert.equal(a.url, b.url);
  assert.equal(a.method, 'GET');
  // client headers must NOT ride along on the key (no fragmentation/poisoning).
  assert.equal(a.headers.has('user-agent'), false);
  assert.equal(a.headers.has('cookie'), false);

  // Different query (cursor/limit) → distinct entry.
  const c = xrpcCacheKey(
    req('https://etzhayyim.com/xrpc/app.bsky.feed.getFeed?limit=30&cursor=z'),
  );
  assert.notEqual(a.url, c.url);
});

test('cache-control advertises edge TTL + stale-while-revalidate', () => {
  assert.match(XRPC_CACHE_CONTROL, /public/);
  assert.match(XRPC_CACHE_CONTROL, /s-maxage=\d+/);
  assert.match(XRPC_CACHE_CONTROL, /stale-while-revalidate=\d+/);
});

test('the public read set covers the feed + profile NSIDs the SPA awaits', () => {
  for (const nsid of [
    'app.bsky.feed.getFeed',
    'app.bsky.feed.getTimeline',
    'app.bsky.actor.getProfile',
  ]) {
    assert.ok(CACHEABLE_READ_NSIDS.has(nsid), nsid);
  }
});
