// feed-merge.js — pure merge of a LIVE server feed page with the local kotoba
// Datom-log post views (used by kotoba-sw.js). Dependency-free so it is
// unit-testable outside the Service Worker (node tests/feed-merge.test.mjs).
//
// Returns the merged { feed, cursor } body, or null when the live page should
// be passed through untouched (no local contribution).
export function mergeLiveFeed(liveBody, localViews, opts = {}) {
  const liveFeed = liveBody && Array.isArray(liveBody.feed) ? liveBody.feed : null;
  if (!liveFeed) return null;
  const views = Array.isArray(localViews) ? localViews : [];
  // Merge on the FIRST page only — later cursor pages pass through untouched
  // so server pagination stays consistent.
  if (opts.hasCursor || views.length === 0) return null;

  const localByUri = new Map(views.map((v) => [v.uri, v]));
  let changed = false;
  // The AppView's discover hydration can return posts with a blank author —
  // prefer the local view of the same post, which carries it.
  const upgraded = liveFeed.map((it) => {
    const p = it && it.post;
    if (p && p.uri && (!p.author || !p.author.did) && localByUri.has(p.uri)) {
      changed = true;
      return { ...it, post: localByUri.get(p.uri) };
    }
    return it;
  });

  const liveUris = new Set(liveFeed.map((it) => it && it.post && it.post.uri).filter(Boolean));
  // Backfill ONLY member-signed local writes (did:key authors) the server
  // hasn't indexed yet — NOT the whole seed snapshot, which would re-append
  // history into page 1 and duplicate later cursor pages.
  const localOnly = views
    .filter(
      (v) =>
        !liveUris.has(v.uri) &&
        v.author &&
        String(v.author.did || "").startsWith("did:key:"),
    )
    .map((v) => ({ post: v }));

  if (!changed && localOnly.length === 0) return null;

  const sortAt = (it) => {
    const p = it && it.post;
    return (p && (p.indexedAt || (p.record && p.record.createdAt))) || "";
  };
  const feed = [...upgraded, ...localOnly].sort((a, b) =>
    sortAt(b) < sortAt(a) ? -1 : sortAt(b) > sortAt(a) ? 1 : 0,
  );
  return { feed, cursor: liveBody.cursor ?? "" };
}
