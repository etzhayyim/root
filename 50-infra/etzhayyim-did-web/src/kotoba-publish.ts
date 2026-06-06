/**
 * kotoba-publish.ts — apex side of member-signed block publishing.
 *
 * The browser kotoba node commits its Datom log into a Prolly tree, MEMBER-SIGNS
 * the root (ed25519, the server never signs — ADR-2605231525), and POSTs the
 * root + signature + the delta blocks here. This module:
 *   1. VERIFIES the ed25519 signature over the root by the claimed did:key
 *      (the server only verifies — it cannot mint a root);
 *   2. stores the blocks in KV (content-addressed; the consuming SW re-verifies
 *      each CID on ingest, so storage is trustless end-to-end);
 *   3. advances the published root pointer so other browsers hydrate the update;
 *   4. records a SUPPRESSABLE, ENCRYPTED IP attestation (Wikipedia-style edit
 *      accountability) — captured server-side (the only place the client IP is
 *      knowable), stored in mutable KV (erasable, unlike the immutable blocks),
 *      encrypted under an operator oversight key when configured. The immutable
 *      blocks themselves never carry IP/PII.
 *
 * KV layout (reuses ACTOR_KV with prefixes):
 *   kblk:<cid>       → block bytes (hex)
 *   kroot:<graph>    → { root, blocks[], datoms, updatedAt, did } (latest)
 *   kattest:<graph>:<root> → { did, ts, ipHash, ipPrefix, ipEnc? }  (suppressable)
 */

export interface PublishEnv {
  ACTOR_KV?: KVNamespace;
  /** base64(32 bytes) AES-256-GCM oversight key. When set, the raw client IP is
   *  stored encrypted (recoverable only by oversight); otherwise only a salted
   *  hash + /24 prefix are kept (pseudonymous, charter-clean). Operator-gated. */
  KOTOBA_ATTEST_KEY?: string;
}

const GENESIS_ROOT_FALLBACK: Record<string, unknown> = {
  graph: "yoro-social-v1",
  // The compiled genesis pointer; the static /kotoba/yoro-social-v1.root.json
  // is the source of truth until the first publish lands in KV.
  root: "",
  note: "no published root yet — client should fall back to the static genesis pointer",
};

// ─── base32 (RFC4648 lower, no pad) — CIDv1 multibase 'b' ────────────────────
const B32 = "abcdefghijklmnopqrstuvwxyz234567";
export function base32Decode(s: string): Uint8Array {
  let bits = 0;
  let value = 0;
  const out: number[] = [];
  for (const ch of s) {
    const idx = B32.indexOf(ch);
    if (idx < 0) continue;
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      out.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return new Uint8Array(out);
}
function hexToBytes(h: string): Uint8Array {
  const clean = h.trim();
  const a = new Uint8Array(clean.length / 2);
  for (let i = 0; i < a.length; i++) a[i] = parseInt(clean.substr(i * 2, 2), 16);
  return a;
}
function bytesToHex(b: Uint8Array): string {
  let s = "";
  for (const x of b) s += x.toString(16).padStart(2, "0");
  return s;
}
function b64(bytes: Uint8Array): string {
  let s = "";
  for (const x of bytes) s += String.fromCharCode(x);
  return btoa(s);
}

// ed25519 verify of the member signature over the raw root CID bytes.
// did = "did:key:z" + hex(32-byte pubkey); root = CIDv1 multibase ("b"+base32);
// commit_signed signs root.0 (the raw CID bytes). (See kotoba-wasm WriteCrypto.)
export async function verifyRootSig(did: string, rootMultibase: string, sigHex: string): Promise<boolean> {
  try {
    if (!did.startsWith("did:key:z")) return false;
    const pub = hexToBytes(did.slice("did:key:z".length));
    if (pub.length !== 32) return false;
    if (!rootMultibase.startsWith("b")) return false;
    const rootBytes = base32Decode(rootMultibase.slice(1));
    const sig = hexToBytes(sigHex);
    if (sig.length !== 64) return false;
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    return await crypto.subtle.verify({ name: "Ed25519" }, key, sig, rootBytes);
  } catch {
    return false;
  }
}

async function sha256Hex(s: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return bytesToHex(new Uint8Array(d));
}

// Encrypt the raw IP under the operator oversight key, if configured.
async function encryptIp(env: PublishEnv, ip: string): Promise<{ iv: string; ct: string } | undefined> {
  if (!env.KOTOBA_ATTEST_KEY) return undefined;
  try {
    const raw = Uint8Array.from(atob(env.KOTOBA_ATTEST_KEY), (c) => c.charCodeAt(0));
    if (raw.length !== 32) return undefined;
    const key = await crypto.subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["encrypt"]);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = new Uint8Array(
      await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(ip)),
    );
    return { iv: b64(iv), ct: b64(ct) };
  } catch {
    return undefined;
  }
}

