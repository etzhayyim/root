// audit-log.ts — Per-tenant audit log (security / compliance).
//
// Every authenticated request emits a `vertex_audit_log` row via
// `executionCtx.waitUntil()` so the latency on the hot path is zero.
// Customer can fetch their own history at `GET /api/audit` and verify
// that no rogue key has been hitting their tenant.
//
// Schema:
//   vertex_id       PK, derived from sha256(orgDid + ts + path + nonce)
//   org_did         caller's org
//   actor_did       caller's specific actor (often == org for single-key tenants)
//   ts_ms           epoch millis
//   surface         coarse surface bucket (cypher / storage / mcp / etc.)
//   method          HTTP method
//   path            request path (query string stripped)
//   status_code     200 / 401 / 429 / etc.
//   latency_ms      time to first byte
//   ip_hash         sha256(client_ip)[:16] for rate-limit / abuse detection
//                   without storing PII
//   user_agent_hint short UA prefix (first 60 chars, classifies driver)
//   key_id          which sk_live_yata_* (keyId) issued the request
//
// Retention: 90 days (purge cron deferred to billing-pool).

export interface AuditEnv {
  HYPERDRIVE?: unknown;
  GFTD_AUDIT_DISABLED?: string;
  YATABASE_AUTH_CACHE?: KVNamespace; // P87: KV mirror when RW is degraded
}

const KV_AUDIT_TTL_SECONDS = 86400; // 24h matches the getAuditEvents window

interface AnyKyselyDb {
  insertInto(table: string): {
    values(row: Record<string, unknown>): { execute(): Promise<unknown> };
  };
}

