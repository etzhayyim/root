// storage-kv.ts — Workers KV fallback for /storage/v1/object/* PUT/GET (P64).
//
// When the lg-yatabase pod doesn't yet have ai.gftd.apps.yata.putObject
// + .getObject NSID handlers (dispatcher 404), the Worker stores small
// objects directly in YATABASE_AUTH_CACHE. Content is hashed (SHA-256)
// for ETag and blob id. Per-org keyspace prevents cross-tenant access.
//
// Constraints:
//   - Object body kept in KV value (max ~25 MiB raw; we cap at 1 MiB).
//   - body stored as base64 (KV is binary-safe but PUT payload is already
//     b64 in the caller path).

export type KvStorageEnv = {
  YATABASE_AUTH_CACHE?: KVNamespace;
};

export type StoredObject = {
  blobId: string;
  etag: string;
  sizeBytes: number;
  contentType: string;
  storedAt: string;
};

const MAX_KV_BODY_BYTES = 1_000_000;
const PREFIX = "storage:v1:";

function objectKey(orgDid: string, bucket: string, key: string): string {
  return `${PREFIX}${orgDid}:obj:${bucket}/${key}`;
}

function metaKey(orgDid: string, bucket: string, key: string): string {
  return `${PREFIX}${orgDid}:meta:${bucket}/${key}`;
}

async function sha256Hex(data: Uint8Array): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function putKvObject(
  env: KvStorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
  bodyBase64: string,
  contentType: string,
): Promise<StoredObject | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const bin = atob(bodyBase64);
    if (bin.length > MAX_KV_BODY_BYTES) return null; // too big for KV fallback
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const etag = await sha256Hex(bytes);
    const meta: StoredObject = {
      blobId: `blob:kv:${etag.slice(0, 32)}`,
      etag: `"${etag.slice(0, 32)}"`,
      sizeBytes: bytes.length,
      contentType: contentType || "application/octet-stream",
      storedAt: new Date().toISOString(),
    };
    await kv.put(objectKey(orgDid, bucket, key), bodyBase64);
    await kv.put(metaKey(orgDid, bucket, key), JSON.stringify(meta));
    return meta;
  } catch (e) {
    console.warn("[yatabase][storage-kv] put failed:", e);
    return null;
  }
}

export async function getKvObject(
  env: KvStorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
): Promise<(StoredObject & { dataBase64: string }) | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const [bodyRaw, metaRaw] = await Promise.all([
      kv.get(objectKey(orgDid, bucket, key)),
      kv.get(metaKey(orgDid, bucket, key)),
    ]);
    if (!bodyRaw || !metaRaw) return null;
    const meta = JSON.parse(metaRaw) as StoredObject;
    return { ...meta, dataBase64: bodyRaw };
  } catch (e) {
    console.warn("[yatabase][storage-kv] get failed:", e);
    return null;
  }
}

// P69: short-lived signed URLs for KV-stored objects. Token is HMAC over
// {orgDid, bucket, key, expiresAt} using DISPATCHER_INTERNAL_SECRET.
// /storage/v1/object/public/... verifies the token and serves the body.
export async function mintKvSignedUrl(
  env: KvStorageEnv & { DISPATCHER_INTERNAL_SECRET?: string; YATA_R2?: R2Bucket },
  orgDid: string,
  bucket: string,
  key: string,
  expiresInSec: number,
): Promise<{ signedURL: string; expiresAt: string } | null> {
  const secret = env.DISPATCHER_INTERNAL_SECRET;
  if (!secret) return null;
  // P73: object can live in either R2 or KV. Mint the signed URL if
  // EITHER tier has it. The public-acl verifier checks both.
  const inKv = await env.YATABASE_AUTH_CACHE?.get(metaKey(orgDid, bucket, key));
  let inR2 = false;
  if (!inKv && env.YATA_R2) {
    try {
      const head = await env.YATA_R2.head(`yata/${orgDid}/${bucket}/${key}`);
      inR2 = !!head;
    } catch { /* ignore */ }
  }
  if (!inKv && !inR2) return null;
  const expiresAt = new Date(Date.now() + Math.max(60, Math.min(86400, expiresInSec)) * 1000).toISOString();
  const payload = `${orgDid}|${bucket}|${key}|${expiresAt}`;
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", keyMaterial, enc.encode(payload));
  const token = Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
  const orgB64 = btoa(orgDid).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  const expB64 = encodeURIComponent(expiresAt);
  const signedURL = `https://yatabase.etzhayyim.com/storage/v1/object/public/${encodeURIComponent(bucket)}/${encodeURIComponent(key)}?token=${token}&org=${orgB64}&exp=${expB64}`;
  return { signedURL, expiresAt };
}

