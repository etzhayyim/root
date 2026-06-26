// Tests for the XRPC NSID→upstream routing + Method A cutover fallback.
//
//   node --test scripts/xrpc-routes.test.mjs
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
let findXrpcRoute, resolveUpstream;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `xrpc-routes-${hash}.mjs`);
  await esbuild.build({
    entryPoints: [join(HERE, "../src/xrpc-routes.ts")],
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
  });
  ({ findXrpcRoute, resolveUpstream } = await import(`${out}?t=${Date.now()}`));
});

const APPVIEW = "https://atproto.etzhayyim.com";
const PDS = "https://pds.etzhayyim.com";

test("repo.* and sync.* route to the PDS upstream (more specific, first match)", () => {
  assert.equal(findXrpcRoute("com.atproto.repo.createRecord").upstream, "XRPC_PDS_UPSTREAM");
  assert.equal(findXrpcRoute("com.atproto.repo.getRecord").upstream, "XRPC_PDS_UPSTREAM");
  assert.equal(findXrpcRoute("com.atproto.sync.getRepo").upstream, "XRPC_PDS_UPSTREAM");
});

test("the rest of com.atproto.* and app.bsky.* stay on the AppView upstream", () => {
  assert.equal(findXrpcRoute("com.atproto.server.createSession").upstream, "XRPC_ATPROTO_UPSTREAM");
  assert.equal(findXrpcRoute("com.atproto.identity.resolveHandle").upstream, "XRPC_ATPROTO_UPSTREAM");
  assert.equal(findXrpcRoute("app.bsky.feed.getTimeline").upstream, "XRPC_ATPROTO_UPSTREAM");
  assert.equal(findXrpcRoute("app.bsky.actor.getProfile").upstream, "XRPC_ATPROTO_UPSTREAM");
});

test("other families are unaffected", () => {
  assert.equal(findXrpcRoute("com.etzhayyim.apps.kotoba.kg.query").upstream, "XRPC_KOTOBA_UPSTREAM");
  assert.equal(findXrpcRoute("chat.bsky.convo.listConvos").upstream, "XRPC_CHAT_UPSTREAM");
  assert.equal(findXrpcRoute("com.etzhayyim.signal.x").upstream, "XRPC_etzhayyim_UPSTREAM");
  assert.equal(findXrpcRoute("nope.unknown.method"), null);
});

test("INERT until cutover: with XRPC_PDS_UPSTREAM empty, repo/sync fall back to AppView", () => {
  const route = findXrpcRoute("com.atproto.repo.createRecord");
  const env = { XRPC_ATPROTO_UPSTREAM: APPVIEW, XRPC_PDS_UPSTREAM: "" };
  // empty PDS env → byte-identical to today (AppView upstream)
  assert.equal(resolveUpstream(route, env), APPVIEW);
  assert.equal(resolveUpstream(route, { XRPC_ATPROTO_UPSTREAM: APPVIEW }), APPVIEW); // unset too
});

test("CUTOVER: with XRPC_PDS_UPSTREAM set, repo/sync go to the independent PDS", () => {
  const route = findXrpcRoute("com.atproto.sync.getRepo");
  const env = { XRPC_ATPROTO_UPSTREAM: APPVIEW, XRPC_PDS_UPSTREAM: PDS };
  assert.equal(resolveUpstream(route, env), PDS);
});

test("non-fallback routes return undefined when their upstream is empty (→ 503)", () => {
  const route = findXrpcRoute("app.bsky.feed.getTimeline"); // no fallback
  assert.equal(resolveUpstream(route, { XRPC_ATPROTO_UPSTREAM: "" }), undefined);
  assert.equal(resolveUpstream(route, {}), undefined);
});
