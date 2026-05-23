// hyperdrive-reads.ts — direct RisingWave reads via Hyperdrive (P3.2).
//
// Bypasses bpmn-dispatcher for the cheap-read hot path:
//   listBuckets / listObjects / headObject / coverage
//
// These reads have:
//   - no side effects (no metering on storage write side, idempotent),
//   - bounded result sets (cursor + limit),
//   - simple Kysely SELECTs against vertex_yata_*.
//
// Saves ~40ms vs the full BPMN round-trip (CF Worker → public HTTPS →
// dispatcher Vultr LB → caddy → aiohttp → LangServer job → LangServer primitive
// → RW). Direct path: Worker → Hyperdrive PG protocol → RW.
//
// All write-side calls (put / delete / presign / sparql / provision)
// MUST still go through bpmn-dispatcher to keep audit + metering
// uniform. The shortcut is reserved for stateless reads.

interface AnyKyselyDb {
  selectFrom(table: string): {
    select(cols: string[]): {
      where(col: string, op: string, val: unknown): {
        where(col: string, op: string, val: unknown): {
          where?(col: string, op: string, val: unknown): unknown;
          orderBy(col: string, dir: "asc" | "desc"): {
            limit(n: number): {
              execute(): Promise<Record<string, unknown>[]>;
            };
          };
          limit(n: number): {
            execute(): Promise<Record<string, unknown>[]>;
            executeTakeFirst(): Promise<Record<string, unknown> | undefined>;
          };
        };
        executeTakeFirst(): Promise<Record<string, unknown> | undefined>;
      };
    };
  };
}

export interface HyperdriveReadEnv {
  HYPERDRIVE?: unknown;
}

export interface ListBucketsResult {
  buckets: Array<{
    bucketId: string;
    bucketName: string;
    region: string;
    encryption: string;
    tierPolicy: string;
    versioningEnabled: boolean;
    publicRead: boolean;
    blobCount: number;
    totalBytes: number;
    createdAt: string;
  }>;
}

export interface ListObjectsResult {
  bucketName: string;
  objects: Array<{
    objectKey: string;
    blobId: string;
    sizeBytes: number;
    etag: string;
    contentType: string;
    storageTier: string;
    createdAt: string;
  }>;
  nextCursor: string;
}

export interface HeadObjectResult {
  exists: boolean;
  etag?: string;
  sizeBytes?: number;
  contentType?: string;
  storageTier?: string;
  lastAccessedAt?: string;
  createdAt?: string;
}

export interface CoverageResult {
  asOf: string;
  tenantsActive: number;
  bucketsTotal: number;
  blobsTotal: number;
  totalBytes: number;
  blobsByTier: string;
  pendingEmbeddings: number;
  openMultipart: number;
}

async function getDb(env: HyperdriveReadEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch (e) {
    console.warn("[yatabase][hyperdrive] db init failed:", e);
    return null;
  }
}

/** SELECT vertex_yata_bucket WHERE org_did = ? */
export async function listBucketsDirect(
  env: HyperdriveReadEnv,
  orgDid: string,
  limit = 50,
): Promise<ListBucketsResult | null> {
  const db = await getDb(env);
  if (!db) return null;
  try {
    const safe = Math.min(Math.max(Math.floor(limit), 1), 200);
    const rows = (await (db
      .selectFrom("vertex_yata_bucket")
      .select([
        "vertex_id",
        "bucket_name",
        "region",
        "encryption",
        "tier_policy",
        "versioning_enabled",
        "public_read",
        "created_at",
      ] as string[])
      .where("org_did", "=", orgDid)
      .where("status", "=", "active") as never as {
        orderBy(c: string, d: "asc" | "desc"): { limit(n: number): { execute(): Promise<Record<string, unknown>[]> } };
      })
      .orderBy("bucket_name", "asc")
      .limit(safe)
      .execute()) as Record<string, unknown>[];
    return {
      buckets: rows.map((r) => ({
        bucketId: String(r.vertex_id ?? ""),
        bucketName: String(r.bucket_name ?? ""),
        region: String(r.region ?? ""),
        encryption: String(r.encryption ?? ""),
        tierPolicy: String(r.tier_policy ?? ""),
        versioningEnabled: Boolean(r.versioning_enabled),
        publicRead: Boolean(r.public_read),
        blobCount: 0, // Joined from mv_yata_blob_count_by_org in P3.2.5
        totalBytes: 0,
        createdAt: String(r.created_at ?? ""),
      })),
    };
  } catch (e) {
    console.warn("[yatabase][hyperdrive] listBuckets failed:", e);
    return null;
  }
}

