// s3-rest.ts — AWS S3-compatible /s3/{bucket}/{key} routes (P3.2).
//
// Translates inbound boto3 / aws-sdk-js / mc requests into internal
// `ai.gftd.apps.yata.{put,get,delete,head}` XRPC dispatches via
// bpmn-dispatcher.
//
// Auth: AWS SigV4 only (Bearer is handled by the /storage/v1/* path).
// The verifier (`s3-sigv4.ts`) resolves the access key id back to the
// owner_did + product_scope so the same caller context structure used
// elsewhere in the Worker is reused.
//
// Response shape: AWS S3 (ETag header, x-amz-meta-* metadata pass-through,
// XML-formatted listing, etc.).
//
// MVP coverage (P3.2):
//   GET    /s3/{bucket}/{key}                       download
//   PUT    /s3/{bucket}/{key}                       upload (≤5 MiB inline)
//   HEAD   /s3/{bucket}/{key}                       metadata
//   DELETE /s3/{bucket}/{key}                       delete
//
// Deferred to P3.2.5:
//   GET /s3/{bucket}/?list-type=2                   ListObjectsV2 (XML)
//   POST /s3/{bucket}/{key}?uploads                 InitiateMultipartUpload
//   PUT  /s3/{bucket}/{key}?partNumber=N&uploadId=X UploadPart
//   POST /s3/{bucket}/{key}?uploadId=X              CompleteMultipartUpload
//   DELETE /s3/{bucket}/{key}?uploadId=X            AbortMultipartUpload
//   /s3/{bucket}/{key} byte-range proxy >5 MiB

import {
  dispatchYataXrpc,
  type DispatcherCallerContext,
  type DispatcherEnv,
} from "./dispatcher";
import { verifySigV4, type SigV4VerifyEnv } from "./s3-sigv4";

interface S3Env extends DispatcherEnv, SigV4VerifyEnv {}

const INLINE_UPLOAD_LIMIT = 5 * 1024 * 1024;
const INLINE_DOWNLOAD_LIMIT = 5 * 1024 * 1024;

interface PutOk {
  ok: true;
  blobId: string;
  versionId?: string;
  etag: string;
  cid?: string;
  sizeBytes: number;
  storageTier: string;
  storageProvider: string;
}

