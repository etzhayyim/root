// kotoba Datom-log read client for the yoro feed (ADR-2606013200).
//
// Reads the yoro-social graph back out of the kotoba canonical state via the
// generic `datomic.datoms` XRPC (`com.etzhayyim.apps.kotoba.datomic.datoms`), then
// shapes the `:yoro.post/* :yoro.profile/* :yoro.follow/*` Datoms into the rows
// the feed/graph/actor functions project into bsky-style views. This replaces
// the superseded kotoba-datomic-projection + single-actor PDS read leg
// (ADR-2605231500 → ADR-2605262130 / 2605312345). Schema SSoT:
// `00-contracts/schemas/yoro-feed-ontology.kotoba.edn`.
//
// Read auth: the yoro graph is registered Public at kotoba-server boot, so
// reads need no token. Falls back silently (callers degrade to PDS) on any
// network/parse error so a kotoba outage never 500s the feed.

import type { Etzhayyim } from "@etzhayyim/sdk";

/** Default yoro feed graph — `KotobaCid::from_bytes(b"yoro-social-v1")`. */
export const DEFAULT_YORO_GRAPH_CID =
  "bafyreibljg5gzye47fldkfq6m4vgy55kcjyez2vx432dubttou36g5yryq";

const DATOMS_NSID = "com.etzhayyim.apps.kotoba.datomic.datoms";

export interface KotobaCfg {
  url: string;
  graph: string;
}

export interface PostRow {
  entity: string;
  uri: string;
  cid: string;
  author: string;
  text: string;
  createdAt: string;
  /** Parsed app.bsky.feed.post record, when `:yoro.post/record` is present. */
  record?: Record<string, unknown>;
  replyParent?: string;
  replyRoot?: string;
}

export interface ProfileRow {
  did: string;
  handle?: string;
  displayName?: string;
  description?: string;
  avatar?: string;
}

export interface FollowRow {
  uri: string;
  follower: string;
  subject: string;
  createdAt: string;
}

export interface YoroScan {
  posts: PostRow[];
  profiles: Map<string, ProfileRow>;
  follows: FollowRow[];
}

interface KotobaDatom {
  e: string;
  a: string;
  v_edn: string;
  t: string;
  added: boolean;
}

/** Resolve kotoba config from the SDK instance, or null when unconfigured. */
export function getKotobaCfg(e: Etzhayyim): KotobaCfg | null {
  const c = (e as unknown as {
    config?: { kotobaUrl?: string; yoroGraphCid?: string };
  }).config;
  if (!c?.kotobaUrl) return null;
  return {
    url: c.kotobaUrl.replace(/\/+$/, ""),
    graph: c.yoroGraphCid || DEFAULT_YORO_GRAPH_CID,
  };
}

/**
 * Minimal EDN-scalar parser for the value types this schema uses: strings
 * (`"..."`), keywords (`:kw`), integers, booleans, nil. Falls back to the raw
 * token. Mirrors `kotoba_edn::to_string` output for scalars.
 */
export function parseEdnScalar(vEdn: string): unknown {
  const s = vEdn.trim();
  if (s.length === 0) return "";
  const first = s[0];
  if (first === '"') {
    // EDN string — same escaping as JSON for our content.
    try {
      return JSON.parse(s);
    } catch {
      return s.slice(1, -1);
    }
  }
  if (first === ":") return s.slice(1); // keyword → bare name
  if (s === "nil") return null;
  if (s === "true") return true;
  if (s === "false") return false;
  if (/^-?\d+$/.test(s)) return Number(s);
  if (/^-?\d+\.\d+$/.test(s)) return Number(s);
  return s;
}

async function fetchDatoms(
  cfg: KotobaCfg,
  index: string,
  components?: string[],
): Promise<KotobaDatom[]> {
  const body: Record<string, unknown> = { graph: cfg.graph, index };
  if (components && components.length) body.components_edn = components;
  const r = await fetch(`${cfg.url}/xrpc/${DATOMS_NSID}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  // A 404 means the graph has no Datomic head yet (never written) — treat as an
  // empty graph rather than an error so an un-ingested feed reads as empty.
  if (r.status === 404) return [];
  if (!r.ok) {
    throw new Error(`kotoba datoms ${index} → ${r.status}`);
  }
  const j = (await r.json()) as { datoms?: KotobaDatom[] };
  return j.datoms ?? [];
}

function asStr(v: unknown): string {
  return typeof v === "string" ? v : v == null ? "" : String(v);
}

/**
 * One `:eavt` scan of the (dedicated) yoro graph → parsed rows. The yoro graph
 * holds only `:yoro/*` Datoms (separate graph CID), so a full scan is bounded
 * by feed size, not the whole node. Internal-scale friendly; can move to
 * per-attribute `:avet` scans if the graph grows.
 */
export async function scanYoro(cfg: KotobaCfg): Promise<YoroScan> {
  const datoms = await fetchDatoms(cfg, ":eavt");
  const byEntity = new Map<string, Record<string, unknown>>();
  for (const d of datoms) {
    if (!d.added) continue;
    let ent = byEntity.get(d.e);
    if (!ent) {
      ent = {};
      byEntity.set(d.e, ent);
    }
    ent[d.a] = parseEdnScalar(d.v_edn);
  }

  const posts: PostRow[] = [];
  const profiles = new Map<string, ProfileRow>();
  const follows: FollowRow[] = [];

  for (const [entity, attrs] of byEntity) {
    if (attrs[":yoro.post/uri"] !== undefined) {
      let record: Record<string, unknown> | undefined;
      const rawRecord = attrs[":yoro.post/record"];
      if (typeof rawRecord === "string" && rawRecord.length) {
        try {
          record = JSON.parse(rawRecord) as Record<string, unknown>;
        } catch {
          record = undefined;
        }
      }
      posts.push({
        entity,
        uri: asStr(attrs[":yoro.post/uri"]),
        cid: asStr(attrs[":yoro.post/cid"]),
        author: asStr(attrs[":yoro.post/author"]),
        text: asStr(attrs[":yoro.post/text"]),
        createdAt: asStr(attrs[":yoro.post/createdAt"]),
        record,
        replyParent: attrs[":yoro.post/replyParent"]
          ? asStr(attrs[":yoro.post/replyParent"])
          : undefined,
        replyRoot: attrs[":yoro.post/replyRoot"]
          ? asStr(attrs[":yoro.post/replyRoot"])
          : undefined,
      });
    } else if (attrs[":yoro.profile/did"] !== undefined) {
      const did = asStr(attrs[":yoro.profile/did"]);
      profiles.set(did, {
        did,
        handle: attrs[":yoro.profile/handle"]
          ? asStr(attrs[":yoro.profile/handle"])
          : undefined,
        displayName: attrs[":yoro.profile/displayName"]
          ? asStr(attrs[":yoro.profile/displayName"])
          : undefined,
        description: attrs[":yoro.profile/description"]
          ? asStr(attrs[":yoro.profile/description"])
          : undefined,
        avatar: attrs[":yoro.profile/avatar"]
          ? asStr(attrs[":yoro.profile/avatar"])
          : undefined,
      });
    } else if (attrs[":yoro.follow/uri"] !== undefined) {
      follows.push({
        uri: asStr(attrs[":yoro.follow/uri"]),
        follower: asStr(attrs[":yoro.follow/follower"]),
        subject: asStr(attrs[":yoro.follow/subject"]),
        createdAt: asStr(attrs[":yoro.follow/createdAt"]),
      });
    }
  }

  // Newest-first; TID/ISO createdAt sorts lexicographically.
  posts.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { posts, profiles, follows };
}
