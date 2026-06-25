// Tests for apex home/discover feed curation (ADR-2606232130).
//
//   node --experimental-strip-types --test scripts/feed-curation.test.mjs
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
let curateFeed, isQuarantinedAuthor, isOwnActor, CURATED_FEED_NSIDS;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `feed-curation-${hash}.mjs`);
  await esbuild.build({
    entryPoints: [join(HERE, "../src/feed-curation.ts")],
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
  });
  ({ curateFeed, isQuarantinedAuthor, isOwnActor, CURATED_FEED_NSIDS } = await import(
    `${out}?t=${Date.now()}`
  ));
});

const item = (did, handle) => ({ post: { author: { did, handle }, text: "x" } });

test("only aggregate feeds are curated (author feed / thread are not)", () => {
  assert.ok(CURATED_FEED_NSIDS.has("app.bsky.feed.getTimeline"));
  assert.ok(CURATED_FEED_NSIDS.has("app.bsky.feed.getDiscoverFeed"));
  assert.equal(CURATED_FEED_NSIDS.has("app.bsky.feed.getAuthorFeed"), false);
  assert.equal(CURATED_FEED_NSIDS.has("app.bsky.feed.getPostThread"), false);
});

test("quarantines the EXCLUDE'd external poster (shinshi) by did or handle", () => {
  assert.ok(isQuarantinedAuthor({ did: "did:web:shinshi.etzhayyim.com" }));
  assert.ok(isQuarantinedAuthor({ handle: "sh1n5h1x.etzhayyim.com" }));
  assert.equal(isQuarantinedAuthor({ did: "did:web:etzhayyim.com" }), false);
  assert.equal(isQuarantinedAuthor({ handle: "tsumugi.etzhayyim.com" }), false);
});

test("quarantines the LIVE gftd.ai shinshi poster (drop the gftd.ai dependency)", () => {
  // the actual flooding author observed on prod is did:web:sh1n5h1x.gftd.ai
  assert.ok(isQuarantinedAuthor({ did: "did:web:sh1n5h1x.gftd.ai" }));
  assert.ok(isQuarantinedAuthor({ handle: "sh1n5h1x.gftd.ai" }));
  assert.ok(isQuarantinedAuthor({ did: "did:web:shinshi.gftd.ai" }));
  // a gftd.ai poster is never treated as one of etzhayyim's own actors
  assert.equal(isOwnActor({ did: "did:web:sh1n5h1x.gftd.ai" }), false);
  // an unrelated gftd.ai entity is NOT swept up (only the shinshi family)
  assert.equal(isQuarantinedAuthor({ did: "did:web:atproto.gftd.ai" }), false);
});

test("own actors = root / agents / mirrors, but NOT the quarantined external", () => {
  assert.ok(isOwnActor({ did: "did:web:etzhayyim.com" }));
  assert.ok(isOwnActor({ did: "did:web:etzhayyim.com:actor:tsumugi" }));
  assert.ok(isOwnActor({ handle: "kaname.etzhayyim.com" }));
  assert.equal(isOwnActor({ did: "did:web:shinshi.etzhayyim.com" }), false, "quarantined is not 'own'");
  assert.equal(isOwnActor({ handle: "alice.bsky.social" }), false);
});

test("curateFeed drops shinshi and boosts own actors, preserving recency within groups", () => {
  const body = {
    cursor: "c1",
    feed: [
      item("did:web:shinshi.etzhayyim.com", "sh1n5h1x.etzhayyim.com"), // dropped
      item("did:plc:ext1", "alice.bsky.social"), // external human, kept (not quarantined)
      item("did:web:etzhayyim.com:actor:tsumugi", "tsumugi.etzhayyim.com"), // own → front
      item("did:web:shinshi.etzhayyim.com", "sh1n5h1x.etzhayyim.com"), // dropped
      item("did:web:etzhayyim.com", "etzhayyim.com"), // own root → front (after tsumugi)
      item("did:plc:ext2", "bob.bsky.social"), // external, kept
    ],
  };
  const out = curateFeed(body);
  const handles = out.feed.map((i) => i.post.author.handle);
  // no shinshi
  assert.equal(out.feed.some((i) => i.post.author.did.includes("shinshi")), false);
  // own actors first, in original relative order (tsumugi before root)
  assert.deepEqual(handles, [
    "tsumugi.etzhayyim.com",
    "etzhayyim.com",
    "alice.bsky.social",
    "bob.bsky.social",
  ]);
  // cursor + other fields preserved
  assert.equal(out.cursor, "c1");
});

test("curateFeed is a no-op shape-wise when there is no feed array (fail-safe)", () => {
  assert.deepEqual(curateFeed({ error: "x" }), { error: "x" });
  assert.deepEqual(curateFeed({}), {});
});

test("opts can disable quarantine / boost independently", () => {
  const body = {
    feed: [
      item("did:web:shinshi.etzhayyim.com", "sh1n5h1x.etzhayyim.com"),
      item("did:web:etzhayyim.com", "etzhayyim.com"),
    ],
  };
  // boost only (keep shinshi)
  const a = curateFeed(body, { quarantine: false, boostOwn: true });
  assert.equal(a.feed.length, 2);
  assert.equal(a.feed[0].post.author.handle, "etzhayyim.com"); // own boosted to front
  // quarantine only (no reorder)
  const b = curateFeed(body, { quarantine: true, boostOwn: false });
  assert.equal(b.feed.length, 1);
  assert.equal(b.feed[0].post.author.handle, "etzhayyim.com");
});
