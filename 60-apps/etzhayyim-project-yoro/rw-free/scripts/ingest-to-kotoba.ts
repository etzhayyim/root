#!/usr/bin/env -S npx tsx
//
// ingest-to-kotoba.ts — pull etzhayyim member atproto repos and write them into
// the kotoba canonical Datom log as `:yoro/*` Datoms (ADR-2606013200).
//
// Source : etzhayyim PDS (atproto.etzhayyim.com) member repos.
// Records: app.bsky.feed.post / app.bsky.graph.follow / app.bsky.actor.profile.
// Sink   : kotoba `datomic.transact` into the dedicated `yoro-social-v1` graph,
//          keyed by unique-identity attributes so re-runs upsert in place.
//
// Scope (ADR-2606013200): etzhayyim-internal content only. The reader is
// `@etzhayyim/yoro-rw-free` (src/kotoba.ts) over the same graph.
//
// Usage:
//   KOTOBA_OPERATOR_DID=did:key:ze2e... \
//   [KOTOBA_URL=http://127.0.0.1:8077] [PDS_URL=https://atproto.etzhayyim.com] \
//   npx tsx scripts/ingest-to-kotoba.ts did:web:yoro.etzhayyim.com [more dids...]
//
// The operator DID is the kotoba node identity (see `serve.log` startup line
// `did=did:key:...`). The write bearer is a JWT whose `sub` equals it — kotoba
// checks `sub == operator_did` and the `exp` claim; it does NOT verify the
// signature (current dev posture). No operator private key is required or used.

import { DEFAULT_YORO_GRAPH_CID } from "../src/kotoba.js";

const KOTOBA_URL = (process.env.KOTOBA_URL ?? "http://127.0.0.1:8077").replace(
  /\/+$/,
  "",
);
const PDS_URL = (process.env.PDS_URL ?? "https://atproto.etzhayyim.com").replace(
  /\/+$/,
  "",
);
const GRAPH = process.env.YORO_GRAPH_CID ?? DEFAULT_YORO_GRAPH_CID;
const OPERATOR_DID = process.env.KOTOBA_OPERATOR_DID ?? "";

const TRANSACT_NSID = "com.etzhayyim.apps.kotoba.datomic.transact";
const MAX_TX_BYTES = 900 * 1024; // stay under the server's 1 MiB tx_edn cap

function die(msg: string): never {
  console.error(`ingest-to-kotoba: ${msg}`);
  process.exit(1);
}

// ── operator bearer (sub == operator_did, signature unverified) ──────────
function b64url(s: string): string {
  return Buffer.from(s).toString("base64url");
}
function operatorBearer(): string {
  if (!OPERATOR_DID) {
    die(
      "KOTOBA_OPERATOR_DID is required (the kotoba node DID from serve.log `did=...`)",
    );
  }
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = b64url(JSON.stringify({ sub: OPERATOR_DID, exp: 9999999999 }));
  return `${header}.${payload}.unsigned`;
}

// ── EDN encoding ─────────────────────────────────────────────────────────
// EDN strings share JSON's double-quote + backslash escaping for our content.
function ednStr(v: unknown): string {
  return JSON.stringify(v == null ? "" : String(v));
}
function ednMap(pairs: Array<[string, string]>): string {
  return `{${pairs.map(([k, v]) => `${k} ${v}`).join(" ")}}`;
}

// ── PDS read ─────────────────────────────────────────────────────────────
interface RepoRecord {
  uri: string;
  cid: string;
  value: Record<string, unknown>;
}

async function listRecords(
  repo: string,
  collection: string,
  limit = 100,
): Promise<RepoRecord[]> {
  const url = `${PDS_URL}/xrpc/com.atproto.repo.listRecords?repo=${encodeURIComponent(
    repo,
  )}&collection=${encodeURIComponent(collection)}&limit=${limit}`;
  try {
    const r = await fetch(url);
    if (!r.ok) {
      console.warn(`  ${collection}: PDS ${r.status} (skipping)`);
      return [];
    }
    const j = (await r.json()) as { records?: RepoRecord[] };
    return j.records ?? [];
  } catch (err) {
    console.warn(
      `  ${collection}: PDS unreachable (${
        err instanceof Error ? err.message : String(err)
      })`,
    );
    return [];
  }
}