export function ipPrefix(ip: string): string {
  if (ip.includes(".")) return ip.split(".").slice(0, 3).join(".") + ".0/24"; // IPv4 /24
  if (ip.includes(":")) return ip.split(":").slice(0, 3).join(":") + "::/48"; // IPv6 /48
  return "";
}

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "x-kotoba-publish": "1" };

/** POST com.etzhayyim.apps.kotoba.block.put — verify sig, store blocks + root,
 *  record a suppressable encrypted IP attestation. */
export async function handleBlockPut(request: Request, env: PublishEnv): Promise<Response> {
  if (!env.ACTOR_KV) {
    return new Response(JSON.stringify({ error: "PublishUnavailable", message: "ACTOR_KV not bound" }), {
      status: 503,
      headers: JSON_HEADERS,
    });
  }
  let body: {
    graph?: string;
    root?: string;
    did?: string;
    sig?: string;
    prevRoot?: string; // optimistic-concurrency base: advance only if KV root == prevRoot
    blocks?: { cid: string; hex: string }[];
    edit?: { collection?: string; uri?: string };
  };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "BadRequest", message: "invalid JSON" }), {
      status: 400,
      headers: JSON_HEADERS,
    });
  }
  const graph = body.graph || "yoro-social-v1";
  const { root, did, sig } = body;
  const blocks = Array.isArray(body.blocks) ? body.blocks : [];
  if (!root || !did || !sig) {
    return new Response(JSON.stringify({ error: "BadRequest", message: "root/did/sig required" }), {
      status: 400,
      headers: JSON_HEADERS,
    });
  }
  // Guardrails: bound the publish so a single caller can't flood KV.
  if (blocks.length > 64) {
    return new Response(JSON.stringify({ error: "TooManyBlocks", max: 64 }), { status: 413, headers: JSON_HEADERS });
  }
  for (const b of blocks) {
    if (!b || typeof b.cid !== "string" || typeof b.hex !== "string" || b.hex.length > 4_000_000) {
      return new Response(JSON.stringify({ error: "BadBlock" }), { status: 413, headers: JSON_HEADERS });
    }
  }

  // 1) VERIFY the member signature over the root (the server only verifies).
  const ok = await verifyRootSig(did, root, sig);
  if (!ok) {
    return new Response(JSON.stringify({ error: "BadSignature", message: "ed25519 verify failed" }), {
      status: 401,
      headers: JSON_HEADERS,
    });
  }

  // 2) Store the delta blocks first (content-addressed + idempotent; a failed
  //    CAS just leaves reusable orphan blocks). The consumer re-verifies each CID.
  await Promise.all(blocks.map((b) => env.ACTOR_KV!.put(`kblk:${b.cid}`, b.hex)));

  const manifest = {
    graph,
    root,
    blocks: blocks.map((b) => b.cid),
    did,
    updatedAt: new Date().toISOString(),
  };
  let rlTokens: number | undefined; // remaining rate-limit tokens (DO path), for observability

  // 3) Advance the published head under KV CHECK-AND-SET (advance only if the
  //    publisher rebased on the current head — prevents lost updates). No Durable
  //    Object (ADR-2605262130 / 2605312345: kotoba is the canonical, content-
  //    addressed substrate; there is no operated server-state primitive). KV
  //    read-check-write narrows the race window and the consumer re-verifies every
  //    CID on ingest, so a concurrent advance can only orphan reusable blocks,
  //    never corrupt the log. Rate-limit + stats below are KV-backed best-effort
  //    (non-atomic) — coarse DoS control + observability where exactness is
  //    unnecessary, NOT an authoritative server-state primitive.
  const bumpStat = async (field: string, extra?: Record<string, unknown>) => {
    try {
      const raw = await env.ACTOR_KV!.get(`kstats:${graph}`);
      const s = (raw ? JSON.parse(raw) : {}) as Record<string, unknown>;
      s[field] = ((s[field] as number) ?? 0) + 1;
      await env.ACTOR_KV!.put(`kstats:${graph}`, JSON.stringify({ ...s, ...extra }));
    } catch {
      /* stats are best-effort observability — never fail the publish on a stats write */
    }
  };
  // CAS conflict (someone advanced the head) — a rebase, NOT abuse, costs no token.
  const prevRaw = await env.ACTOR_KV.get(`kroot:${graph}`);
  if (prevRaw) {
    let cur: { root?: string } = {};
    try {
      cur = JSON.parse(prevRaw);
    } catch {
      /* treat as no prior */
    }
    if (cur.root && cur.root !== body.prevRoot) {
      await bumpStat("conflicts");
      return new Response(
        JSON.stringify({ error: "Conflict", message: "root advanced — rebase and retry", currentRoot: cur.root }),
        { status: 409, headers: JSON_HEADERS },
      );
    }
  }
  // Best-effort per-DID token-bucket rate limit on actual head advances (caps the
  // sustained root-churn DoS vector). A token is spent ONLY on a real advance, so
  // honest rebasers are never charged.
  {
    const CAP = 12;
    const REFILL_MS = 2500;
    const now = Date.now();
    const rlKey = `krl:${graph}:${did || "anon"}`;
    let b: { tokens: number; ts: number } = { tokens: CAP, ts: now };
    try {
      const raw = await env.ACTOR_KV.get(rlKey);
      if (raw) b = JSON.parse(raw) as { tokens: number; ts: number };
    } catch {
      /* fresh bucket */
    }
    const refill = Math.floor((now - b.ts) / REFILL_MS);
    if (refill > 0) {
      b.tokens = Math.min(CAP, b.tokens + refill);
      b.ts = now;
    }
    if (b.tokens < 1) {
      await env.ACTOR_KV.put(rlKey, JSON.stringify(b));
      await bumpStat("rateLimited");
      return new Response(
        JSON.stringify({ error: "RateLimited", message: "publish rate exceeded — retry later", retryAfterMs: REFILL_MS }),
        { status: 429, headers: { ...JSON_HEADERS, "retry-after": String(Math.ceil(REFILL_MS / 1000)) } },
      );
    }
    b.tokens -= 1;
    rlTokens = b.tokens;
    await env.ACTOR_KV.put(rlKey, JSON.stringify(b));
  }
  await env.ACTOR_KV.put(`kroot:${graph}`, JSON.stringify(manifest));
  await bumpStat("advances", { lastAdvanceAt: new Date().toISOString(), root });

  // 4) Suppressable, encrypted IP attestation (Wikipedia-style accountability,
  //    captured server-side, never in the immutable blocks).
  const ip = request.headers.get("cf-connecting-ip") || request.headers.get("x-forwarded-for") || "";
  const attest = {
    did,
    root,
    edit: body.edit || null,
    ts: new Date().toISOString(),
    ipHash: ip ? await sha256Hex(`${graph}:${ip}`) : "", // pseudonymous, charter-clean
    ipPrefix: ipPrefix(ip),
    ipEnc: ip ? await encryptIp(env, ip) : undefined, // raw IP recoverable only w/ oversight key
  };
  await env.ACTOR_KV.put(`kattest:${graph}:${root}`, JSON.stringify(attest));

  return new Response(
    JSON.stringify({
      ok: true,
      root,
      storedBlocks: blocks.length,
      rlTokens,
      attest: { ipHash: attest.ipHash, ipPrefix: attest.ipPrefix, ipEncrypted: !!attest.ipEnc },
    }),
    { status: 200, headers: JSON_HEADERS },
  );
}

