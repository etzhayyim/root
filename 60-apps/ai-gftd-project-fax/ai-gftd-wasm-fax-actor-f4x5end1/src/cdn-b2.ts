// B2 CDN backend — ADR-0043 Phase 5: R2 retired, B2 sole source of truth.
// All blob reads / writes / heads / lists route through aws4fetch SigV4 to
// s3.{region}.backblazeb2.com/{bucket}. Bandwidth Alliance: B2 → CF egress free.

import { AwsClient } from "aws4fetch";

export interface B2Env {
  B2_ENDPOINT: string;
  B2_BUCKET: string;
  B2_REGION: string;
  B2_KEY_ID: string;
  B2_APP_KEY: string;
}

function requireB2(env: Partial<B2Env>): asserts env is B2Env {
  const missing = (["B2_ENDPOINT", "B2_BUCKET", "B2_REGION", "B2_KEY_ID", "B2_APP_KEY"] as const).filter(
    (k) => !env[k],
  );
  if (missing.length > 0) {
    throw new Error(`[cdn-b2] missing env: ${missing.join(",")}`);
  }
}

function encodeKey(key: string): string {
  return key.split("/").map(encodeURIComponent).join("/");
}

function awsClient(env: B2Env): AwsClient {
  return new AwsClient({
    accessKeyId: env.B2_KEY_ID,
    secretAccessKey: env.B2_APP_KEY,
    service: "s3",
    region: env.B2_REGION,
  });
}

function objectUrl(env: B2Env, key: string): string {
  return `https://${env.B2_ENDPOINT}/${env.B2_BUCKET}/${encodeKey(key)}`;
}

export async function cdnWrite(
  env: Partial<B2Env>,
  key: string,
  data: ArrayBuffer,
  contentType: string,
): Promise<void> {
  requireB2(env);
  const res = await awsClient(env).fetch(objectUrl(env, key), {
    method: "PUT",
    body: data,
    headers: { "content-type": contentType },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`b2 PUT ${res.status}: ${body.slice(0, 120)}`);
  }
}

export async function cdnRead(
  env: Partial<B2Env>,
  key: string,
): Promise<{ body: ArrayBuffer; contentType: string } | null> {
  requireB2(env);
  const res = await awsClient(env).fetch(objectUrl(env, key), { method: "GET" });
  if (res.status === 404 || res.status === 403) return null;
  if (!res.ok) throw new Error(`b2 GET ${res.status}`);
  return {
    body: await res.arrayBuffer(),
    contentType: res.headers.get("content-type") || "application/octet-stream",
  };
}

// B2 S3 API returns 403 for missing objects (AWS mimicry) when caller lacks
// list-bucket permission on the prefix. Treat both 403 and 404 as "not exists".
export async function cdnHead(
  env: Partial<B2Env>,
  key: string,
): Promise<{ contentType: string; size: number } | null> {
  requireB2(env);
  const res = await awsClient(env).fetch(objectUrl(env, key), { method: "HEAD" });
  if (res.status === 404 || res.status === 403) return null;
  if (!res.ok) throw new Error(`b2 HEAD ${res.status}`);
  const size = Number(res.headers.get("content-length") || "0");
  return {
    contentType: res.headers.get("content-type") || "application/octet-stream",
    size,
  };
}

export interface CdnListResult {
  objects: Array<{ key: string; size: number }>;
  truncated: boolean;
  cursor: string;
}

export async function cdnList(
  env: Partial<B2Env>,
  prefix: string,
  limit: number,
  cursor?: string,
): Promise<CdnListResult> {
  requireB2(env);
  const url = new URL(`https://${env.B2_ENDPOINT}/${env.B2_BUCKET}`);
  url.searchParams.set("list-type", "2");
  url.searchParams.set("prefix", prefix);
  url.searchParams.set("max-keys", String(Math.max(1, Math.min(1000, limit))));
  if (cursor) url.searchParams.set("continuation-token", cursor);

  const res = await awsClient(env).fetch(url.toString(), { method: "GET" });
  if (!res.ok) throw new Error(`b2 LIST ${res.status}`);
  const xml = await res.text();

  const keys: Array<{ key: string; size: number }> = [];
  const keyRe = /<Key>([^<]+)<\/Key>[\s\S]*?<Size>([^<]+)<\/Size>/g;
  let m: RegExpExecArray | null;
  while ((m = keyRe.exec(xml)) !== null) {
    keys.push({ key: m[1]!, size: Number(m[2]) });
  }
  const truncated = /<IsTruncated>true<\/IsTruncated>/.test(xml);
  const nextCursor = /<NextContinuationToken>([^<]+)<\/NextContinuationToken>/.exec(xml)?.[1] ?? "";
  return { objects: keys, truncated, cursor: nextCursor };
}
