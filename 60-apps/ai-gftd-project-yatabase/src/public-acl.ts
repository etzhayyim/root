// public-acl.ts — `/storage/v1/object/public/{bucket}/{key}` handler (P3.2).
//
// Streams a public-readable blob to anonymous callers with two gates:
//
//   1. Bucket-level: `vertex_yata_bucket.public_read = true` AND
//      `status = 'active'`. Looked up via Hyperdrive direct.
//   2. Blob-level: status = 'active', is_delete_marker = false,
//      bucket-membership match. (Per-blob ACL rows are checked in P3.3
//      when the bucket-default flips to private; for now the bucket
//      flag governs the entire bucket.)
//
// Implementation: rather than streaming bytes through CF Worker memory
// (which would burn LRU + bandwidth), the Worker mints a short-TTL
// presigned URL via `yata.storage.presign` BPMN and 302-redirects.
// CF Cache API caches the redirect Response for 60s keyed on
// `bucket/key`, so repeat hits do not re-roll the dispatcher round-trip.
//
// 5 MiB inline limit does NOT apply here because the redirect target is
// the upstream provider (B2 / Vultr OS) which serves the bytes directly.
//
// Trade-offs:
//   - Each cache miss = 1 dispatcher RT + 1 RW SELECT (bucket lookup) +
//     1 redirect mint. Roughly 200-400ms cold, single-digit ms warm.
//   - Cache key includes bucket + key only (no Range / If-* sensitivity)
//     — fine for static-asset use cases the public ACL is intended for.
//   - 60s redirect TTL is shorter than the presigned URL TTL (default
//     3600s) so a stale cache entry is still followable until presigned
//     URL expiry.

import { dispatchYataXrpc, type DispatcherCallerContext, type DispatcherEnv } from "./dispatcher";
import type { HyperdriveReadEnv } from "./hyperdrive-reads";

interface PublicAclEnv extends DispatcherEnv, HyperdriveReadEnv {}

interface AnyKyselyDb {
  selectFrom(table: string): {
    select(cols: string[]): {
      where(col: string, op: string, val: unknown): {
        where(col: string, op: string, val: unknown): {
          where(col: string, op: string, val: unknown): {
            limit(n: number): {
              executeTakeFirst(): Promise<Record<string, unknown> | undefined>;
            };
          };
        };
      };
    };
  };
}

const PUBLIC_REDIRECT_TTL = 60; // seconds

async function bucketIsPublic(env: HyperdriveReadEnv, bucket: string): Promise<{ public: boolean; orgDid: string } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    const db = sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
    const row = await db
      .selectFrom("vertex_yata_bucket")
      .select(["public_read", "status", "org_did"])
      .where("bucket_name", "=", bucket)
      .where("status", "=", "active")
      .where("public_read", "=", true)
      .limit(1)
      .executeTakeFirst();
    if (!row) return null;
    return { public: true, orgDid: String(row.org_did ?? "") };
  } catch (e) {
    console.warn("[yatabase][public-acl] bucket lookup failed:", e);
    return null;
  }
}

/**
 * Handle `/storage/v1/object/public/{bucket}/{key}`. Returns:
 *   - 302 redirect to a presigned URL on success
 *   - 404 if bucket not public or object missing
 *   - 503 on dispatcher failure (cache miss)
 */