async function getDb(env: AuditEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export interface AuditEvent {
  orgDid: string;
  actorDid?: string;
  surface: string;
  method: string;
  path: string;
  statusCode: number;
  latencyMs: number;
  ipHint?: string;
  userAgent?: string;
  keyIdHint?: string;
}

export async function emitAudit(env: AuditEnv, event: AuditEvent): Promise<void> {
  if (env.GFTD_AUDIT_DISABLED === "1") return;
  if (!event.orgDid) return;

  const tsMs = Date.now();
  const ipHash = event.ipHint ? (await sha256Hex(event.ipHint)).slice(0, 16) : "";
  const uaHint = (event.userAgent ?? "").slice(0, 60);
  const cleanPath = event.path.split("?")[0];

  // P87: KV-first write. Per-org keyspace sorted by descending tsMs so
  // a kv.list with the org prefix returns recent events first (KV list
  // is sorted lex ascending by key). Best-effort: KV failure logged
  // but doesn't surface to the request hot path (we're in waitUntil).
  if (env.YATABASE_AUTH_CACHE && event.orgDid) {
    try {
      const invertedTs = (10n ** 16n - BigInt(tsMs)).toString().padStart(16, "0");
      const rand = Math.random().toString(36).slice(2, 10);
      const key = `audit:v1:${event.orgDid}:${invertedTs}:${rand}`;
      const value = JSON.stringify({
        tsMs, surface: event.surface, method: event.method, path: cleanPath,
        statusCode: event.statusCode, latencyMs: event.latencyMs,
        ipHash, userAgentHint: uaHint, keyId: event.keyIdHint ?? "",
        actorDid: event.actorDid ?? event.orgDid,
      });
      await env.YATABASE_AUTH_CACHE.put(key, value, { expirationTtl: KV_AUDIT_TTL_SECONDS });
    } catch (e) {
      console.warn("[yatabase][audit] KV put failed:", e);
    }
  }

  // Legacy RW path — best-effort, currently degraded by ADR-2605111200.
  let realDb: unknown = null;
  let sqlTag: ((s: TemplateStringsArray, ...v: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    realDb = (sdk as unknown as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(env.HYPERDRIVE as never);
    sqlTag = (sdk as unknown as { sql?: (s: TemplateStringsArray, ...v: unknown[]) => unknown }).sql ?? null;
  } catch {
    return;
  }
  if (!realDb || !sqlTag) return;

  const nowIso = new Date(tsMs).toISOString().slice(0, 19).replace("T", " ");
  const idDigest = await sha256Hex(`${event.orgDid}|${tsMs}|${event.path}|${Math.random()}`);
  const vertexId = `at://did:web:audit.gftd.ai/ai.gftd.apps.audit.event/${idDigest.slice(0, 32)}`;

  try {
    const q = sqlTag`
      INSERT INTO vertex_audit_log
        (vertex_id, org_did, actor_did, ts_ms, surface, method, path,
         status_code, latency_ms, ip_hash, user_agent_hint, key_id,
         created_at)
      VALUES (${vertexId}, ${event.orgDid}, ${event.actorDid ?? event.orgDid},
              ${tsMs}, ${event.surface}, ${event.method}, ${cleanPath},
              ${event.statusCode}, ${event.latencyMs}, ${ipHash},
              ${uaHint}, ${event.keyIdHint ?? ""}, ${nowIso})
    `;
    const exec = (q as unknown as { execute: (db: unknown) => Promise<unknown> }).execute;
    await exec.call(q, realDb);
  } catch (e) {
    console.warn("[yatabase][audit] insert failed:", e);
  }
}

// P87: KV-backed audit query. Read per-org events from KV when RW is
// degraded. Used by getAuditEvents() and /api/export.
async function readAuditFromKv(
  env: AuditEnv,
  orgDid: string,
  limit: number,
): Promise<AuditQueryResult | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const cap = Math.min(Math.max(limit, 1), 500);
    const list = await kv.list({ prefix: `audit:v1:${orgDid}:`, limit: cap });
    const events: AuditQueryResult["events"] = [];
    for (const k of list.keys ?? []) {
      const raw = await kv.get(k.name);
      if (!raw) continue;
      try {
        const e = JSON.parse(raw) as Record<string, unknown>;
        events.push({
          tsMs: Number(e.tsMs ?? 0),
          surface: String(e.surface ?? ""),
          method: String(e.method ?? ""),
          path: String(e.path ?? ""),
          statusCode: Number(e.statusCode ?? 0),
          latencyMs: Number(e.latencyMs ?? 0),
          ipHash: String(e.ipHash ?? ""),
          userAgentHint: String(e.userAgentHint ?? ""),
          keyId: String(e.keyId ?? ""),
        });
      } catch { /* ignore */ }
    }
    const sinceMs = Date.now() - 24 * 60 * 60 * 1000;
    return {
      orgDid,
      windowStart: new Date(sinceMs).toISOString(),
      windowEnd: new Date().toISOString(),
      events,
      truncatedAt: cap,
    };
  } catch (e) {
    console.warn("[yatabase][audit] KV list failed:", e);
    return null;
  }
}

export interface AuditQueryResult {
  orgDid: string;
  windowStart: string;
  windowEnd: string;
  events: Array<{
    tsMs: number;
    surface: string;
    method: string;
    path: string;
    statusCode: number;
    latencyMs: number;
    ipHash: string;
    userAgentHint: string;
    keyId: string;
  }>;
  truncatedAt: number;
}

export async function getAuditEvents(
  env: AuditEnv,
  orgDid: string,
  limit = 100,
): Promise<AuditQueryResult | null> {
  // P87: KV-first read (authoritative when RW degraded). Falls back to
  // RW if KV returns empty AND we have a Hyperdrive binding.
  const kv = await readAuditFromKv(env, orgDid, limit);
  if (kv && kv.events.length > 0) return kv;

  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    return kv;  // KV result (possibly empty) is better than null
  }
  if (!sqlTag) return kv;
  const db = await getDb(env);
  if (!db) return kv;

  const cap = Math.min(Math.max(limit, 1), 500);
  const sinceMs = Date.now() - 24 * 60 * 60 * 1000;
  const q = sqlTag`
    SELECT ts_ms, surface, method, path, status_code, latency_ms,
           ip_hash, user_agent_hint, key_id
    FROM vertex_audit_log
    WHERE org_did = ${orgDid} AND ts_ms >= ${sinceMs}
    ORDER BY ts_ms DESC
    LIMIT ${cap}
  `;

  let rows: Array<Record<string, unknown>> = [];
  try {
    const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    rows = result.rows ?? [];
  } catch (e) {
    console.warn("[yatabase][audit] query failed:", e);
    return null;
  }

  return {
    orgDid,
    windowStart: new Date(sinceMs).toISOString(),
    windowEnd: new Date().toISOString(),
    events: rows.map((r) => ({
      tsMs: Number(r.ts_ms ?? 0),
      surface: String(r.surface ?? ""),
      method: String(r.method ?? ""),
      path: String(r.path ?? ""),
      statusCode: Number(r.status_code ?? 0),
      latencyMs: Number(r.latency_ms ?? 0),
      ipHash: String(r.ip_hash ?? ""),
      userAgentHint: String(r.user_agent_hint ?? ""),
      keyId: String(r.key_id ?? ""),
    })),
    truncatedAt: cap,
  };
}