/** POST com.etzhayyim.apps.kotoba.block.has — body { cids: [...] } → { missing:
 *  [...] } the CIDs not already in KV. Lets the publisher send only the delta
 *  (content-addressed blocks are immutable, so "present" never needs resending). */
export async function handleBlockHas(request: Request, env: PublishEnv): Promise<Response> {
  let cids: string[] = [];
  try {
    const body = (await request.json()) as { cids?: unknown };
    if (Array.isArray(body.cids)) cids = body.cids.filter((c): c is string => typeof c === "string").slice(0, 4096);
  } catch {
    return new Response(JSON.stringify({ error: "BadRequest" }), { status: 400, headers: JSON_HEADERS });
  }
  if (!env.ACTOR_KV) return new Response(JSON.stringify({ missing: cids }), { status: 200, headers: JSON_HEADERS });
  const present = await Promise.all(
    cids.map(async (c) => ((await env.ACTOR_KV!.get(`kblk:${c}`, "stream")) ? c : null)),
  );
  const has = new Set(present.filter(Boolean) as string[]);
  return new Response(JSON.stringify({ missing: cids.filter((c) => !has.has(c)) }), {
    status: 200,
    headers: JSON_HEADERS,
  });
}

/** GET com.etzhayyim.apps.kotoba.root?graph=… — the latest published root
 *  pointer (KV), or a 204-ish empty so the client falls back to the static
 *  genesis pointer. */
