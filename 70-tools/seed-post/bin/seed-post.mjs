#!/usr/bin/env node
// etzhayyim-seed-post — Step 1 of kotoba-datomic-based post display.
//
// Writes an `app.bsky.feed.post` record into the operator DID's MST so
// the substrate read path (yoro-xrpc-adapter → @etzhayyim/sdk read →
// pds.etzhayyim.com) returns a non-empty feed.
//
// Per:
//   - ADR-2605172000 (kotoba substrate)
//   - ADR-2605262130 + 90-docs/provenance/archives/kotoba-datomic.edn
//   - ADR-2605231525 (member wallet / member passkey-derived ES256 only;
//     no platform-held private key — this CLI is operator-local, the
//     PDS app-password lives in the operator's macOS Keychain).
//
// Auth: app-password via env PDS_HANDLE + PDS_APP_PASSWORD (loaded by the
// wrapper from Keychain). Falls back to resumable session via
// ETZ_PROJECTOR_PDS_SESSION JSON (matches mst-projector/emit.ts shape).

import { AtpAgent } from "@atproto/api";

// Default tracks `did:web:yoro.etzhayyim.com`'s DID document
// (service[type=AtprotoPersonalDataServer]). Override with `PDS_URL=...`
// when seeding into the religious-corp pds.etzhayyim.com post-cutover.
const PDS_URL = process.env.PDS_URL ?? "https://atproto.etzhayyim.com";
const ACTOR_DID =
  process.env.ACTOR_DID ?? "did:web:yoro.etzhayyim.com";
const TEXT =
  process.argv.slice(2).join(" ") ||
  process.env.SEED_POST_TEXT ||
  "hello kotoba-datomic — first post on the kotoba substrate. " +
    "MST → IPFS → L2 anchor. ADR-2605172000.";

const collection = "app.bsky.feed.post";

function die(msg, extra) {
  process.stderr.write(`[seed-post] ERROR: ${msg}\n`);
  if (extra) process.stderr.write(`${extra}\n`);
  process.exit(1);
}

async function authedAgent() {
  const agent = new AtpAgent({ service: PDS_URL });
  const sessJson = process.env.ETZ_PROJECTOR_PDS_SESSION;
  if (sessJson) {
    const s = JSON.parse(sessJson);
    await agent.resumeSession({
      did: s.did,
      handle: s.handle,
      accessJwt: s.accessJwt,
      refreshJwt: s.refreshJwt,
      active: true,
    });
    return agent;
  }
  const handle = process.env.PDS_HANDLE;
  const password = process.env.PDS_APP_PASSWORD;
  if (!handle || !password) {
    die(
      "no auth configured",
      "set PDS_HANDLE + PDS_APP_PASSWORD, or ETZ_PROJECTOR_PDS_SESSION (JSON: did/handle/accessJwt/refreshJwt). " +
        "macOS users: ./bin/seed-post.sh wraps the Keychain lookup.",
    );
  }
  try {
    await agent.login({ identifier: handle, password });
  } catch (err) {
    die(`login failed for ${handle}`, err?.message ?? String(err));
  }
  return agent;
}

async function main() {
  const agent = await authedAgent();
  const repo = agent.session?.did ?? ACTOR_DID;

  const record = {
    $type: collection,
    text: TEXT,
    createdAt: new Date().toISOString(),
    langs: [/^[\x00-\x7f]+$/.test(TEXT) ? "en" : "ja"],
  };

  const created = await agent.com.atproto.repo.createRecord({
    repo,
    collection,
    record,
  });
  if (!created.success) die("createRecord failed", JSON.stringify(created));

  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        repo,
        uri: created.data.uri,
        cid: created.data.cid,
        text: TEXT,
        pds: PDS_URL,
        verify:
          `curl -s '${PDS_URL}/xrpc/com.atproto.repo.listRecords?repo=${encodeURIComponent(
            repo,
          )}&collection=${collection}&limit=1' | jq` +
          " && curl -s 'https://etzhayyim.com/xrpc/app.bsky.feed.getTimeline?limit=5' | jq",
      },
      null,
      2,
    ) + "\n",
  );

  const verify = await agent.com.atproto.repo.listRecords({
    repo,
    collection,
    limit: 1,
  });
  if (!verify.success || verify.data.records.length === 0) {
    process.stderr.write(
      "[seed-post] WARN: createRecord returned success but verify listRecords saw 0 records (possible PDS replication lag)\n",
    );
  }
}

main().catch((err) => {
  die("unhandled", err?.stack ?? String(err));
});
