// Tests for the pure feed/profile + CRDT-merge logic the browser uses (the code
// that decides what users see and whether concurrent edits survive). Plain JS,
// no deps. Run: node --test tests/kotoba-feed.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  edVal,
  safeParse,
  actorMatches,
  buildPostViews,
  buildProfileView,
  mergeDatoms,
} from "../public/kotoba-feed.js";

// Datom builder mirroring the SW/seed encoding: v_edn = JSON.stringify(value).
const D = (e, a, value) => ({ e, a, v_edn: JSON.stringify(value), added: true });
function postDatoms(uri, { text = "", createdAt, author = "did:key:zauthor" } = {}) {
  const view = {
    uri,
    cid: uri,
    record: { $type: "app.bsky.feed.post", text, createdAt },
    author: { did: author, handle: author },
    likeCount: 0,
    repostCount: 0,
    text,
  };
  return [
    D(`post:${uri}`, ":yoro.post/uri", uri),
    D(`post:${uri}`, ":yoro.post/author", author),
    D(`post:${uri}`, ":yoro.post/createdAt", createdAt),
    D(`post:${uri}`, ":yoro.post/view", JSON.stringify(view)),
  ];
}

test("edVal / safeParse round-trip", () => {
  assert.equal(edVal(JSON.stringify("hi")), "hi");
  assert.equal(edVal("not-json"), "not-json");
  assert.deepEqual(safeParse(JSON.stringify({ a: 1 })), { a: 1 });
  assert.equal(safeParse("nope"), null);
  assert.deepEqual(safeParse({ already: "obj" }), { already: "obj" });
});

test("buildPostViews assembles posts, newest first", () => {
  const ds = [
    ...postDatoms("at://x/1", { text: "older", createdAt: "2026-01-01T00:00:00Z" }),
    ...postDatoms("at://x/2", { text: "newer", createdAt: "2026-06-01T00:00:00Z" }),
  ];
  const v = buildPostViews(ds);
  assert.equal(v.length, 2);
  assert.equal(v[0].uri, "at://x/2", "newest first");
  assert.equal(v[0].record.text, "newer");
  assert.ok(!("__sortAt" in v[0]), "scratch sort key stripped");
});

test("buildPostViews derives like/repost counts from the append-only log", () => {
  const ds = [
    ...postDatoms("at://x/1", { createdAt: "2026-06-01T00:00:00Z" }),
    D("like:a", ":yoro.like/subject", "at://x/1"),
    D("like:b", ":yoro.like/subject", "at://x/1"),
    D("rp:a", ":yoro.repost/subject", "at://x/1"),
  ];
  const v = buildPostViews(ds);
  assert.equal(v[0].likeCount, 2, "two likes counted from datoms");
  assert.equal(v[0].repostCount, 1, "one repost counted from datoms");
});

test("buildPostViews ignores malformed/incomplete posts", () => {
  const ds = [
    { e: "post:bad", a: ":yoro.post/uri", v_edn: "at://x/9" }, // no view
    ...postDatoms("at://x/ok", { createdAt: "2026-06-01T00:00:00Z" }),
  ];
  const v = buildPostViews(ds);
  assert.equal(v.length, 1);
  assert.equal(v[0].uri, "at://x/ok");
});

test("mergeDatoms is a dedup union (CRDT) — idempotent & order-independent", () => {
  const a = [D("e1", ":yoro.post/uri", "u1"), D("e1", ":yoro.post/author", "did")];
  const b = [D("e1", ":yoro.post/author", "did"), D("e2", ":yoro.post/uri", "u2")];
  const ab = mergeDatoms(a, b);
  assert.equal(ab.length, 3, "shared datom deduped");
  // idempotent
  assert.equal(mergeDatoms(ab, ab).length, 3);
  // order-independent set (same membership regardless of arg order)
  const ba = mergeDatoms(b, a);
  const key = (d) => `${d.e} ${d.a} ${d.v_edn}`;
  assert.deepEqual(new Set(ab.map(key)), new Set(ba.map(key)));
});

test("mergeDatoms preserves no-lost-update: both authors' posts survive", () => {
  const A = postDatoms("at://A/1", { author: "did:A", createdAt: "2026-06-01T00:00:00Z" });
  const B = postDatoms("at://B/1", { author: "did:B", createdAt: "2026-06-02T00:00:00Z" });
  const merged = mergeDatoms(A, B);
  const uris = buildPostViews(merged).map((v) => v.uri);
  assert.ok(uris.includes("at://A/1") && uris.includes("at://B/1"), "both edits present after merge");
});

test("buildProfileView resolves by handle or did, counts posts", () => {
  const ds = [
    D("p1", ":yoro.profile/did", "did:key:zwriter"),
    D("p1", ":yoro.profile/handle", "writer.example"),
    D("p1", ":yoro.profile/displayName", "Writer"),
    ...postDatoms("at://writer/1", { author: "did:key:zwriter", createdAt: "2026-06-01T00:00:00Z" }),
  ];
  const byHandle = buildProfileView(ds, "writer.example");
  assert.equal(byHandle.did, "did:key:zwriter");
  assert.equal(byHandle.postsCount, 1);
  const byDid = buildProfileView(ds, "did:key:zwriter");
  assert.equal(byDid.handle, "writer.example");
  assert.equal(buildProfileView(ds, "nobody"), null);
});

test("actorMatches matches did/handle, case-insensitive, substring", () => {
  const view = { author: { did: "did:key:zABC", handle: "alice.example" } };
  assert.equal(actorMatches(view, "did:key:zabc"), true);
  assert.equal(actorMatches(view, "alice.example"), true);
  assert.equal(actorMatches(view, "alice"), true);
  assert.equal(actorMatches(view, "bob"), false);
  assert.equal(actorMatches(view, ""), true, "empty wanted matches all");
});