export async function handlePublicAcl(
  req: Request,
  env: PublicAclEnv,
  bucket: string,
  key: string,
): Promise<Response> {
  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response(JSON.stringify({ error: "MethodNotAllowed" }), {
      status: 405,
      headers: { "content-type": "application/json" },
    });
  }

  // P69: signed-URL token verification. `?token=...&org=...&exp=...` from
  // mintKvSignedUrl unlocks the object regardless of bucket public-read.
  const url = new URL(req.url);
  const token = url.searchParams.get("token");
  const orgB64 = url.searchParams.get("org");
  const exp = url.searchParams.get("exp");
  if (token && orgB64 && exp) {
    const { verifyKvSignedUrl, getKvObject } = await import("./storage-kv");
    const verified = await verifyKvSignedUrl(env as never, orgB64, bucket, key, exp, token);
    if (verified) {
      // P73: prefer R2 (no size cap, fast). Fall back to KV.
      const { getR2Object } = await import("./storage-r2");
      const r2obj = await getR2Object(env as never, verified.orgDid, bucket, key);
      if (r2obj) {
        if (req.method === "HEAD") {
          return new Response(null, {
            status: 200,
            headers: {
              "content-type": r2obj.contentType,
              "content-length": String(r2obj.sizeBytes),
              etag: r2obj.etag,
              "x-yatabase-storage-tier": "r2-signed",
            },
          });
        }
        return new Response(r2obj.body, {
          status: 200,
          headers: {
            "content-type": r2obj.contentType,
            "content-length": String(r2obj.sizeBytes),
            etag: r2obj.etag,
            "cache-control": "private, max-age=60",
            "x-yatabase-storage-tier": "r2-signed",
          },
        });
      }
      const obj = await getKvObject(env as never, verified.orgDid, bucket, key);
      if (obj) {
        const bin = atob(obj.dataBase64);
        const out = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
        if (req.method === "HEAD") {
          return new Response(null, {
            status: 200,
            headers: {
              "content-type": obj.contentType,
              "content-length": String(obj.sizeBytes),
              etag: obj.etag,
              "x-yatabase-storage-tier": "kv-fallback-signed",
            },
          });
        }
        return new Response(out, {
          status: 200,
          headers: {
            "content-type": obj.contentType,
            "content-length": String(obj.sizeBytes),
            etag: obj.etag,
            "cache-control": "private, max-age=60",
            "x-yatabase-storage-tier": "kv-fallback-signed",
          },
        });
      }
      return new Response(JSON.stringify({ error: "NotFound", message: "object missing" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      });
    }
    return new Response(JSON.stringify({ error: "Forbidden", message: "invalid or expired signed token" }), {
      status: 403,
      headers: { "content-type": "application/json" },
    });
  }

  // Cache hit?
  const cache = (caches as { default?: Cache }).default;
  const cacheKey = new Request(`https://yatabase.etzhayyim.com/__cache/public/${bucket}/${encodeURIComponent(key)}`);
  if (cache) {
    const cached = await cache.match(cacheKey);
    if (cached) return cached.clone();
  }

  // Bucket gate.
  const bucketRow = await bucketIsPublic(env, bucket);
  if (!bucketRow) {
    return new Response(JSON.stringify({ error: "NotFound", message: "bucket is not public" }), {
      status: 404,
      headers: { "content-type": "application/json" },
    });
  }

  // Mint a presigned URL through the dispatcher. Caller context is the
  // bucket owner — the public download is on the owner's metering tab.
  const caller: DispatcherCallerContext = {
    orgDid: bucketRow.orgDid,
    actorDid: bucketRow.orgDid,
    productScope: "yata",
    traceId: req.headers.get("cf-ray") ?? undefined,
  };
  const result = await dispatchYataXrpc<{ url?: string; expiresAt?: string }>(
    env,
    "com.etzhayyim.apps.yata.presignUrl",
    {
      bucketName: bucket,
      objectKey: key,
      method: "GET",
      expiresInSec: 3600,
    },
    caller,
    { timeoutMs: 15_000 },
  );
  if (!result.ok || !result.data?.url) {
    return new Response(JSON.stringify({ error: "BackendUnavailable", message: result.error ?? "presign failed" }), {
      status: 503,
      headers: { "content-type": "application/json" },
    });
  }

  const resp = new Response(null, {
    status: 302,
    headers: {
      location: result.data.url,
      "cache-control": `public, max-age=${PUBLIC_REDIRECT_TTL}`,
    },
  });

  if (cache && req.method === "GET") {
    const cacheable = new Response(null, {
      status: 302,
      headers: {
        location: result.data.url,
        "cache-control": `public, max-age=${PUBLIC_REDIRECT_TTL}`,
      },
    });
    void cache.put(cacheKey, cacheable);
  }

  return resp;
}
