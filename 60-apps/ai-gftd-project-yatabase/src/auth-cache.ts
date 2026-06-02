// auth-cache.ts — Workers KV fallback for sk_live_yata_* resolution.
//
// Why this exists: per ADR-2605111200 the Worker no longer talks to RW
// directly, so it asks the lg-yatabase pod via dispatcher for every
// bearer key. When RisingWave durability degrades (another team's batch
// jobs jam the barrier coordinator, etc.), the pod's authResolveApiKey
// returns `{found: false}` and customers' bearer tokens stop working
// even though signup just minted them.
//
// This module caches `SHA256(rawKey) → {ownerDid, scopes, productScope}`
// in a Workers KV namespace bound as YATABASE_AUTH_CACHE (24h TTL):
//   • signup writes the KV entry at mint-time (auth-signup.ts)
//   • resolveAuthContext checks KV before hitting the pod (app.ts)
//   • resolveAuthContext also backfills KV on first pod hit
//
// Security: the cache key is a SHA-256 of the raw bearer; an attacker
// would already need the bearer to look it up. TTL = 24h so revocation
// propagates worst-case in 24h.
//
// Workers Cache API (caches.default) was tried first but `put` succeeded
// while `match` returned undefined across requests — synthesized
// responses don't persist reliably in the edge cache. KV is the right
// primitive for cross-request state.

const KV_TTL_SECONDS = 86400;

export type CachedKeyRecord = {
  ownerDid: string;
  scopes: string;
  productScope: string;
};

export type AuthCacheEnv = {
  YATABASE_AUTH_CACHE?: KVNamespace;
};

export async function sha256Hex(input: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function kvKeyFor(keyHash: string): string {
  return `auth:v1:${keyHash}`;
}

export async function rememberApiKeyResolution(
  env: AuthCacheEnv,
  rawKey: string,
  ownerDid: string,
  scopes: string = "atproto,include:com.etzhayyim.apps.yata",
  productScope: string = "yata",
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) {
    console.warn("[yatabase][auth-cache] no KV binding (YATABASE_AUTH_CACHE)");
    return;
  }
  try {
    const keyHash = await sha256Hex(rawKey);
    const body = JSON.stringify({ ownerDid, scopes, productScope, at: Date.now() });
    await kv.put(kvKeyFor(keyHash), body, { expirationTtl: KV_TTL_SECONDS });
    // P63: maintain a per-org key index so /api/export can enumerate
    // the active keys without round-tripping to RW.
    try {
      const idxKey = `org_keys:v1:${ownerDid}`;
      const prevRaw = await kv.get(idxKey);
      const prev = prevRaw ? JSON.parse(prevRaw) as { keys?: Array<{ keyHash: string; keyPrefix: string; mintedAt: string }> } : { keys: [] };
      const list = prev.keys ?? [];
      const keyPrefix = rawKey.slice(0, 16);
      if (!list.some((k) => k.keyHash === keyHash)) {
        list.push({ keyHash, keyPrefix, mintedAt: new Date().toISOString() });
        await kv.put(idxKey, JSON.stringify({ keys: list }));
      }
    } catch (e) {
      console.warn("[yatabase][auth-cache] org_keys index update failed:", e);
    }
    console.log(`[yatabase][auth-cache] PUT ok keyHash=${keyHash.slice(0, 16)} ownerDid=${ownerDid}`);
  } catch (e) {
    console.warn("[yatabase][auth-cache] put failed:", e);
  }
}

export async function listCachedKeysForOrg(env: AuthCacheEnv, ownerDid: string): Promise<Array<{ keyHash: string; keyPrefix: string; mintedAt: string }>> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return [];
  try {
    const raw = await kv.get(`org_keys:v1:${ownerDid}`);
    if (!raw) return [];
    const data = JSON.parse(raw) as { keys?: Array<{ keyHash: string; keyPrefix: string; mintedAt: string }> };
    return data.keys ?? [];
  } catch {
    return [];
  }
}

// P86: cache the AWS SigV4 credentials minted alongside the bearer key
// so /s3/* path verification doesn't need to round-trip to RW (blocked
// by ADR-2605111200). Key shape: `aws_creds:v1:{accessKeyId}` →
// `{secret, ownerDid, scopes, productScope, at}`.
export type CachedAwsCredsRecord = {
  secret: string;
  ownerDid: string;
  scopes: string;
  productScope: string;
};

export async function rememberAwsCreds(
  env: AuthCacheEnv,
  awsAccessKeyId: string,
  awsSecretAccessKey: string,
  ownerDid: string,
  scopes: string = "atproto,include:com.etzhayyim.apps.yata",
  productScope: string = "yata",
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv || !awsAccessKeyId || !awsSecretAccessKey) return;
  try {
    const body = JSON.stringify({
      secret: awsSecretAccessKey, ownerDid, scopes, productScope, at: Date.now(),
    });
    await kv.put(`aws_creds:v1:${awsAccessKeyId}`, body, { expirationTtl: KV_TTL_SECONDS });
  } catch (e) {
    console.warn("[yatabase][auth-cache] aws_creds put failed:", e);
  }
}

export async function lookupCachedAwsCreds(
  env: AuthCacheEnv,
  awsAccessKeyId: string,
): Promise<CachedAwsCredsRecord | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const raw = await kv.get(`aws_creds:v1:${awsAccessKeyId}`);
    if (!raw) return null;
    const data = JSON.parse(raw) as {
      secret?: string; ownerDid?: string; scopes?: string; productScope?: string;
    };
    if (!data?.secret || !data?.ownerDid) return null;
    return {
      secret: data.secret,
      ownerDid: data.ownerDid,
      scopes: data.scopes ?? "atproto",
      productScope: data.productScope ?? "yata",
    };
  } catch (e) {
    console.warn("[yatabase][auth-cache] aws_creds lookup threw:", e);
    return null;
  }
}

export async function lookupCachedApiKey(
  env: AuthCacheEnv,
  rawKey: string,
): Promise<CachedKeyRecord | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const keyHash = await sha256Hex(rawKey);
    const raw = await kv.get(kvKeyFor(keyHash));
    if (!raw) {
      console.log(`[yatabase][auth-cache] MISS keyHash=${keyHash.slice(0, 16)}`);
      return null;
    }
    const data = JSON.parse(raw) as {
      ownerDid?: string; scopes?: string; productScope?: string;
    };
    if (!data?.ownerDid) return null;
    console.log(`[yatabase][auth-cache] HIT keyHash=${keyHash.slice(0, 16)} ownerDid=${data.ownerDid}`);
    return {
      ownerDid: data.ownerDid,
      scopes: data.scopes ?? "atproto",
      productScope: data.productScope ?? "yata",
    };
  } catch (e) {
    console.warn("[yatabase][auth-cache] lookup threw:", e);
    return null;
  }
}