export async function verifyKvSignedUrl(
  env: KvStorageEnv & { DISPATCHER_INTERNAL_SECRET?: string },
  orgB64: string,
  bucket: string,
  key: string,
  expiresAt: string,
  token: string,
): Promise<{ orgDid: string } | null> {
  const secret = env.DISPATCHER_INTERNAL_SECRET;
  if (!secret) return null;
  // Decode orgDid (base64url-ish)
  let orgDid: string;
  try {
    const pad = "=".repeat((4 - (orgB64.length % 4)) % 4);
    orgDid = atob(orgB64.replace(/-/g, "+").replace(/_/g, "/") + pad);
  } catch { return null; }
  if (new Date(expiresAt).getTime() < Date.now()) return null;
  const payload = `${orgDid}|${bucket}|${key}|${expiresAt}`;
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", keyMaterial, enc.encode(payload));
  const expected = Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
  if (token !== expected) return null;
  return { orgDid };
}

export async function listKvBuckets(env: KvStorageEnv, orgDid: string): Promise<Array<{ name: string; objectCount: number }>> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return [];
  try {
    const list = await kv.list({ prefix: `${PREFIX}${orgDid}:meta:` });
    const counts = new Map<string, number>();
    for (const k of list.keys ?? []) {
      const tail = k.name.slice(`${PREFIX}${orgDid}:meta:`.length);
      const bucket = tail.split("/")[0];
      if (bucket) counts.set(bucket, (counts.get(bucket) ?? 0) + 1);
    }
    return Array.from(counts.entries()).map(([name, objectCount]) => ({ name, objectCount }));
  } catch {
    return [];
  }
}

// P70: list objects within a bucket (Supabase shape).
export async function listKvObjects(
  env: KvStorageEnv,
  orgDid: string,
  bucket: string,
  prefix: string,
  limit: number,
): Promise<Array<{ name: string; size: number; etag: string; contentType: string; updatedAt: string }>> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return [];
  try {
    const metaPrefix = `${PREFIX}${orgDid}:meta:${bucket}/${prefix}`;
    const list = await kv.list({ prefix: metaPrefix, limit: Math.max(1, Math.min(1000, limit)) });
    const out: Array<{ name: string; size: number; etag: string; contentType: string; updatedAt: string }> = [];
    for (const k of list.keys ?? []) {
      const raw = await kv.get(k.name);
      if (!raw) continue;
      try {
        const meta = JSON.parse(raw) as StoredObject;
        const objectKeyOnly = k.name.slice(`${PREFIX}${orgDid}:meta:${bucket}/`.length);
        out.push({
          name: objectKeyOnly,
          size: meta.sizeBytes,
          etag: meta.etag,
          contentType: meta.contentType,
          updatedAt: meta.storedAt,
        });
      } catch { /* ignore */ }
    }
    return out;
  } catch {
    return [];
  }
}

// P70: delete object from KV. Returns true if anything was actually
// removed (so the caller can report 200 vs 404).
export async function deleteKvObject(
  env: KvStorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
): Promise<boolean> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return false;
  try {
    const existed = await kv.get(metaKey(orgDid, bucket, key));
    if (!existed) return false;
    await Promise.all([
      kv.delete(objectKey(orgDid, bucket, key)),
      kv.delete(metaKey(orgDid, bucket, key)),
    ]);
    return true;
  } catch (e) {
    console.warn("[yatabase][storage-kv] delete failed:", e);
    return false;
  }
}