interface GetOk {
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

function s3Error(code: string, message: string, status: number): Response {
  // Minimal S3-style XML error body. boto3 / aws-sdk-js parse this.
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>${code}</Code><Message>${escapeXml(message)}</Message></Error>`;
  return new Response(body, {
    status,
    headers: { "content-type": "application/xml" },
  });
}

function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/**
 * Parse `/s3/{bucket}/{key}` into `{ bucket, key }`. The key MAY contain
 * additional `/` characters. Returns null if the path is not /s3/-shaped.
 */
export function parseS3Path(pathname: string): { bucket: string; key: string } | null {
  if (!pathname.startsWith("/s3/")) return null;
  const rest = pathname.slice("/s3/".length);
  const slash = rest.indexOf("/");
  if (slash < 0) {
    // Bucket-only path (used for ListObjectsV2 in P3.2.5).
    return { bucket: rest, key: "" };
  }
  return { bucket: rest.slice(0, slash), key: rest.slice(slash + 1) };
}

/**
 * Top-level dispatch for /s3/*. Verifies SigV4, resolves caller, and
 * dispatches to the XRPC primitive. Returns null if path does not match.
 */
export async function handleS3Rest(
  req: Request,
  env: S3Env,
): Promise<Response | null> {
  const url = new URL(req.url);
  const parsed = parseS3Path(url.pathname);
  if (!parsed) return null;

  // Read body once (needed for SigV4 hash + dispatch).
  let bodyBytes = new Uint8Array();
  if (req.method === "PUT" || req.method === "POST") {
    bodyBytes = new Uint8Array(await req.arrayBuffer());
    if (bodyBytes.length > INLINE_UPLOAD_LIMIT) {
      return s3Error(
        "EntityTooLarge",
        `inline single-part PUT limited to ${INLINE_UPLOAD_LIMIT} bytes; ` +
          "use multipart upload (POST ?uploads → PUT ?partNumber=N&uploadId=X → POST ?uploadId=X) " +
          "or presigned URL (POST /storage/v1/object/sign)",
        413,
      );
    }
  }

  // Verify SigV4. Worker re-creates the request object with the same
  // body bytes so the verifier can recompute the canonical request.
  const verifiableReq = new Request(req.url, {
    method: req.method,
    headers: req.headers,
    // Body is irrelevant to the verifier (it uses x-amz-content-sha256).
    body: bodyBytes.length > 0 ? bodyBytes : undefined,
  });
  const auth = await verifySigV4({ req: verifiableReq, bodyBytes, env });
  if (!auth) {
    return s3Error("SignatureDoesNotMatch", "AWS SigV4 verification failed", 403);
  }

  // Product-scope gate (mirror of enforceApiKeyProductScope from PDS).
  if (auth.productScope === "obj") {
    return s3Error(
      "AccessDenied",
      "obj-scoped api keys are not currently issued; use yata or unscoped",
      403,
    );
  }

  const caller: DispatcherCallerContext = {
    orgDid: auth.ownerDid, // owner_did is used as org_did upstream when no separate org assignment exists
    actorDid: auth.ownerDid,
    productScope: auth.productScope ?? "yata",
    traceId: req.headers.get("cf-ray") ?? undefined,
  };

  // Bucket-only paths: ListObjectsV2 (P3.2.5).
  if (!parsed.key) {
    if (req.method === "GET" && url.searchParams.get("list-type") === "2") {
      return handleS3ListV2(env, caller, parsed.bucket, url.searchParams);
    }
    return s3Error("NotImplemented", `bucket-level ${req.method} not supported`, 501);
  }

  // Multipart endpoints (P3.2.5).
  if (req.method === "POST" && url.searchParams.has("uploads")) {
    return handleMultipartInit(env, caller, parsed.bucket, parsed.key, req.headers);
  }
  if (req.method === "PUT" && url.searchParams.has("partNumber") && url.searchParams.has("uploadId")) {
    return handleMultipartPart(
      env, caller,
      url.searchParams.get("uploadId")!,
      Number.parseInt(url.searchParams.get("partNumber") ?? "0", 10),
      bodyBytes,
    );
  }
  if (req.method === "POST" && url.searchParams.has("uploadId")) {
    return handleMultipartComplete(env, caller, url.searchParams.get("uploadId")!, bodyBytes);
  }
  if (req.method === "DELETE" && url.searchParams.has("uploadId")) {
    return handleMultipartAbort(env, caller, url.searchParams.get("uploadId")!);
  }

  if (req.method === "GET" || req.method === "HEAD") {
    return handleS3Get(req, env, caller, parsed.bucket, parsed.key);
  }
  if (req.method === "PUT") {
    return handleS3Put(env, caller, parsed.bucket, parsed.key, bodyBytes, req.headers);
  }
  if (req.method === "DELETE") {
    return handleS3Delete(env, caller, parsed.bucket, parsed.key);
  }
  return s3Error("MethodNotAllowed", `unsupported method ${req.method}`, 405);
}

// ──────────────────────────────────────────────────────────────────────
// ListObjectsV2 (XML)
// ──────────────────────────────────────────────────────────────────────

async function handleS3ListV2(
  env: S3Env,
  caller: DispatcherCallerContext,
  bucket: string,
  qs: URLSearchParams,
): Promise<Response> {
  const prefix     = qs.get("prefix") ?? "";
  const delimiter  = qs.get("delimiter") ?? "";
  const maxKeys    = Math.min(Math.max(Number.parseInt(qs.get("max-keys") ?? "1000", 10), 1), 1000);
  const startAfter = qs.get("start-after") ?? qs.get("continuation-token") ?? undefined;

  const result = await dispatchYataXrpc<{
    bucketName?: string;
    objects?: Array<{ objectKey: string; sizeBytes: number; etag: string; createdAt: string; storageTier?: string }>;
    commonPrefixes?: string[];
    nextCursor?: string;
    error?: string;
  }>(
    env,
    "ai.gftd.apps.yata.listObjects",
    { bucketName: bucket, prefix, delimiter, limit: maxKeys, cursor: startAfter },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok || !result.data) {
    return s3Error("InternalError", result.error ?? "list failed", 500);
  }
  if (result.data.error) {
    return s3Error("NoSuchBucket", result.data.error, 404);
  }

  const objects = result.data.objects ?? [];
  const cps = result.data.commonPrefixes ?? [];
  const nextToken = result.data.nextCursor ?? "";
  const isTruncated = Boolean(nextToken);

  // S3 ListBucketResult XML
  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
  xml += `<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n`;
  xml += `  <Name>${escapeXml(bucket)}</Name>\n`;
  xml += `  <Prefix>${escapeXml(prefix)}</Prefix>\n`;
  xml += `  <KeyCount>${objects.length}</KeyCount>\n`;
  xml += `  <MaxKeys>${maxKeys}</MaxKeys>\n`;
  xml += `  <IsTruncated>${isTruncated}</IsTruncated>\n`;
  if (delimiter) xml += `  <Delimiter>${escapeXml(delimiter)}</Delimiter>\n`;
  if (isTruncated) xml += `  <NextContinuationToken>${escapeXml(nextToken)}</NextContinuationToken>\n`;
  for (const o of objects) {
    xml += `  <Contents>\n`;
    xml += `    <Key>${escapeXml(o.objectKey)}</Key>\n`;
    xml += `    <LastModified>${escapeXml(o.createdAt)}</LastModified>\n`;
    xml += `    <ETag>"${escapeXml(o.etag)}"</ETag>\n`;
    xml += `    <Size>${o.sizeBytes}</Size>\n`;
    xml += `    <StorageClass>${s3StorageClassFromTier(o.storageTier ?? "warm")}</StorageClass>\n`;
    xml += `  </Contents>\n`;
  }
  for (const cp of cps) {
    xml += `  <CommonPrefixes><Prefix>${escapeXml(cp)}</Prefix></CommonPrefixes>\n`;
  }
  xml += `</ListBucketResult>\n`;

  return new Response(xml, { status: 200, headers: { "content-type": "application/xml" } });
}

// ──────────────────────────────────────────────────────────────────────
// Multipart endpoints (P3.2.5)
// ──────────────────────────────────────────────────────────────────────

async function handleMultipartInit(
  env: S3Env,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
  headers: Headers,
): Promise<Response> {
  const result = await dispatchYataXrpc<{ ok?: boolean; uploadId?: string; expiresAt?: string; error?: string }>(
    env,
    "ai.gftd.apps.yata.multipartInit",
    { bucketName: bucket, objectKey: key, contentType: headers.get("content-type") ?? "application/octet-stream" },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok || !result.data?.uploadId) {
    return s3Error("InternalError", result.error ?? result.data?.error ?? "init failed", 500);
  }
  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<InitiateMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n` +
    `  <Bucket>${escapeXml(bucket)}</Bucket>\n` +
    `  <Key>${escapeXml(key)}</Key>\n` +
    `  <UploadId>${escapeXml(result.data.uploadId)}</UploadId>\n` +
    `</InitiateMultipartUploadResult>\n`;
  return new Response(xml, { status: 200, headers: { "content-type": "application/xml" } });
}

async function handleMultipartPart(
  env: S3Env,
  caller: DispatcherCallerContext,
  uploadId: string,
  partNumber: number,
  body: Uint8Array,
): Promise<Response> {
  if (!uploadId || partNumber < 1) {
    return s3Error("InvalidArgument", "uploadId + partNumber required", 400);
  }
  if (body.length === 0) {
    return s3Error("MissingContent", "empty part body", 400);
  }
  let bin = "";
  for (let i = 0; i < body.length; i++) bin += String.fromCharCode(body[i] ?? 0);
  const data = btoa(bin);
  const result = await dispatchYataXrpc<{ partNumber?: number; etag?: string; sizeBytes?: number; error?: string }>(
    env,
    "ai.gftd.apps.yata.multipartPart",
    { uploadId, partNumber, data },
    caller,
    { timeoutMs: 60_000 },
  );
  if (!result.ok || !result.data?.etag) {
    return s3Error("InternalError", result.error ?? result.data?.error ?? "part failed", 500);
  }
  return new Response(null, {
    status: 200,
    headers: { etag: `"${result.data.etag}"` },
  });
}

async function handleMultipartComplete(
  env: S3Env,
  caller: DispatcherCallerContext,
  uploadId: string,
  body: Uint8Array,
): Promise<Response> {
  // Expected XML body:
  //  <CompleteMultipartUpload>
  //    <Part><PartNumber>1</PartNumber><ETag>"..."</ETag></Part>
  //    ...
  //  </CompleteMultipartUpload>
  const xmlBody = new TextDecoder().decode(body);
  const parts: Array<{ partNumber: number; etag: string }> = [];
  const partRe = /<Part>\s*<PartNumber>\s*(\d+)\s*<\/PartNumber>\s*<ETag>\s*"?([^"<]+)"?\s*<\/ETag>\s*<\/Part>/g;
  let m: RegExpExecArray | null;
  while ((m = partRe.exec(xmlBody)) !== null) {
    parts.push({ partNumber: Number.parseInt(m[1] ?? "0", 10), etag: m[2] ?? "" });
  }

  const result = await dispatchYataXrpc<{
    ok?: boolean; bucketName?: string; objectKey?: string; etag?: string; sizeBytes?: number; error?: string;
  }>(
    env,
    "ai.gftd.apps.yata.multipartComplete",
    { uploadId, parts },
    caller,
    { timeoutMs: 120_000 },
  );
  if (!result.ok || !result.data?.ok) {
    return s3Error("InternalError", result.error ?? result.data?.error ?? "complete failed", 500);
  }
  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<CompleteMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n` +
    `  <Location>https://yatabase.etzhayyim.com/s3/${escapeXml(result.data.bucketName ?? "")}/${escapeXml(result.data.objectKey ?? "")}</Location>\n` +
    `  <Bucket>${escapeXml(result.data.bucketName ?? "")}</Bucket>\n` +
    `  <Key>${escapeXml(result.data.objectKey ?? "")}</Key>\n` +
    `  <ETag>"${escapeXml(result.data.etag ?? "")}"</ETag>\n` +
    `</CompleteMultipartUploadResult>\n`;
  return new Response(xml, { status: 200, headers: { "content-type": "application/xml" } });
}

