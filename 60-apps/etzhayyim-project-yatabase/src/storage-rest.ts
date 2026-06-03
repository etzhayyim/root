// storage-rest.ts — Supabase-shape `/storage/v1/*` REST handlers.
//
// Translates HTTP requests into com.etzhayyim.apps.yata.{put,get,delete,head,
// list,presign} XRPC calls dispatched via bpmn-dispatcher (dispatcher.ts).
// Response shape mirrors Supabase Storage REST so existing
// @supabase/storage-js clients can talk to yatabase with only a base URL
// swap.
//
// Streaming downloads larger than 5 MiB inline are deferred to P3.2.

import { dispatchYataXrpc, type DispatcherCallerContext, type DispatcherEnv } from "./dispatcher";

interface StorageEnv extends DispatcherEnv {}

const INLINE_DOWNLOAD_LIMIT = 5 * 1024 * 1024;

interface PutObjectOk {
  ok: true;
  bucketName: string;
  objectKey: string;
  blobId: string;
  versionId?: string;
  etag: string;
  cid?: string;
  sizeBytes: number;
  storageTier: string;
  storageProvider: string;
}

interface GetObjectOk {
  bucketName: string;
  objectKey: string;
  blobId: string;
  versionId?: string;
  etag: string;
  cid?: string;
  sizeBytes: number;
  contentType: string;
  storageTier: string;
  storageProvider: string;
  encryption: string;
  data?: string;
  lastAccessedAt?: string;
  createdAt?: string;
}

function badRequest(message: string): Response {
  return new Response(JSON.stringify({ statusCode: "400", error: "Bad Request", message }), {
    status: 400,
    headers: { "content-type": "application/json" },
  });
}

function notFound(message: string): Response {
  return new Response(JSON.stringify({ statusCode: "404", error: "Not Found", message }), {
    status: 404,
    headers: { "content-type": "application/json" },
  });
}