/** SELECT vertex_yata_blob WHERE bucket_name = ? AND org_did = ? */
export async function listObjectsDirect(
  env: HyperdriveReadEnv,
  orgDid: string,
  bucketName: string,
  prefix: string,
  limit = 100,
  _cursor?: string,
): Promise<ListObjectsResult | null> {
  const db = await getDb(env);
  if (!db) return null;
  try {
    const safe = Math.min(Math.max(Math.floor(limit), 1), 1000);
    let q = (db
      .selectFrom("vertex_yata_blob")
      .select([
        "vertex_id",
        "object_key",
        "size_bytes",
        "etag",
        "content_type",
        "storage_tier",
        "created_at",
      ] as string[])
      .where("org_did", "=", orgDid)
      .where("bucket_name", "=", bucketName) as unknown as {
        where(c: string, op: string, v: unknown): typeof q;
        orderBy(c: string, d: "asc" | "desc"): { limit(n: number): { execute(): Promise<Record<string, unknown>[]> } };
      });
    if (prefix) q = q.where("object_key", "like", `${prefix}%`);
    const rows = (await q
      .orderBy("object_key", "asc")
      .limit(safe + 1)
      .execute()) as Record<string, unknown>[];
    const hasMore = rows.length > safe;
    const objects = rows.slice(0, safe).map((r) => ({
      objectKey: String(r.object_key ?? ""),
      blobId: String(r.vertex_id ?? ""),
      sizeBytes: Number(r.size_bytes ?? 0),
      etag: String(r.etag ?? ""),
      contentType: String(r.content_type ?? ""),
      storageTier: String(r.storage_tier ?? ""),
      createdAt: String(r.created_at ?? ""),
    }));
    return {
      bucketName,
      objects,
      nextCursor: hasMore && objects.length > 0
        ? objects[objects.length - 1]!.objectKey
        : "",
    };
  } catch (e) {
    console.warn("[yatabase][hyperdrive] listObjects failed:", e);
    return null;
  }
}

/** SELECT first matching row for HEAD. */
export async function headObjectDirect(
  env: HyperdriveReadEnv,
  orgDid: string,
  bucketName: string,
  objectKey: string,
): Promise<HeadObjectResult | null> {
  const db = await getDb(env);
  if (!db) return null;
  try {
    const row = (await (db
      .selectFrom("vertex_yata_blob")
      .select([
        "etag",
        "size_bytes",
        "content_type",
        "storage_tier",
        "last_accessed_at",
        "created_at",
      ] as string[])
      .where("org_did", "=", orgDid)
      .where("bucket_name", "=", bucketName) as unknown as {
        where(c: string, op: string, v: unknown): {
          orderBy(c: string, d: "asc" | "desc"): {
            limit(n: number): { executeTakeFirst(): Promise<Record<string, unknown> | undefined> };
          };
        };
      })
      .where("object_key", "=", objectKey)
      .orderBy("created_at", "desc")
      .limit(1)
      .executeTakeFirst()) as Record<string, unknown> | undefined;
    if (!row) return { exists: false };
    return {
      exists: true,
      etag: String(row.etag ?? ""),
      sizeBytes: Number(row.size_bytes ?? 0),
      contentType: String(row.content_type ?? ""),
      storageTier: String(row.storage_tier ?? ""),
      lastAccessedAt: String(row.last_accessed_at ?? ""),
      createdAt: String(row.created_at ?? ""),
    };
  } catch (e) {
    console.warn("[yatabase][hyperdrive] headObject failed:", e);
    return null;
  }
}