// ── entity → EDN map builders ────────────────────────────────────────────
function didFromUri(uri: string): string {
  const m = uri.match(/^at:\/\/([^/]+)\//);
  return m ? m[1] : "did:web:unknown";
}

function postEntity(rec: RepoRecord): string {
  const v = rec.value;
  const reply = v.reply as
    | { parent?: { uri?: string }; root?: { uri?: string } }
    | undefined;
  const pairs: Array<[string, string]> = [
    [":db/id", ednStr(rec.uri)],
    [":yoro.post/uri", ednStr(rec.uri)],
    [":yoro.post/cid", ednStr(rec.cid)],
    [":yoro.post/author", ednStr(didFromUri(rec.uri))],
    [":yoro.post/text", ednStr((v.text as string) ?? "")],
    [
      ":yoro.post/createdAt",
      ednStr((v.createdAt as string) ?? new Date(0).toISOString()),
    ],
    [":yoro.post/record", ednStr(JSON.stringify(v))],
  ];
  if (reply?.parent?.uri)
    pairs.push([":yoro.post/replyParent", ednStr(reply.parent.uri)]);
  if (reply?.root?.uri)
    pairs.push([":yoro.post/replyRoot", ednStr(reply.root.uri)]);
  return ednMap(pairs);
}

function followEntity(rec: RepoRecord): string {
  const v = rec.value;
  return ednMap([
    [":db/id", ednStr(rec.uri)],
    [":yoro.follow/uri", ednStr(rec.uri)],
    [":yoro.follow/follower", ednStr(didFromUri(rec.uri))],
    [":yoro.follow/subject", ednStr((v.subject as string) ?? "")],
    [":yoro.follow/createdAt", ednStr((v.createdAt as string) ?? "")],
  ]);
}

function profileEntity(did: string, rec: RepoRecord): string {
  const v = rec.value;
  const pairs: Array<[string, string]> = [
    [":db/id", ednStr(did)],
    [":yoro.profile/did", ednStr(did)],
    [
      ":yoro.profile/handle",
      ednStr(
        did.startsWith("did:web:")
          ? did.slice("did:web:".length).replace(/:/g, ".")
          : did,
      ),
    ],
  ];
  if (v.displayName)
    pairs.push([":yoro.profile/displayName", ednStr(v.displayName)]);
  if (v.description)
    pairs.push([":yoro.profile/description", ednStr(v.description)]);
  const avatarRef = (v.avatar as { ref?: { $link?: string } } | undefined)?.ref
    ?.$link;
  if (avatarRef) pairs.push([":yoro.profile/avatar", ednStr(avatarRef)]);
  return ednMap(pairs);
}

// ── kotoba transact ──────────────────────────────────────────────────────
async function transact(txEdn: string, bearer: string): Promise<void> {
  const r = await fetch(`${KOTOBA_URL}/xrpc/${TRANSACT_NSID}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${bearer}`,
    },
    body: JSON.stringify({ graph: GRAPH, tx_edn: txEdn }),
  });
  const body = await r.text();
  if (!r.ok) {
    die(`transact → ${r.status}: ${body.slice(0, 300)}`);
  }
}

// Transact a list of EDN entity maps, chunked under the tx_edn size cap.
async function transactEntities(
  entities: string[],
  bearer: string,
): Promise<void> {
  let buf: string[] = [];
  let size = 0;
  const flush = async () => {
    if (!buf.length) return;
    await transact(`[${buf.join(" ")}]`, bearer);
    buf = [];
    size = 0;
  };
  for (const ent of entities) {
    if (size + ent.length > MAX_TX_BYTES && buf.length) await flush();
    buf.push(ent);
    size += ent.length + 1;
  }
  await flush();
}

const SCHEMA_TX =
  "[" +
  [
    '{:db/id ":yoro.post/uri" :db/ident :yoro.post/uri :db/unique :db.unique/identity}',
    '{:db/id ":yoro.profile/did" :db/ident :yoro.profile/did :db/unique :db.unique/identity}',
    '{:db/id ":yoro.follow/uri" :db/ident :yoro.follow/uri :db/unique :db.unique/identity}',
  ].join(" ") +
  "]";

async function main(): Promise<void> {
  const dids = process.argv.slice(2);
  if (dids.length === 0) dids.push("did:web:yoro.etzhayyim.com");
  const bearer = operatorBearer();

  console.log(`ingest-to-kotoba`);
  console.log(`  kotoba : ${KOTOBA_URL}`);
  console.log(`  pds    : ${PDS_URL}`);
  console.log(`  graph  : ${GRAPH}`);
  console.log(`  members: ${dids.join(", ")}`);

  // 1) schema install (idempotent — re-asserting identity attrs is a no-op).
  await transact(SCHEMA_TX, bearer);
  console.log(`  schema : installed`);

  let totalPosts = 0;
  let totalFollows = 0;
  let totalProfiles = 0;

  for (const did of dids) {
    console.log(`\n[${did}]`);
    const entities: string[] = [];

    const posts = await listRecords(did, "app.bsky.feed.post");
    for (const rec of posts) entities.push(postEntity(rec));
    totalPosts += posts.length;
    console.log(`  posts  : ${posts.length}`);

    const follows = await listRecords(did, "app.bsky.graph.follow");
    for (const rec of follows) entities.push(followEntity(rec));
    totalFollows += follows.length;
    console.log(`  follows: ${follows.length}`);

    const profiles = await listRecords(did, "app.bsky.actor.profile", 1);
    if (profiles.length) {
      entities.push(profileEntity(did, profiles[0]));
      totalProfiles += 1;
    }
    console.log(`  profile: ${profiles.length ? "yes" : "—"}`);

    if (entities.length) await transactEntities(entities, bearer);
  }

  console.log(
    `\ndone: ${totalPosts} posts, ${totalFollows} follows, ${totalProfiles} profiles → ${GRAPH}`,
  );
}

main().catch((e) => die(e instanceof Error ? e.stack ?? e.message : String(e)));