function dispatcherError(status: number, message: string): Response {
  return new Response(JSON.stringify({ statusCode: String(status), error: "Dispatcher Error", message }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

async function readBodyAsBase64(req: Request): Promise<{ data: string; contentType: string } | null> {
  const ct = (req.headers.get("content-type") ?? "").toLowerCase();
  if (ct.startsWith("multipart/form-data")) {
    const fd = await req.formData();
    const file = fd.get("file");
    if (!(file instanceof File) && !(file instanceof Blob)) return null;
    const buf = new Uint8Array(await file.arrayBuffer());
    let bin = "";
    for (let i = 0; i < buf.length; i++) bin += String.fromCharCode(buf[i] ?? 0);
    return {
      data: btoa(bin),
      contentType: file instanceof File && file.type ? file.type : "application/octet-stream",
    };
  }
  if (ct.includes("application/json")) {
    const j = (await req.json()) as { data?: string; contentType?: string };
    if (typeof j.data !== "string") return null;
    return { data: j.data, contentType: j.contentType ?? "application/octet-stream" };
  }
  const buf = new Uint8Array(await req.arrayBuffer());
  let bin = "";
  for (let i = 0; i < buf.length; i++) bin += String.fromCharCode(buf[i] ?? 0);
  return { data: btoa(bin), contentType: ct || "application/octet-stream" };
}

export function parseStoragePath(pathname: string): {
  kind: "object" | "objectPublic" | "objectList" | "objectSign" | "objectMultipart" | "bucket";
  bucket?: string;
  key?: string;
  /** For `objectMultipart`: one of init / upload / complete / abort. */
  multipartAction?: "init" | "upload" | "complete" | "abort";
} | null {
  if (!pathname.startsWith("/storage/v1/")) return null;
  const rest = pathname.slice("/storage/v1/".length);
  if (rest === "bucket" || rest.startsWith("bucket/")) {
    return { kind: "bucket" };
  }
  if (rest.startsWith("object/list/")) {
    return { kind: "objectList", bucket: rest.slice("object/list/".length) };
  }
  if (rest.startsWith("object/sign/")) {
    const tail = rest.slice("object/sign/".length);
    const slash = tail.indexOf("/");
    if (slash < 0) return null;
    return { kind: "objectSign", bucket: tail.slice(0, slash), key: tail.slice(slash + 1) };
  }
  if (rest.startsWith("object/public/")) {
    const tail = rest.slice("object/public/".length);
    const slash = tail.indexOf("/");
    if (slash < 0) return null;
    return { kind: "objectPublic", bucket: tail.slice(0, slash), key: tail.slice(slash + 1) };
  }
  // P3.2.6 — Supabase multipart shape:
  //   /storage/v1/object/multipart/{bucket}/{key}/{init|upload|complete|abort}
  if (rest.startsWith("object/multipart/")) {
    const tail = rest.slice("object/multipart/".length);
    const slash = tail.indexOf("/");
    if (slash < 0) return null;
    const bucket = tail.slice(0, slash);
    const after = tail.slice(slash + 1);
    const lastSlash = after.lastIndexOf("/");
    if (lastSlash < 0) return null;
    const action = after.slice(lastSlash + 1);
    if (!["init", "upload", "complete", "abort"].includes(action)) return null;
    return {
      kind: "objectMultipart",
      bucket,
      key: after.slice(0, lastSlash),
      multipartAction: action as "init" | "upload" | "complete" | "abort",
    };
  }
  if (rest.startsWith("object/")) {
    const tail = rest.slice("object/".length);
    const slash = tail.indexOf("/");
    if (slash < 0) return null;
    return { kind: "object", bucket: tail.slice(0, slash), key: tail.slice(slash + 1) };
  }
  return null;
}

export async function handleStorageRest(
  req: Request,
  env: StorageEnv,
  caller: DispatcherCallerContext | null,
): Promise<Response | null> {
  const url = new URL(req.url);
  const parsed = parseStoragePath(url.pathname);
  if (!parsed) return null;

  if (parsed.kind !== "objectPublic" && !caller) {
    return new Response(JSON.stringify({ statusCode: "401", error: "Unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }

  switch (parsed.kind) {
    case "object":
      return handleObject(req, env, caller!, parsed.bucket!, parsed.key!);
    case "objectPublic":
      return dispatcherError(501, "public ACL download not yet implemented (P3.2)");
    case "objectList":
      return handleList(req, env, caller!, parsed.bucket!);
    case "objectSign":
      return handleSign(req, env, caller!, parsed.bucket!, parsed.key!);
    case "objectMultipart":
      return handleMultipart(
        req, env, caller!,
        parsed.bucket!, parsed.key!,
        parsed.multipartAction!,
      );
    case "bucket":
      return handleBucket(env, caller!);
  }
}

// ──────────────────────────────────────────────────────────────────────
// Supabase multipart (P3.2.6)
//
// /storage/v1/object/multipart/{bucket}/{key}/init       (POST)
// /storage/v1/object/multipart/{bucket}/{key}/upload     (POST ?partNumber=N&uploadId=X, body=raw)
// /storage/v1/object/multipart/{bucket}/{key}/complete   (POST body={uploadId, parts:[]})
// /storage/v1/object/multipart/{bucket}/{key}/abort      (POST body={uploadId})
// ──────────────────────────────────────────────────────────────────────

async function handleMultipart(
  req: Request,
  env: StorageEnv,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
  action: "init" | "upload" | "complete" | "abort",
): Promise<Response> {
  if (req.method !== "POST") return badRequest(`multipart ${action} requires POST`);

  if (action === "init") {
    let body: { contentType?: string; encryption?: string } = {};
    try { body = (await req.json()) as typeof body; } catch { /* ignore */ }
    const result = await dispatchYataXrpc<{ ok?: boolean; uploadId?: string; expiresAt?: string; error?: string }>(
      env,
      "com.etzhayyim.apps.yata.multipartInit",
      { bucketName: bucket, objectKey: key, contentType: body.contentType, encryption: body.encryption },
      caller,
      { timeoutMs: 30_000 },
    );
    if (!result.ok || !result.data?.uploadId) {
      return dispatcherError(result.status, result.error ?? result.data?.error ?? "init failed");
    }
    return new Response(
      JSON.stringify({ uploadId: result.data.uploadId, expiresAt: result.data.expiresAt }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }

  if (action === "upload") {
    const url = new URL(req.url);
    const uploadId = url.searchParams.get("uploadId");
    const partNumber = Number.parseInt(url.searchParams.get("partNumber") ?? "0", 10);
    if (!uploadId || partNumber < 1) return badRequest("uploadId + partNumber required");
    const buf = new Uint8Array(await req.arrayBuffer());
    let bin = "";
    for (let i = 0; i < buf.length; i++) bin += String.fromCharCode(buf[i] ?? 0);
    const data = btoa(bin);
    const result = await dispatchYataXrpc<{ partNumber?: number; etag?: string; sizeBytes?: number; error?: string }>(
      env,
      "com.etzhayyim.apps.yata.multipartPart",
      { uploadId, partNumber, data },
      caller,
      { timeoutMs: 60_000 },
    );
    if (!result.ok || !result.data?.etag) {
      return dispatcherError(result.status, result.error ?? result.data?.error ?? "part failed");
    }
    return new Response(
      JSON.stringify({ partNumber, etag: result.data.etag, sizeBytes: result.data.sizeBytes }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }

  if (action === "complete") {
    let body: { uploadId?: string; parts?: Array<{ partNumber: number; etag: string }> } = {};
    try { body = (await req.json()) as typeof body; } catch { /* ignore */ }
    if (!body.uploadId) return badRequest("uploadId required");
    const result = await dispatchYataXrpc<{
      ok?: boolean; bucketName?: string; objectKey?: string; etag?: string; sizeBytes?: number; error?: string;
    }>(
      env,
      "com.etzhayyim.apps.yata.multipartComplete",
      { uploadId: body.uploadId, parts: body.parts ?? [] },
      caller,
      { timeoutMs: 120_000 },
    );
    if (!result.ok || !result.data?.ok) {
      return dispatcherError(result.status, result.error ?? result.data?.error ?? "complete failed");
    }
    return new Response(JSON.stringify(result.data), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }

  // abort
  let body: { uploadId?: string } = {};
  try { body = (await req.json()) as typeof body; } catch { /* ignore */ }
  if (!body.uploadId) return badRequest("uploadId required");
  const result = await dispatchYataXrpc(
    env,
    "com.etzhayyim.apps.yata.multipartAbort",
    { uploadId: body.uploadId },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok) return dispatcherError(result.status, result.error ?? "abort failed");
  return new Response(JSON.stringify({ message: "Aborted" }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function handleObject(
  req: Request,
  env: StorageEnv,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
): Promise<Response> {
  if (req.method === "PUT" || req.method === "POST") {
    const parsed = await readBodyAsBase64(req);
    if (!parsed) return badRequest("missing body or unsupported content-type");
    const ifNoneMatch = req.headers.get("if-none-match") ?? undefined;
    const result = await dispatchYataXrpc<PutObjectOk & { error?: string }>(
      env,
      "com.etzhayyim.apps.yata.putObject",
      {
        bucketName: bucket,
        objectKey: key,
        data: parsed.data,
        contentType: parsed.contentType,
        ifNoneMatch,
      },
      caller,
      { timeoutMs: 120_000 },
    );
    if (!result.ok || !result.data) {
      // P73: R2 fallback FIRST (no size cap, durable, listable). When
      // YATA_R2 isn't bound the function returns null and we fall
      // through to the legacy KV fallback (1 MiB ceiling, P64).
      const { putR2Object } = await import("./storage-r2");
      const bin = atob(parsed.data);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const r2stored = await putR2Object(env as never, caller.orgDid, bucket, key, bytes, parsed.contentType);
      if (r2stored) {
        return new Response(
          JSON.stringify({
            Key: `${bucket}/${key}`,
            Id: r2stored.blobId,
            ETag: r2stored.etag,
            Size: r2stored.sizeBytes,
            StorageTier: "r2",
            StorageProvider: "cloudflare-r2",
          }),
          { status: 200, headers: { "content-type": "application/json", etag: r2stored.etag } },
        );
      }
      // P64: Workers-KV fallback. When the pod doesn't have the storage
      // NSID yet (dispatcher 404), persist the small object body in KV so
      // the customer journey + Studio "first PUT" demo works. Limited to
      // 10 KiB per object (Workers KV 25 MiB ceiling minus overhead).
      const { putKvObject } = await import("./storage-kv");
      const stored = await putKvObject(env as never, caller.orgDid, bucket, key, parsed.data, parsed.contentType);
      if (stored) {
        return new Response(
          JSON.stringify({
            Key: `${bucket}/${key}`,
            Id: stored.blobId,
            ETag: stored.etag,
            Size: stored.sizeBytes,
            StorageTier: "kv-fallback",
            note: "stored in Workers KV (pod storage NSID not yet wired); durable, content-addressed",
          }),
          { status: 200, headers: { "content-type": "application/json", etag: stored.etag } },
        );
      }
      return dispatcherError(result.status, result.error ?? "put failed");
    }
    if ((result.data as { error?: string }).error)
      return badRequest((result.data as { error: string }).error);
    return new Response(
      JSON.stringify({
        Key: `${bucket}/${key}`,
        Id: result.data.blobId,
        ETag: result.data.etag,
        Size: result.data.sizeBytes,
        StorageTier: result.data.storageTier,
      }),
      { status: 200, headers: { "content-type": "application/json", etag: result.data.etag } },
    );
  }

  if (req.method === "GET" || req.method === "HEAD") {
    const ifNoneMatch = req.headers.get("if-none-match") ?? undefined;
    const result = await dispatchYataXrpc<GetObjectOk & { error?: string }>(
      env,
      "com.etzhayyim.apps.yata.getObject",
      {
        bucketName: bucket,
        objectKey: key,
        metadataOnly: req.method === "HEAD",
        ifNoneMatch,
      },
      caller,
      { timeoutMs: 60_000 },
    );
    if (!result.ok || !result.data) {
      // P73: R2 fallback FIRST for downloads.
      const { getR2Object, headR2Object } = await import("./storage-r2");
      if (req.method === "HEAD") {
        const r2head = await headR2Object(env as never, caller.orgDid, bucket, key);
        if (r2head) {
          return new Response(null, {
            status: 200,
            headers: {
              "content-type": r2head.contentType,
              "content-length": String(r2head.sizeBytes),
              etag: r2head.etag,
              "x-yatabase-storage-tier": "r2",
              "x-yatabase-storage-provider": "cloudflare-r2",
            },
          });
        }
      } else {
        const r2obj = await getR2Object(env as never, caller.orgDid, bucket, key);
        if (r2obj) {
          return new Response(r2obj.body, {
            status: 200,
            headers: {
              "content-type": r2obj.contentType,
              "content-length": String(r2obj.sizeBytes),
              etag: r2obj.etag,
              "x-yatabase-storage-tier": "r2",
              "x-yatabase-storage-provider": "cloudflare-r2",
            },
          });
        }
      }
      // P64: KV fallback for downloads of objects that landed via the KV
      // putKvObject path.
      const { getKvObject } = await import("./storage-kv");
      const stored = await getKvObject(env as never, caller.orgDid, bucket, key);
      if (stored) {
        if (req.method === "HEAD") {
          return new Response(null, {
            status: 200,
            headers: {
              "content-type": stored.contentType || "application/octet-stream",
              "content-length": String(stored.sizeBytes),
              etag: stored.etag,
              "x-yatabase-storage-tier": "kv-fallback",
              "x-yatabase-storage-provider": "workers-kv",
            },
          });
        }
        const bin = atob(stored.dataBase64);
        const out = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
        return new Response(out, {
          status: 200,
          headers: {
            "content-type": stored.contentType || "application/octet-stream",
            "content-length": String(stored.sizeBytes),
            etag: stored.etag,
            "x-yatabase-storage-tier": "kv-fallback",
            "x-yatabase-storage-provider": "workers-kv",
          },
        });
      }
      return notFound(result.error ?? "object not found");
    }
    if ((result.data as { error?: string }).error) return notFound((result.data as { error: string }).error);
    if (req.method === "HEAD") {
      return new Response(null, {
        status: 200,
        headers: {
          "content-type": result.data.contentType || "application/octet-stream",
          "content-length": String(result.data.sizeBytes),
          etag: result.data.etag,
          "x-yatabase-storage-tier": result.data.storageTier,
          "x-yatabase-storage-provider": result.data.storageProvider,
        },
      });
    }
    if (result.data.sizeBytes > INLINE_DOWNLOAD_LIMIT) {
      return dispatcherError(
        413,
        `inline download limited to ${INLINE_DOWNLOAD_LIMIT} bytes; use POST /storage/v1/object/sign for a presigned URL`,
      );
    }
    if (!result.data.data) return notFound("object body unavailable");
    const bin = atob(result.data.data);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return new Response(out, {
      status: 200,
      headers: {
        "content-type": result.data.contentType || "application/octet-stream",
        "content-length": String(result.data.sizeBytes),
        etag: result.data.etag,
        "x-yatabase-storage-tier": result.data.storageTier,
        "x-yatabase-storage-provider": result.data.storageProvider,
      },
    });
  }

  if (req.method === "DELETE") {
    const purge = new URL(req.url).searchParams.get("purge") === "true";
    const result = await dispatchYataXrpc(
      env,
      "com.etzhayyim.apps.yata.deleteObject",
      { bucketName: bucket, objectKey: key, purge },
      caller,
      { timeoutMs: 30_000 },
    );
    if (!result.ok) {
      // P73: R2 delete first, then KV.
      const { deleteR2Object } = await import("./storage-r2");
      const r2del = await deleteR2Object(env as never, caller.orgDid, bucket, key);
      if (r2del) {
        return new Response(JSON.stringify({ message: "Successfully deleted", source: "r2" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      const { deleteKvObject } = await import("./storage-kv");
      const deleted = await deleteKvObject(env as never, caller.orgDid, bucket, key);
      if (deleted) {
        return new Response(JSON.stringify({ message: "Successfully deleted", source: "kv-fallback" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      return dispatcherError(result.status, result.error ?? "delete failed");
    }
    return new Response(JSON.stringify({ message: "Successfully deleted" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }

  return badRequest(`unsupported method ${req.method}`);
}

async function handleList(
  req: Request,
  env: StorageEnv,
  caller: DispatcherCallerContext,
  bucket: string,
): Promise<Response> {
  const url = new URL(req.url);
  const prefix = url.searchParams.get("prefix") ?? "";
  const limit = Number.parseInt(url.searchParams.get("limit") ?? "100", 10);
  const cursor = url.searchParams.get("cursor") ?? undefined;
  const result = await dispatchYataXrpc(
    env,
    "com.etzhayyim.apps.yata.listObjects",
    { bucketName: bucket, prefix, limit, cursor },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok) {
    // P73: R2 list first. Merge with KV fallback so customers see
    // objects from both tiers in a single response (P64 KV objects +
    // P73 R2 objects).
    const { listR2Objects } = await import("./storage-r2");
    const { listKvObjects } = await import("./storage-kv");
    const [r2Objs, kvObjs] = await Promise.all([
      listR2Objects(env as never, caller.orgDid, bucket, prefix, limit),
      listKvObjects(env as never, caller.orgDid, bucket, prefix, limit),
    ]);
    const seen = new Set<string>();
    const merged: Array<{ name: string; size: number; etag: string; contentType: string; updatedAt: string }> = [];
    for (const o of [...r2Objs, ...kvObjs]) {
      if (seen.has(o.name)) continue;
      seen.add(o.name);
      merged.push(o);
    }
    const source = r2Objs.length > 0 ? (kvObjs.length > 0 ? "r2+kv-fallback" : "r2") : "kv-fallback";
    return new Response(JSON.stringify({ objects: merged, bucket, prefix, source }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }
  return new Response(JSON.stringify(result.data ?? {}), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function handleSign(
  req: Request,
  env: StorageEnv,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
): Promise<Response> {
  let body: { method?: string; expiresIn?: number; contentType?: string } = {};
  if ((req.headers.get("content-type") ?? "").includes("application/json")) {
    try { body = (await req.json()) as typeof body; } catch { /* ignore */ }
  }
  const expiresIn = Number(body.expiresIn ?? new URL(req.url).searchParams.get("expiresIn") ?? 3600);
  const method = body.method ?? "GET";
  const result = await dispatchYataXrpc(
    env,
    "com.etzhayyim.apps.yata.presignUrl",
    { bucketName: bucket, objectKey: key, method, expiresInSec: expiresIn, contentType: body.contentType },
    caller,
    { timeoutMs: 15_000 },
  );
  if (!result.ok) {
    // P69: KV signed-URL fallback. Mint a short-lived signed token that
    // /storage/v1/object/public/{bucket}/{key}?token=... validates.
    const { mintKvSignedUrl } = await import("./storage-kv");
    const signed = await mintKvSignedUrl(env as never, caller.orgDid, bucket, key, expiresIn);
    if (signed) {
      return new Response(JSON.stringify(signed), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    return dispatcherError(result.status, result.error ?? "sign failed");
  }
  const data = result.data as { url?: string; expiresAt?: string };
  return new Response(JSON.stringify({ signedURL: data.url ?? "", expiresAt: data.expiresAt }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function handleBucket(env: StorageEnv, caller: DispatcherCallerContext): Promise<Response> {
  const result = await dispatchYataXrpc(
    env,
    "com.etzhayyim.apps.yata.listBuckets",
    {},
    caller,
    { timeoutMs: 15_000 },
  );
  if (!result.ok) {
    // P73: R2 + KV bucket enumeration merged so customers see all
    // tiers in one response.
    const { listR2Buckets } = await import("./storage-r2");
    const { listKvBuckets } = await import("./storage-kv");
    const [r2Bk, kvBk] = await Promise.all([
      listR2Buckets(env as never, caller.orgDid),
      listKvBuckets(env as never, caller.orgDid),
    ]);
    const counts = new Map<string, number>();
    for (const b of [...r2Bk, ...kvBk]) counts.set(b.name, (counts.get(b.name) ?? 0) + b.objectCount);
    const buckets = Array.from(counts.entries()).map(([name, objectCount]) => ({ name, objectCount }));
    const source = r2Bk.length > 0 ? (kvBk.length > 0 ? "r2+kv-fallback" : "r2") : "kv-fallback";
    return new Response(JSON.stringify({ buckets, source }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }
  return new Response(JSON.stringify(result.data ?? { buckets: [] }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}
