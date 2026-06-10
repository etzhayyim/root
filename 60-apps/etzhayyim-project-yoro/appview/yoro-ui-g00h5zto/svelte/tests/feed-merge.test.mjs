// Unit test for the kotoba-sw.js NETWORK-FIRST feed merge (feed-merge.js).
// Run: node tests/feed-merge.test.mjs
import assert from "node:assert/strict";
import { mergeLiveFeed } from "../public/kotoba/feed-merge.js";

const post = (uri, at, did = "did:web:etzhayyim.com") => ({
  uri,
  indexedAt: at,
  record: { createdAt: at },
  author: { did, handle: did },
});
const item = (uri, at, did) => ({ post: post(uri, at, did) });

// 1) No local views → pass live through untouched (null).
assert.equal(
  mergeLiveFeed({ feed: [item("at://a/1", "2026-06-10T00:00:00Z")] }, []),
  null,
  "empty local → passthrough",
);

// 2) Later cursor pages → pass through untouched even with local views.
assert.equal(
  mergeLiveFeed(
    { feed: [item("at://a/1", "2026-06-10T00:00:00Z")], cursor: "abc" },
    [post("at://local/1", "2026-06-11T00:00:00Z", "did:key:zMember")],
    { hasCursor: true },
  ),
  null,
  "cursor page → passthrough",
);

// 3) Stale seed posts (did:web authors) are NOT backfilled — the live page
//    stays canonical, no re-appended history.
assert.equal(
  mergeLiveFeed({ feed: [item("at://a/1", "2026-06-10T00:00:00Z")] }, [
    post("at://seed/old", "2026-06-01T00:00:00Z", "did:web:etzhayyim.com"),
  ]),
  null,
  "seed-only local → passthrough",
);

// 4) Member-signed local write (did:key) the server lacks IS backfilled,
//    sorted newest-first, live cursor preserved.
{
  const m = mergeLiveFeed(
    { feed: [item("at://a/1", "2026-06-10T00:00:00Z")], cursor: "next" },
    [post("at://local/new", "2026-06-11T00:00:00Z", "did:key:zMember")],
  );
  assert.ok(m, "member write → merged");
  assert.equal(m.feed.length, 2);
  assert.equal(m.feed[0].post.uri, "at://local/new", "local write sorts first (newest)");
  assert.equal(m.cursor, "next", "live cursor preserved");
}

// 5) Already-indexed member write is deduped by uri (no double entry).
{
  const m = mergeLiveFeed(
    { feed: [item("at://local/new", "2026-06-11T00:00:00Z", "did:key:zMember")] },
    [post("at://local/new", "2026-06-11T00:00:00Z", "did:key:zMember")],
  );
  assert.equal(m, null, "deduped → passthrough");
}

// 6) Live post with a BLANK author (AppView discover hydration bug) is
//    upgraded to the local view of the same post, which carries the author.
{
  const blank = {
    post: { uri: "at://a/1", indexedAt: "2026-06-10T00:00:00Z", author: { did: "", handle: "" } },
  };
  const m = mergeLiveFeed({ feed: [blank] }, [
    post("at://a/1", "2026-06-10T00:00:00Z", "did:web:etzhayyim.com:actor:danjo"),
  ]);
  assert.ok(m, "blank author → upgraded");
  assert.equal(m.feed[0].post.author.did, "did:web:etzhayyim.com:actor:danjo");
}

console.log("feed-merge.test.mjs: 6/6 OK");