export async function handleRootGet(url: URL, env: PublishEnv): Promise<Response> {
  const graph = url.searchParams.get("graph") || "yoro-social-v1";
  if (env.ACTOR_KV) {
    const raw = await env.ACTOR_KV.get(`kroot:${graph}`);
    if (raw) return new Response(raw, { status: 200, headers: JSON_HEADERS });
  }
  return new Response(JSON.stringify({ ...GENESIS_ROOT_FALLBACK, graph }), { status: 200, headers: JSON_HEADERS });
}

/** GET com.etzhayyim.apps.kotoba.stats?graph=… — publish outcome counters
 *  (advances / conflicts / rateLimited) from the authoritative head DO. Public,
 *  no PII — operability/monitoring surface. */
export async function handleStatsGet(url: URL, env: PublishEnv): Promise<Response> {
  const graph = url.searchParams.get("graph") || "yoro-social-v1";
  if (!env.ACTOR_KV) {
    return new Response(JSON.stringify({ error: "StatsUnavailable", message: "ACTOR_KV not bound" }), {
      status: 503,
      headers: JSON_HEADERS,
    });
  }
  // Best-effort KV-backed publish-outcome counters (advances / conflicts /
  // rateLimited) — observability only, no DO (ADR-2605262130 / 2605312345).
  let s: Record<string, unknown> = {};
  try {
    const raw = await env.ACTOR_KV.get(`kstats:${graph}`);
    if (raw) s = JSON.parse(raw) as Record<string, unknown>;
  } catch {
    /* no stats yet */
  }
  const rootRaw = await env.ACTOR_KV.get(`kroot:${graph}`);
  let root = "";
  let updatedAt = "";
  if (rootRaw) {
    try {
      const m = JSON.parse(rootRaw) as { root?: string; updatedAt?: string };
      root = m.root ?? "";
      updatedAt = m.updatedAt ?? "";
    } catch {
      /* ignore */
    }
  }
  return new Response(JSON.stringify({ graph, ...s, root, updatedAt }), { status: 200, headers: JSON_HEADERS });
}

/** GET /kotoba/blocks/<cid> fallback — serves a dynamically published block from
 *  KV (the genesis blocks are static assets and never reach the Worker). */
export async function serveBlockFromKv(cid: string, env: PublishEnv): Promise<Response | null> {
  if (!env.ACTOR_KV) return null;
  const hex = await env.ACTOR_KV.get(`kblk:${cid}`);
  if (!hex) return null;
  const bytes = hexToBytes(hex);
  return new Response(bytes, {
    status: 200,
    headers: {
      "content-type": "application/octet-stream",
      "cache-control": "public, max-age=31536000, immutable", // content-addressed
      "x-kotoba-block": "kv",
    },
  });
}