async function handleMultipartAbort(
  env: S3Env,
  caller: DispatcherCallerContext,
  uploadId: string,
): Promise<Response> {
  const result = await dispatchYataXrpc(
    env,
    "ai.gftd.apps.yata.multipartAbort",
    { uploadId },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok) {
    return s3Error("InternalError", result.error ?? "abort failed", 500);
  }
  return new Response(null, { status: 204 });
}

async function handleS3Get(
  req: Request,
  env: S3Env,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
): Promise<Response> {
  const ifNoneMatch = req.headers.get("if-none-match") ?? undefined;
  const result = await dispatchYataXrpc<GetOk & { error?: string }>(
    env,
    "ai.gftd.apps.yata.getObject",
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
    // P86: R2 fallback for GET/HEAD.
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
            "x-amz-storage-class": "STANDARD",
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
            "x-amz-storage-class": "STANDARD",
          },
        });
      }
    }
    return s3Error("NoSuchKey", result.error ?? "object not found", 404);
  }
  if ((result.data as { error?: string }).error)
    return s3Error("NoSuchKey", (result.data as { error: string }).error, 404);
  if (req.method === "HEAD") {
    return new Response(null, {
      status: 200,
      headers: {
        "content-type": result.data.contentType || "application/octet-stream",
        "content-length": String(result.data.sizeBytes),
        etag: `"${result.data.etag}"`,
        "x-yatabase-storage-tier": result.data.storageTier,
        "x-amz-storage-class": s3StorageClassFromTier(result.data.storageTier),
      },
    });
  }
  if (result.data.sizeBytes > INLINE_DOWNLOAD_LIMIT) {
    // P3.2.5 byte-range "proxy": rather than streaming bytes through
    // Worker memory, mint a 1-hour presigned URL and 302-redirect.
    // boto3 / aws-sdk-js follow redirects transparently. Range:
    // headers are forwarded to the upstream provider URL by the
    // client.
    const presign = await dispatchYataXrpc<{ url?: string; expiresAt?: string; error?: string }>(
      env,
      "ai.gftd.apps.yata.presignUrl",
      { bucketName: bucket, objectKey: key, method: "GET", expiresInSec: 3600 },
      caller,
      { timeoutMs: 15_000 },
    );
    if (!presign.ok || !presign.data?.url) {
      return s3Error("InternalError", presign.error ?? "presign for large object failed", 500);
    }
    return new Response(null, {
      status: 302,
      headers: {
        location: presign.data.url,
        "content-type": result.data.contentType || "application/octet-stream",
        etag: `"${result.data.etag}"`,
        "x-yatabase-storage-tier": result.data.storageTier,
        "x-amz-storage-class": s3StorageClassFromTier(result.data.storageTier),
        "x-yatabase-redirect-reason": "size>5MiB-presigned",
      },
    });
  }
  if (!result.data.data) return s3Error("NoSuchKey", "object body unavailable", 404);
  const bin = atob(result.data.data);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return new Response(out, {
    status: 200,
    headers: {
      "content-type": result.data.contentType || "application/octet-stream",
      "content-length": String(result.data.sizeBytes),
      etag: `"${result.data.etag}"`,
      "x-yatabase-storage-tier": result.data.storageTier,
      "x-amz-storage-class": s3StorageClassFromTier(result.data.storageTier),
    },
  });
}

