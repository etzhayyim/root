import { Lexicons } from "/Users/junkawasaki/github/ai-gftd-apps-gftdcojp/node_modules/.pnpm/@atproto+lexicon@0.4.14/node_modules/@atproto/lexicon/dist/index.js";
import { XrpcClient } from "/Users/junkawasaki/github/ai-gftd-apps-gftdcojp/node_modules/.pnpm/@atproto+xrpc@0.7.7/node_modules/@atproto/xrpc/dist/index.js";
import { readFileSync } from "node:fs";

const docs = JSON.parse(readFileSync("/Users/junkawasaki/github/ai-gftd-apps-gftdcojp/10-protocol/lexicons-bundle/src/lexicons.gen.json", "utf8"));
const lex = new Lexicons(docs);
console.log(`[lex] loaded ${docs.length} docs`);

const client = new XrpcClient({ service: "https://atproto.gftd.ai" }, lex);

// 1. com.atproto.identity.resolveHandle (well-known stable)
try {
  const res = await client.call("com.atproto.identity.resolveHandle", { handle: "yoro.gftd.ai" });
  console.log("[ok] resolveHandle yoro.gftd.ai →", res.data);
} catch (e) {
  console.error("[err] resolveHandle:", e.message ?? e);
}

// 2. com.atproto.server.describeServer (no DB lookup, validator coverage on com.atproto)
try {
  const res = await client.call("com.atproto.server.describeServer", {});
  console.log("[ok] describeServer →", JSON.stringify(res.data).slice(0, 200));
} catch (e) {
  console.error("[err] describeServer:", e.message ?? e);
}

// 3. app.bsky.actor.getProfile (Maps actor that previously triggered fallback)
try {
  const res = await client.call("app.bsky.actor.getProfile", { actor: "did:web:uqpel6i6.gftd.ai" });
  console.log("[ok] getProfile uqpel6i6 → did=" + res.data.did + " followsCount=" + res.data.followsCount + " postsCount=" + res.data.postsCount);
} catch (e) {
  console.error("[err] getProfile uqpel6i6:", e.message ?? e);
}

// 4. app.bsky.feed.getAuthorFeed
try {
  const res = await client.call("app.bsky.feed.getAuthorFeed", { actor: "did:web:uqpel6i6.gftd.ai", limit: 5 });
  console.log("[ok] getAuthorFeed uqpel6i6 → " + (res.data.feed?.length ?? 0) + " items");
} catch (e) {
  console.error("[err] getAuthorFeed uqpel6i6:", e.message ?? e);
}

// 5. ai.gftd.apps.yoro.health (no DB)
try {
  const res = await client.call("ai.gftd.apps.yoro.health", {});
  console.log("[ok] yoro.health →", JSON.stringify(res.data));
} catch (e) {
  console.error("[err] yoro.health:", e.message ?? e);
}
