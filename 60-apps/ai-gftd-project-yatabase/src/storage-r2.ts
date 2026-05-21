// storage-r2.ts — Cloudflare R2 fallback for /storage/v1/object/* (P73).
//
// When the lg-yatabase pod's putObject/getObject NSID handlers haven't
// shipped, the Worker can persist objects directly to the R2 bucket
// bound as YATA_R2. R2 has no relevant size cap (vs. KV's 1 MiB), so
// promoting it ahead of the KV fallback unblocks customers uploading
// real files (photos, PDFs, datasets).
//
// Per-org keyspace: `yata/{orgDid}/{bucket}/{key}`. This namespacing
// ensures one org cannot list/read another org's blobs even though
// they share an R2 bucket.

export type R2StorageEnv = {
  YATA_R2?: R2Bucket;
};

export type R2StoredObject = {
  blobId: string;
  etag: string;
  sizeBytes: number;
  contentType: string;
  storedAt: string;
};

const PREFIX = "yata";

function r2Key(orgDid: string, bucket: string, key: string): string {
  return `${PREFIX}/${orgDid}/${bucket}/${key}`;
}

export async function putR2Object(
  env: R2StorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
  body: ArrayBuffer | Uint8Array | ReadableStream | string,
  contentType: string,
): Promise<R2StoredObject | null> {
  const r2 = env.YATA_R2;
  if (!r2) return null;
  try {
    const putKey = r2Key(orgDid, bucket, key);
    const customMeta = { orgDid, bucket, key, contentType };
    const result = await r2.put(putKey, body, {
      httpMetadata: { contentType: contentType || "application/octet-stream" },
      customMetadata: customMeta,
    });
    if (!result) return null;
    return {
      blobId: `blob:r2:${result.etag}`,
      etag: `"${result.etag}"`,
      sizeBytes: result.size,
      contentType: contentType || "application/octet-stream",
      storedAt: result.uploaded.toISOString(),
    };
  } catch (e) {
    console.warn("[yatabase][storage-r2] put failed:", e);
    return null;
  }
}

export async function getR2Object(
  env: R2StorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
): Promise<(R2StoredObject & { body: ReadableStream }) | null> {
  const r2 = env.YATA_R2;
  if (!r2) return null;
  try {
    const obj = await r2.get(r2Key(orgDid, bucket, key));
    if (!obj) return null;
    return {
      blobId: `blob:r2:${obj.etag}`,
      etag: `"${obj.etag}"`,
      sizeBytes: obj.size,
      contentType: obj.httpMetadata?.contentType ?? "application/octet-stream",
      storedAt: obj.uploaded.toISOString(),
      body: obj.body,
    };
  } catch (e) {
    console.warn("[yatabase][storage-r2] get failed:", e);
    return null;
  }
}

export async function headR2Object(
  env: R2StorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
): Promise<R2StoredObject | null> {
  const r2 = env.YATA_R2;
  if (!r2) return null;
  try {
    const obj = await r2.head(r2Key(orgDid, bucket, key));
    if (!obj) return null;
    return {
      blobId: `blob:r2:${obj.etag}`,
      etag: `"${obj.etag}"`,
      sizeBytes: obj.size,
      contentType: obj.httpMetadata?.contentType ?? "application/octet-stream",
      storedAt: obj.uploaded.toISOString(),
    };
  } catch (e) {
    console.warn("[yatabase][storage-r2] head failed:", e);
    return null;
  }
}

export async function deleteR2Object(
  env: R2StorageEnv,
  orgDid: string,
  bucket: string,
  key: string,
): Promise<boolean> {
  const r2 = env.YATA_R2;
  if (!r2) return false;
  try {
    const existing = await r2.head(r2Key(orgDid, bucket, key));
    if (!existing) return false;
    await r2.delete(r2Key(orgDid, bucket, key));
    return true;
  } catch (e) {
    console.warn("[yatabase][storage-r2] delete failed:", e);
    return false;
  }
}

export async function listR2Objects(
  env: R2StorageEnv,
  orgDid: string,
  bucket: string,
  prefix: string,
  limit: number,
): Promise<Array<{ name: string; size: number; etag: string; contentType: string; updatedAt: string }>> {
  const r2 = env.YATA_R2;
  if (!r2) return [];
  try {
    const listPrefix = `${PREFIX}/${orgDid}/${bucket}/${prefix}`;
    const result = await r2.list({
      prefix: listPrefix,
      limit: Math.max(1, Math.min(1000, limit)),
    });
    const stripPrefix = `${PREFIX}/${orgDid}/${bucket}/`;
    return result.objects.map((o) => ({
      name: o.key.slice(stripPrefix.length),
      size: o.size,
      etag: `"${o.etag}"`,
      contentType: o.httpMetadata?.contentType ?? "application/octet-stream",
      updatedAt: o.uploaded.toISOString(),
    }));
  } catch (e) {
    console.warn("[yatabase][storage-r2] list failed:", e);
    return [];
  }
}

export async function listR2Buckets(
  env: R2StorageEnv,
  orgDid: string,
): Promise<Array<{ name: string; objectCount: number }>> {
  const r2 = env.YATA_R2;
  if (!r2) return [];
  try {
    const orgPrefix = `${PREFIX}/${orgDid}/`;
    const counts = new Map<string, number>();
    let cursor: string | undefined;
    // Pagination: scan up to 5 pages to keep latency bounded; this gives
    // up to 5000 objects per /storage/v1/bucket call. Past that, the user
    // is well-served by the pod-side handler when it ships.
    for (let i = 0; i < 5; i++) {
      const result: R2Objects = await r2.list({ prefix: orgPrefix, limit: 1000, cursor });
      for (const o of result.objects ?? []) {
        const tail = o.key.slice(orgPrefix.length);
        const bucketName = tail.split("/")[0];
        if (bucketName) counts.set(bucketName, (counts.get(bucketName) ?? 0) + 1);
      }
      if (!result.truncated) break;
      cursor = result.cursor;
    }
    return Array.from(counts.entries()).map(([name, objectCount]) => ({ name, objectCount }));
  } catch (e) {
    console.warn("[yatabase][storage-r2] listBuckets failed:", e);
    return [];
  }
}