async function handleS3Put(
  env: S3Env,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
  body: Uint8Array,
  headers: Headers,
): Promise<Response> {
  if (body.length === 0) {
    return s3Error("MissingContent", "PUT body required", 400);
  }
  const contentType = headers.get("content-type") ?? "application/octet-stream";

  // P86: R2 fallback FIRST (no size cap, durable). When the pod returns
  // a non-200 / 404, store directly in R2 keyed by orgDid for tenant
  // isolation. The /storage/v1/* path uses the same R2 store.
  let bin = "";
  for (let i = 0; i < body.length; i++) bin += String.fromCharCode(body[i] ?? 0);
  const data = btoa(bin);
  const result = await dispatchYataXrpc<PutOk & { error?: string }>(
    env,
    "ai.gftd.apps.yata.putObject",
    { bucketName: bucket, objectKey: key, data, contentType },
    caller,
    { timeoutMs: 120_000 },
  );
  if (!result.ok || !result.data) {
    const { putR2Object } = await import("./storage-r2");
    const r2stored = await putR2Object(env as never, caller.orgDid, bucket, key, body, contentType);
    if (r2stored) {
      return new Response(null, {
        status: 200,
        headers: {
          etag: r2stored.etag,
          "x-yatabase-storage-tier": "r2",
          "x-amz-storage-class": "STANDARD",
        },
      });
    }
    return s3Error("InternalError", result.error ?? "put failed", 500);
  }
  if ((result.data as { error?: string }).error)
    return s3Error("InvalidRequest", (result.data as { error: string }).error, 400);
  return new Response(null, {
    status: 200,
    headers: {
      etag: `"${result.data.etag}"`,
      "x-amz-version-id": result.data.versionId ?? "",
      "x-yatabase-storage-tier": result.data.storageTier,
    },
  });
}

async function handleS3Delete(
  env: S3Env,
  caller: DispatcherCallerContext,
  bucket: string,
  key: string,
): Promise<Response> {
  const result = await dispatchYataXrpc(
    env,
    "ai.gftd.apps.yata.deleteObject",
    { bucketName: bucket, objectKey: key, purge: false },
    caller,
    { timeoutMs: 30_000 },
  );
  if (!result.ok) return s3Error("InternalError", result.error ?? "delete failed", 500);
  return new Response(null, { status: 204 });
}

function s3StorageClassFromTier(tier: string): string {
  switch (tier) {
    case "hot":  return "STANDARD";
    case "warm": return "STANDARD_IA";
    case "cold": return "GLACIER";
    default:     return "STANDARD";
  }
}
